#!/usr/bin/env python3
"""
BirdNET Vocalization Service

Monitors BirdNET-Pi's birds.db for new detections and classifies vocalization types.
Stores results in separate vocalization.db (never modifies BirdNET-Pi files).

Usage:
    python service.py [--birdnet-dir /path/to/BirdNET-Pi] [--interval 30]
"""

import argparse
import logging
import os
import signal
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

from classifier import VocalizationClassifier

# Configuration
DEFAULT_BIRDNET_DIR = Path("/home/pi/BirdNET-Pi")
DEFAULT_DATA_DIR = Path("/opt/birdnet-vocalization/data")
DEFAULT_INTERVAL = 30  # seconds between checks
MIN_CONFIDENCE = 0.5   # minimum confidence to store result


def setup_logging(data_dir: Path):
    """Setup logging to data directory (writable by service user)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    log_file = data_dir / "service.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    return logging.getLogger(__name__)


# Will be initialized in main()
logger = logging.getLogger(__name__)


class VocalizationService:
    """Service that monitors BirdNET-Pi and classifies vocalizations."""

    def __init__(self, birdnet_dir: Path, models_dir: Path, data_dir: Path, language: str = 'en'):
        self.birdnet_dir = birdnet_dir
        self.birdnet_db = birdnet_dir / "scripts" / "birds.db"
        # BirdNET-Pi stores extracted audio in BirdSongs/Extracted/By_Date/
        self.extracted_dir = birdnet_dir / "BirdSongs" / "Extracted" / "By_Date"

        self.data_dir = data_dir
        self.vocalization_db = data_dir / "vocalization.db"
        self.language = language

        self.classifier = VocalizationClassifier(models_dir, language=language)
        self.running = False
        self.last_processed_id = 0

        self._init_database()
        self._load_last_processed()

    def _init_database(self):
        """Initialize vocalization database."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.vocalization_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vocalizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                birdnet_id INTEGER UNIQUE,
                file_name TEXT,
                common_name TEXT,
                scientific_name TEXT,
                vocalization_type TEXT,
                vocalization_type_display TEXT,
                confidence REAL,
                probabilities TEXT,
                classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_birdnet_id ON vocalizations(birdnet_id)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.vocalization_db}")

    def _load_last_processed(self):
        """Load last processed detection ID."""
        conn = sqlite3.connect(self.vocalization_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM service_state WHERE key = 'last_processed_id'"
        )
        row = cursor.fetchone()
        if row:
            self.last_processed_id = int(row[0])
        conn.close()
        logger.info(f"Resuming from detection ID: {self.last_processed_id}")

    def _save_last_processed(self):
        """Save last processed detection ID."""
        conn = sqlite3.connect(self.vocalization_db)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO service_state (key, value)
            VALUES ('last_processed_id', ?)
        """, (str(self.last_processed_id),))
        conn.commit()
        conn.close()

    def _get_new_detections(self) -> list[dict]:
        """Get new detections from BirdNET-Pi database.

        Uses Sci_Name (scientific name) for model matching since it's universal
        across all BirdNET-Pi language settings.
        """
        if not self.birdnet_db.exists():
            logger.warning(f"BirdNET-Pi database not found: {self.birdnet_db}")
            return []

        conn = sqlite3.connect(self.birdnet_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Sci_Name is the scientific name (e.g., "Turdus merula")
        # Com_Name is the display name in user's language (e.g., "Merel", "Blackbird", "Koltrast")
        cursor.execute("""
            SELECT rowid, Date, Time, Sci_Name, Com_Name, Confidence, File_Name
            FROM detections
            WHERE rowid > ?
            ORDER BY rowid ASC
            LIMIT 100
        """, (self.last_processed_id,))

        detections = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return detections

    def _find_audio_file(self, detection: dict) -> Path | None:
        """Find audio file for detection."""
        file_name = detection.get('File_Name', '')
        if not file_name:
            return None

        # If File_Name is already an absolute path, use it directly
        if file_name.startswith('/'):
            audio_path = Path(file_name)
            if audio_path.exists():
                return audio_path
            # Also try just the filename part
            file_name = audio_path.name

        # Try direct path first (relative to birdnet_dir)
        audio_path = self.birdnet_dir / file_name
        if audio_path.exists():
            return audio_path

        # Try By_Date structure
        date_str = detection.get('Date', '')
        if date_str:
            audio_path = self.extracted_dir / date_str / file_name
            if audio_path.exists():
                return audio_path

        # Try without By_Date (some setups use flat structure)
        audio_path = self.extracted_dir / file_name
        if audio_path.exists():
            return audio_path

        # Search in extracted directory recursively
        for audio_file in self.extracted_dir.rglob(file_name):
            return audio_file

        # Last resort: search in entire BirdSongs directory
        birdsongs_dir = self.birdnet_dir / "BirdSongs"
        if birdsongs_dir.exists():
            for audio_file in birdsongs_dir.rglob(file_name):
                return audio_file

        return None

    def _store_result(self, detection: dict, result: dict):
        """Store classification result."""
        import json

        conn = sqlite3.connect(self.vocalization_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO vocalizations
            (birdnet_id, file_name, common_name, scientific_name,
             vocalization_type, vocalization_type_display, confidence, probabilities)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            detection['rowid'],
            detection.get('File_Name', ''),
            detection.get('Com_Name', ''),
            detection.get('Sci_Name', ''),
            result['type'],
            result['type_display'],
            result['confidence'],
            json.dumps(result['probabilities'])
        ))

        conn.commit()
        conn.close()

    def process_detections(self):
        """Process new detections."""
        detections = self._get_new_detections()

        if not detections:
            return

        processed = 0
        classified = 0

        for detection in detections:
            rowid = detection['rowid']
            # Use scientific name for model matching (universal across languages)
            scientific_name = detection.get('Sci_Name', '')
            # Common name for display (in user's language)
            common_name = detection.get('Com_Name', '')

            # Check if we have a model for this species (by scientific name)
            if not self.classifier.has_model(scientific_name):
                logger.warning(f"No model for: {scientific_name} ({common_name})")
                self.last_processed_id = rowid
                processed += 1
                continue

            logger.debug(f"Model found for: {scientific_name}")

            # Find audio file
            audio_path = self._find_audio_file(detection)
            if not audio_path:
                logger.warning(f"Audio not found for {common_name} ({scientific_name}): {detection.get('File_Name')}")
                self.last_processed_id = rowid
                processed += 1
                continue

            logger.debug(f"Found audio: {audio_path}")

            # Classify using scientific name
            result = self.classifier.classify(scientific_name, audio_path)

            if result and result['confidence'] >= MIN_CONFIDENCE:
                self._store_result(detection, result)
                classified += 1
                logger.info(
                    f"{common_name} ({scientific_name}): {result['type_display']} ({result['confidence']:.0%})"
                )

            self.last_processed_id = rowid
            processed += 1

        if processed > 0:
            self._save_last_processed()
            logger.info(f"Processed {processed} detections, classified {classified}")

    def run(self, interval: int = DEFAULT_INTERVAL):
        """Run the service loop."""
        self.running = True
        logger.info(f"Service started, checking every {interval}s")
        logger.info(f"Monitoring: {self.birdnet_db}")
        logger.info(f"Models: {self.classifier.models_dir}")
        logger.info(f"Available species: {len(self.classifier.get_available_species())}")

        while self.running:
            try:
                self.process_detections()
            except Exception as e:
                logger.error(f"Error processing detections: {e}")

            time.sleep(interval)

    def stop(self):
        """Stop the service."""
        self.running = False
        logger.info("Service stopping...")


def main():
    parser = argparse.ArgumentParser(
        description="BirdNET Vocalization Classification Service"
    )
    parser.add_argument(
        "--birdnet-dir",
        type=Path,
        default=DEFAULT_BIRDNET_DIR,
        help=f"BirdNET-Pi installation directory (default: {DEFAULT_BIRDNET_DIR})"
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path(__file__).parent.parent / "models",
        help="Directory containing vocalization models"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data",
        help="Directory for vocalization database"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Check interval in seconds (default: {DEFAULT_INTERVAL})"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        choices=["en", "nl", "de"],
        help="Language for vocalization types: en (song/call/alarm), nl (zang/roep/alarm), de (Gesang/Ruf/Alarm)"
    )

    args = parser.parse_args()

    # Setup logging first (needs data_dir)
    global logger
    logger = setup_logging(args.data_dir)

    service = VocalizationService(
        birdnet_dir=args.birdnet_dir,
        models_dir=args.models_dir,
        data_dir=args.data_dir,
        language=args.language
    )

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    service.run(interval=args.interval)


if __name__ == "__main__":
    main()
