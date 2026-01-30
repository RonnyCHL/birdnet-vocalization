#!/usr/bin/env python3
"""
BirdNET Vocalization Classifier

Lightweight CNN classifier for bird vocalization types (song/call/alarm).
Works with BirdNET-Pi audio files and species-specific trained models.

Usage:
    classifier = VocalizationClassifier(models_dir="/path/to/models")
    result = classifier.classify("American Robin", "/path/to/audio.mp3")
    if result:
        print(f"{result['type']} ({result['confidence']:.0%})")
        # Output: song (87%)
"""

import re
import logging
from pathlib import Path

import numpy as np

# Lazy imports for faster startup
_torch = None
_librosa = None


def get_torch():
    """Lazy load torch."""
    global _torch
    if _torch is None:
        import torch
        _torch = torch
    return _torch


def get_librosa():
    """Lazy load librosa."""
    global _librosa
    if _librosa is None:
        import librosa
        _librosa = librosa
    return _librosa


# Audio processing constants
SAMPLE_RATE = 48000
N_MELS = 128
N_FFT = 2048
HOP_LENGTH = 512
FMIN = 500
FMAX = 8000
SEGMENT_DURATION = 3.0

# Translations for vocalization types
TRANSLATIONS = {
    'en': {
        'song': 'song',
        'call': 'call',
        'alarm': 'alarm'
    },
    'nl': {
        'song': 'zang',
        'call': 'roep',
        'alarm': 'alarm'
    },
    'de': {
        'song': 'Gesang',
        'call': 'Ruf',
        'alarm': 'Alarm'
    }
}

logger = logging.getLogger(__name__)


def create_cnn_model(num_classes=3):
    """Create CNN model matching trained architecture."""
    torch = get_torch()
    nn = torch.nn

    class VocalizationCNN(nn.Module):
        """CNN model for vocalization classification."""

        def __init__(self, input_shape=(128, 128), num_classes=3):
            super().__init__()

            self.features = nn.Sequential(
                nn.Conv2d(1, 32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Dropout2d(0.25),
                nn.Conv2d(32, 64, kernel_size=3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Dropout2d(0.25),
                nn.Conv2d(64, 128, kernel_size=3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Dropout2d(0.25),
            )

            h, w = input_shape[0] // 8, input_shape[1] // 8
            flatten_size = 128 * h * w

            self.classifier = nn.Sequential(
                nn.Flatten(),
                nn.Linear(flatten_size, 256),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(256, num_classes)
            )

        def forward(self, x):
            x = self.features(x)
            x = self.classifier(x)
            return x

    return VocalizationCNN(num_classes=num_classes)


class VocalizationClassifier:
    """
    Classifier for vocalization types (song/call/alarm).

    Usage:
        classifier = VocalizationClassifier(models_dir="./models")
        result = classifier.classify("American Robin", "/path/to/audio.mp3")
        if result:
            print(f"{result['type']} ({result['confidence']:.0%})")
    """

    def __init__(self, models_dir: str | Path, max_cached_models: int = 5, language: str = 'en'):
        self.models_dir = Path(models_dir)
        self.models_cache = {}
        self.cache_order = []  # LRU tracking
        self.max_cached_models = max_cached_models
        self.available_models = {}
        self._initialized = False
        self.language = language if language in TRANSLATIONS else 'en'

    def _init_lazy(self):
        """Lazy initialization - only load when needed."""
        if self._initialized:
            return
        self._scan_models()
        self._initialized = True

    def _scan_models(self):
        """Scan available models.

        Models are named by scientific name (e.g., Turdus_merula.pt).
        This makes them work with any BirdNET-Pi language setting.
        """
        if not self.models_dir.exists():
            logger.warning(f"Models directory not found: {self.models_dir}")
            return

        for model_file in self.models_dir.glob("*.pt"):
            name = model_file.stem
            # New format: Scientific_name.pt (e.g., Turdus_merula.pt)
            # Old format: species_name_cnn_v1.pt (deprecated)

            # Remove any _cnn_v1 suffix (for backwards compatibility)
            species_name = re.sub(r'_cnn_v\d+$', '', name)

            # Store by scientific name (normalized: lowercase, spaces)
            # e.g., "Turdus_merula" -> "turdus merula"
            key = species_name.replace('_', ' ').lower()
            self.available_models[key] = model_file

        logger.info(f"Vocalization classifier: {len(self.available_models)} models loaded")

    def _normalize_name(self, name: str) -> str:
        """Normalize species name for matching."""
        normalized = name.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _find_model(self, species_name: str) -> Path | None:
        """Find model for species."""
        self._init_lazy()
        normalized = self._normalize_name(species_name)

        logger.debug(f"Looking for model: '{species_name}' -> normalized: '{normalized}'")

        if normalized in self.available_models:
            logger.debug(f"Exact match found for '{normalized}'")
            return self.available_models[normalized]

        # Fuzzy match
        for key in self.available_models:
            if key in normalized or normalized in key:
                logger.debug(f"Fuzzy match: '{normalized}' matched '{key}'")
                return self.available_models[key]

        logger.debug(f"No model found for '{normalized}'. Available models sample: {list(self.available_models.keys())[:5]}")
        return None

    def _load_model(self, model_path: Path):
        """Load model with LRU caching. Returns (model, class_names)."""
        path_str = str(model_path)

        # Cache hit
        if path_str in self.models_cache:
            if path_str in self.cache_order:
                self.cache_order.remove(path_str)
            self.cache_order.append(path_str)
            return self.models_cache[path_str]

        try:
            torch = get_torch()
            checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)

            num_classes = checkpoint.get('num_classes', 3)
            model = create_cnn_model(num_classes=num_classes)
            model.load_state_dict(checkpoint['model_state_dict'])
            model.eval()

            class_names = checkpoint.get('class_names', ['song', 'call', 'alarm'])

            # LRU cache cleanup
            while len(self.models_cache) >= self.max_cached_models and self.cache_order:
                oldest = self.cache_order.pop(0)
                if oldest in self.models_cache:
                    del self.models_cache[oldest]

            self.models_cache[path_str] = (model, class_names)
            self.cache_order.append(path_str)
            return (model, class_names)

        except Exception as e:
            logger.error(f"Error loading model {model_path}: {e}")
            return None

    def _audio_to_spectrogram(self, audio_path: Path) -> np.ndarray | None:
        """Convert audio to mel spectrogram."""
        try:
            librosa = get_librosa()
            audio, sr = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)

            segment_samples = int(SEGMENT_DURATION * SAMPLE_RATE)
            if len(audio) < segment_samples:
                padded = np.zeros(segment_samples)
                padded[:len(audio)] = audio
                audio = padded
            else:
                audio = audio[:segment_samples]

            mel_spec = librosa.feature.melspectrogram(
                y=audio, sr=SAMPLE_RATE, n_mels=N_MELS,
                n_fft=N_FFT, hop_length=HOP_LENGTH,
                fmin=FMIN, fmax=FMAX
            )

            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            mel_spec_norm = (mel_spec_db - mel_spec_db.min()) / \
                           (mel_spec_db.max() - mel_spec_db.min() + 1e-8)

            return mel_spec_norm

        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return None

    def has_model(self, species_name: str) -> bool:
        """Check if a model exists for this species."""
        self._init_lazy()
        return self._find_model(species_name) is not None

    def get_available_species(self) -> list[str]:
        """Get list of species with available models."""
        self._init_lazy()
        return [name.title() for name in self.available_models.keys()]

    def classify(self, scientific_name: str, audio_path: str | Path) -> dict | None:
        """
        Classify vocalization type.

        Args:
            scientific_name: Species scientific name (e.g., "Turdus merula")
                           Works with any format: "Turdus merula", "Turdus_merula", "turdus merula"
            audio_path: Path to audio file (MP3 or WAV)

        Returns:
            Dict with type, confidence, probabilities, or None if not possible
        """
        model_path = self._find_model(scientific_name)
        if not model_path:
            return None

        audio_path = Path(audio_path)
        if not audio_path.exists():
            return None

        result = self._load_model(model_path)
        if result is None:
            return None

        model, class_names = result

        spectrogram = self._audio_to_spectrogram(audio_path)
        if spectrogram is None:
            return None

        try:
            torch = get_torch()

            # Resize to 128x128 if needed
            if spectrogram.shape != (128, 128):
                from skimage.transform import resize
                spectrogram = resize(spectrogram, (128, 128), anti_aliasing=True)

            # To tensor
            x = torch.FloatTensor(spectrogram).unsqueeze(0).unsqueeze(0)

            with torch.no_grad():
                outputs = model(x)
                probas = torch.softmax(outputs, dim=1)[0]

            class_idx = probas.argmax().item()
            confidence = probas[class_idx].item()
            voc_type = class_names[class_idx]

            # Translate type to selected language
            trans = TRANSLATIONS.get(self.language, TRANSLATIONS['en'])
            voc_type_translated = trans.get(voc_type, voc_type)

            return {
                'type': voc_type,  # Always English internally
                'type_display': voc_type_translated,  # Translated for display
                'confidence': confidence,
                'model': model_path.name,
                'probabilities': {
                    name: probas[i].item()
                    for i, name in enumerate(class_names)
                }
            }

        except Exception as e:
            logger.error(f"Classification error: {e}")
            return None
