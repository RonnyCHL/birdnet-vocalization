#!/usr/bin/env python3
"""
BirdNET Vocalization Web Viewer

Web interface to view vocalization classification results.
Runs on port 8088 by default.

Features:
- Real-time classification results with filtering
- Spectrogram preview for each detection
- CSV/JSON export functionality
- Confidence histogram and distribution analysis
- Day/night indicators for detections
- Multi-language UI support
- Recent activity widget
- Feedback collection for model improvement

Usage:
    python webviewer.py [--port 8088] [--data-dir /path/to/data]
"""

import argparse
import csv
import io
import json
import sqlite3
import subprocess
import urllib.request
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_PORT = 8088
DEFAULT_DATA_DIR = Path("/opt/birdnet-vocalization/data")
INSTALL_DIR = Path("/opt/birdnet-vocalization")
GITHUB_API_URL = "https://api.github.com/repos/RonnyCHL/birdnet-vocalization/commits/master"

# UI Translations
TRANSLATIONS = {
    'en': {
        'title': 'BirdNET Vocalization',
        'total': 'Total',
        'songs': 'Songs',
        'calls': 'Calls',
        'alarms': 'Alarms',
        'no_model': 'No Model',
        'model_coverage': 'Model Coverage',
        'overview': 'Overview',
        'behavior': 'Behavior Insights',
        'all_types': 'All types',
        'song': 'Song',
        'call': 'Call',
        'alarm': 'Alarm',
        'filter_species': 'Filter species...',
        'min_confidence': 'Min confidence',
        'refresh': 'Refresh',
        'export': 'Export',
        'detected': 'Detected',
        'species': 'Species',
        'type': 'Type',
        'confidence': 'Confidence',
        'audio': 'Audio',
        'feedback': 'Feedback',
        'play': 'Play',
        'weekly_trends': 'Weekly Trends',
        'alerts': 'Alerts',
        'activity_by_hour': 'Activity by Hour (Last 7 Days)',
        'species_breakdown': 'Species Behavior Breakdown (Last 30 Days)',
        'confidence_distribution': 'Confidence Distribution',
        'no_data': 'No vocalizations yet. Waiting for BirdNET-Pi detections...',
        'no_alerts': 'No alerts - all normal',
        'not_enough_data': 'Not enough data yet',
        'recent_activity': 'Last 5 min',
        'day': 'Day',
        'night': 'Night',
        'update_available': 'Update Available',
        'update_now': 'Update Now',
        'later': 'Later',
        'csv': 'CSV',
        'json': 'JSON',
    },
    'nl': {
        'title': 'BirdNET Vocalisatie',
        'total': 'Totaal',
        'songs': 'Zang',
        'calls': 'Roepen',
        'alarms': 'Alarm',
        'no_model': 'Geen Model',
        'model_coverage': 'Model Dekking',
        'overview': 'Overzicht',
        'behavior': 'Gedragsinzichten',
        'all_types': 'Alle types',
        'song': 'Zang',
        'call': 'Roep',
        'alarm': 'Alarm',
        'filter_species': 'Filter soorten...',
        'min_confidence': 'Min zekerheid',
        'refresh': 'Vernieuwen',
        'export': 'Exporteren',
        'detected': 'Gedetecteerd',
        'species': 'Soort',
        'type': 'Type',
        'confidence': 'Zekerheid',
        'audio': 'Audio',
        'feedback': 'Feedback',
        'play': 'Afspelen',
        'weekly_trends': 'Weektrends',
        'alerts': 'Waarschuwingen',
        'activity_by_hour': 'Activiteit per Uur (Laatste 7 Dagen)',
        'species_breakdown': 'Soortgedrag Verdeling (Laatste 30 Dagen)',
        'confidence_distribution': 'Zekerheidsverdeling',
        'no_data': 'Nog geen vocalisaties. Wachten op BirdNET-Pi detecties...',
        'no_alerts': 'Geen waarschuwingen - alles normaal',
        'not_enough_data': 'Nog niet genoeg data',
        'recent_activity': 'Laatste 5 min',
        'day': 'Dag',
        'night': 'Nacht',
        'update_available': 'Update Beschikbaar',
        'update_now': 'Nu Updaten',
        'later': 'Later',
        'csv': 'CSV',
        'json': 'JSON',
    },
    'de': {
        'title': 'BirdNET Vokalisation',
        'total': 'Gesamt',
        'songs': 'Gesang',
        'calls': 'Rufe',
        'alarms': 'Alarm',
        'no_model': 'Kein Modell',
        'model_coverage': 'Modellabdeckung',
        'overview': 'Übersicht',
        'behavior': 'Verhaltensanalyse',
        'all_types': 'Alle Typen',
        'song': 'Gesang',
        'call': 'Ruf',
        'alarm': 'Alarm',
        'filter_species': 'Arten filtern...',
        'min_confidence': 'Min. Konfidenz',
        'refresh': 'Aktualisieren',
        'export': 'Exportieren',
        'detected': 'Erkannt',
        'species': 'Art',
        'type': 'Typ',
        'confidence': 'Konfidenz',
        'audio': 'Audio',
        'feedback': 'Feedback',
        'play': 'Abspielen',
        'weekly_trends': 'Wochentrends',
        'alerts': 'Warnungen',
        'activity_by_hour': 'Aktivität pro Stunde (Letzte 7 Tage)',
        'species_breakdown': 'Artenverhalten (Letzte 30 Tage)',
        'confidence_distribution': 'Konfidenzverteilung',
        'no_data': 'Noch keine Vokalisationen. Warte auf BirdNET-Pi Erkennungen...',
        'no_alerts': 'Keine Warnungen - alles normal',
        'not_enough_data': 'Noch nicht genug Daten',
        'recent_activity': 'Letzte 5 Min',
        'day': 'Tag',
        'night': 'Nacht',
        'update_available': 'Update verfügbar',
        'update_now': 'Jetzt aktualisieren',
        'later': 'Später',
        'csv': 'CSV',
        'json': 'JSON',
    },
    'sv': {
        'title': 'BirdNET Vokalisering',
        'total': 'Totalt',
        'songs': 'Sång',
        'calls': 'Läten',
        'alarms': 'Varning',
        'no_model': 'Ingen Modell',
        'model_coverage': 'Modelltäckning',
        'overview': 'Översikt',
        'behavior': 'Beteendeanalys',
        'all_types': 'Alla typer',
        'song': 'Sång',
        'call': 'Läte',
        'alarm': 'Varning',
        'filter_species': 'Filtrera arter...',
        'min_confidence': 'Min konfidens',
        'refresh': 'Uppdatera',
        'export': 'Exportera',
        'detected': 'Upptäckt',
        'species': 'Art',
        'type': 'Typ',
        'confidence': 'Konfidens',
        'audio': 'Ljud',
        'feedback': 'Feedback',
        'play': 'Spela',
        'weekly_trends': 'Veckotrender',
        'alerts': 'Varningar',
        'activity_by_hour': 'Aktivitet per Timme (Senaste 7 Dagarna)',
        'species_breakdown': 'Artbeteende (Senaste 30 Dagarna)',
        'confidence_distribution': 'Konfidensfördelning',
        'no_data': 'Inga vokaliseringar ännu. Väntar på BirdNET-Pi-upptäckter...',
        'no_alerts': 'Inga varningar - allt normalt',
        'not_enough_data': 'Inte tillräckligt med data ännu',
        'recent_activity': 'Senaste 5 min',
        'day': 'Dag',
        'night': 'Natt',
        'update_available': 'Uppdatering tillgänglig',
        'update_now': 'Uppdatera nu',
        'later': 'Senare',
        'csv': 'CSV',
        'json': 'JSON',
    },
}


class VocalizationHandler(BaseHTTPRequestHandler):
    """HTTP handler for vocalization viewer."""

    data_dir = DEFAULT_DATA_DIR
    birdnet_dir = None
    models_dir = None
    latitude = 52.0  # Default for day/night calculation
    longitude = 5.0

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_html_page()
        elif parsed.path == "/api/vocalizations":
            self.send_vocalizations(parsed.query)
        elif parsed.path == "/api/stats":
            self.send_stats()
        elif parsed.path == "/api/charts":
            self.send_charts()
        elif parsed.path == "/api/behavior":
            self.send_behavior_insights(parsed.query)
        elif parsed.path == "/api/audio":
            self.send_audio(parsed.query)
        elif parsed.path == "/api/spectrogram":
            self.send_spectrogram(parsed.query)
        elif parsed.path == "/api/export":
            self.send_export(parsed.query)
        elif parsed.path == "/api/recent":
            self.send_recent_activity()
        elif parsed.path == "/api/update/check":
            self.check_update()
        elif parsed.path == "/api/confidence-histogram":
            self.send_confidence_histogram()
        elif parsed.path == "/api/spectrogram/status":
            self.send_spectrogram_status()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/update/apply":
            self.apply_update()
        elif parsed.path == "/api/feedback":
            self.save_feedback()
        elif parsed.path == "/api/spectrogram/install":
            self.install_spectrogram_deps()
        else:
            self.send_error(404, "Not Found")

    def send_html_page(self):
        """Send the main HTML page with all features."""
        html = self._generate_html()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(html.encode('utf-8')))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _generate_html(self):
        """Generate the complete HTML page."""
        # Embed translations as JSON for client-side use
        translations_json = json.dumps(TRANSLATIONS)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BirdNET Vocalization Viewer</title>
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-tertiary: #0f3460;
            --text-primary: #eee;
            --text-secondary: #888;
            --accent: #4ecca3;
            --accent-hover: #3db892;
            --warning: #f9ed69;
            --danger: #f38181;
            --no-model: #9b59b6;
        }}
        [data-theme="light"] {{
            --bg-primary: #f5f5f5;
            --bg-secondary: #ffffff;
            --bg-tertiary: #e8e8e8;
            --text-primary: #333;
            --text-secondary: #666;
            --accent: #2d9a78;
            --accent-hover: #238565;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
            transition: background 0.3s, color 0.3s;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}

        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .header-left {{ display: flex; align-items: center; gap: 15px; }}
        h1 {{ color: var(--accent); font-size: 1.5em; }}
        .header-right {{ display: flex; align-items: center; gap: 10px; }}

        /* Recent Activity Widget */
        .recent-widget {{
            background: var(--bg-secondary);
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .recent-widget .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent);
            animation: pulse 2s infinite;
        }}
        .recent-counts {{ display: flex; gap: 8px; }}
        .recent-counts span {{ display: flex; align-items: center; gap: 3px; }}
        .recent-counts .song {{ color: var(--accent); }}
        .recent-counts .call {{ color: var(--warning); }}
        .recent-counts .alarm {{ color: var(--danger); }}

        /* Language selector */
        .lang-select {{
            background: var(--bg-secondary);
            border: none;
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: 5px;
            cursor: pointer;
        }}

        .theme-toggle, .export-btn {{
            background: var(--bg-secondary);
            border: none;
            padding: 8px 12px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 1.1em;
            transition: background 0.3s;
            color: var(--text-primary);
        }}
        .theme-toggle:hover, .export-btn:hover {{ background: var(--bg-tertiary); }}

        .update-indicator {{ display: flex; align-items: center; gap: 10px; }}
        .update-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #666;
        }}
        .update-dot.available {{
            background: var(--warning);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .update-btn {{
            background: var(--warning);
            color: #1a1a2e;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            display: none;
        }}
        .update-btn.visible {{ display: inline-block; }}
        .version-info {{ font-size: 0.8em; color: var(--text-secondary); }}

        /* Stats */
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-card h3 {{ color: var(--accent); font-size: 1.8em; }}
        .stat-card p {{ color: var(--text-secondary); margin-top: 5px; font-size: 0.9em; }}
        .stat-card.no-model h3 {{ color: var(--no-model); }}
        .stat-card.coverage {{ border: 2px solid var(--accent); }}
        .stat-card.coverage h3 {{ font-size: 1.3em; }}

        /* Tabs */
        .tabs {{
            display: flex;
            gap: 5px;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--bg-tertiary);
            padding-bottom: 10px;
        }}
        .tab-btn {{
            background: var(--bg-secondary);
            border: none;
            padding: 10px 20px;
            border-radius: 5px 5px 0 0;
            cursor: pointer;
            color: var(--text-secondary);
            font-weight: bold;
        }}
        .tab-btn:hover {{ background: var(--bg-tertiary); }}
        .tab-btn.active {{ background: var(--accent); color: #1a1a2e; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* Charts */
        .charts-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .chart-card {{
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 10px;
        }}
        .chart-card h3 {{
            color: var(--accent);
            margin-bottom: 15px;
            font-size: 0.95em;
        }}
        .chart-container {{ position: relative; height: 200px; }}

        /* Filters */
        .filters {{
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        .filters select, .filters input[type="text"] {{
            padding: 10px;
            border-radius: 5px;
            border: none;
            background: var(--bg-primary);
            color: var(--text-primary);
        }}
        .confidence-filter {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .confidence-filter input[type="range"] {{
            width: 100px;
            accent-color: var(--accent);
        }}
        .confidence-filter .value {{
            min-width: 40px;
            text-align: center;
            background: var(--bg-primary);
            padding: 5px 8px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .refresh-btn {{
            background: var(--accent);
            color: #1a1a2e;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }}
        .refresh-btn:hover {{ background: var(--accent-hover); }}

        /* Export dropdown */
        .export-dropdown {{
            position: relative;
            display: inline-block;
        }}
        .export-menu {{
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            background: var(--bg-secondary);
            border-radius: 5px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            z-index: 100;
            min-width: 120px;
        }}
        .export-menu.visible {{ display: block; }}
        .export-menu button {{
            display: block;
            width: 100%;
            padding: 10px 15px;
            border: none;
            background: none;
            color: var(--text-primary);
            cursor: pointer;
            text-align: left;
        }}
        .export-menu button:hover {{ background: var(--bg-tertiary); }}

        /* Table */
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-secondary);
            border-radius: 10px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--bg-primary);
        }}
        th {{ background: var(--bg-tertiary); color: var(--accent); font-size: 0.9em; }}
        tr:hover {{ background: var(--bg-primary); }}
        .type-song {{ color: var(--accent); }}
        .type-call {{ color: var(--warning); }}
        .type-alarm {{ color: var(--danger); }}
        .type-unknown {{ color: var(--no-model); }}
        .confidence {{
            background: var(--bg-tertiary);
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 0.85em;
        }}

        /* Day/Night indicator */
        .time-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }}
        .day-night {{
            font-size: 1em;
        }}

        /* Spectrogram preview */
        .spectrogram-cell {{
            width: 80px;
        }}
        .spectrogram-preview {{
            width: 70px;
            height: 35px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7em;
            color: var(--text-secondary);
            overflow: hidden;
        }}
        .spectrogram-preview img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .spectrogram-preview:hover {{ opacity: 0.8; }}

        .play-btn {{
            background: var(--accent);
            color: #1a1a2e;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
        }}
        .play-btn:hover {{ background: var(--accent-hover); }}
        .play-btn:disabled {{ background: var(--text-secondary); cursor: not-allowed; }}

        .feedback-btns {{ display: flex; gap: 5px; }}
        .feedback-btn {{
            background: var(--bg-tertiary);
            border: none;
            padding: 5px 8px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.2s;
        }}
        .feedback-btn:hover {{ transform: scale(1.1); }}
        .feedback-btn.selected.correct {{ background: var(--accent); }}
        .feedback-btn.selected.incorrect {{ background: var(--danger); }}
        .feedback-btn.faded {{ opacity: 0.3; }}

        .empty {{ text-align: center; padding: 50px; color: var(--text-secondary); }}

        /* Behavior Insights */
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .insight-card {{
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 10px;
        }}
        .insight-card h3 {{
            color: var(--accent);
            margin-bottom: 15px;
            font-size: 0.95em;
        }}
        .trend-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .trend-badge.up {{ background: rgba(78, 204, 163, 0.2); color: var(--accent); }}
        .trend-badge.down {{ background: rgba(243, 129, 129, 0.2); color: var(--danger); }}
        .trend-badge.neutral {{ background: var(--bg-tertiary); color: var(--text-secondary); }}

        .alert-list {{ list-style: none; }}
        .alert-item {{
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 5px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9em;
        }}
        .alert-item.warning {{ background: rgba(249, 237, 105, 0.2); border-left: 3px solid var(--warning); }}
        .alert-item.info {{ background: rgba(78, 204, 163, 0.1); border-left: 3px solid var(--accent); }}

        .species-bar {{
            display: flex;
            height: 18px;
            border-radius: 9px;
            overflow: hidden;
            margin: 5px 0;
        }}
        .species-bar-segment.song {{ background: var(--accent); }}
        .species-bar-segment.call {{ background: var(--warning); }}
        .species-bar-segment.alarm {{ background: var(--danger); }}
        .species-row {{ margin-bottom: 12px; }}
        .species-row-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
            font-size: 0.9em;
        }}
        .species-row-name {{ font-weight: bold; }}
        .species-row-total {{ color: var(--text-secondary); }}
        .species-legend {{
            display: flex;
            gap: 15px;
            font-size: 0.8em;
            color: var(--text-secondary);
        }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        .legend-dot.song {{ background: var(--accent); }}
        .legend-dot.call {{ background: var(--warning); }}
        .legend-dot.alarm {{ background: var(--danger); }}

        /* Confidence Histogram */
        .histogram-bars {{
            display: flex;
            align-items: flex-end;
            height: 120px;
            gap: 2px;
            padding: 10px 0;
        }}
        .histogram-bar {{
            flex: 1;
            background: var(--accent);
            border-radius: 2px 2px 0 0;
            min-height: 2px;
            position: relative;
        }}
        .histogram-bar:hover::after {{
            content: attr(data-count);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-tertiary);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.7em;
            white-space: nowrap;
        }}
        .histogram-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.75em;
            color: var(--text-secondary);
            padding-top: 5px;
        }}

        /* Audio player */
        .audio-player {{
            display: none;
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-secondary);
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 100;
            align-items: center;
            gap: 15px;
        }}
        .audio-player.visible {{ display: flex; }}
        .audio-player .species-name {{ color: var(--accent); font-weight: bold; }}
        .audio-player audio {{ height: 30px; }}
        .audio-player .close-btn {{
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 1.2em;
        }}

        /* Spectrogram Modal */
        .spectrogram-modal {{
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.8);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }}
        .spectrogram-modal.visible {{ display: flex; }}
        .spectrogram-modal-content {{
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 10px;
            max-width: 600px;
            width: 90%;
        }}
        .spectrogram-modal img {{
            width: 100%;
            border-radius: 5px;
        }}
        .spectrogram-modal .close-btn {{
            float: right;
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 1.5em;
        }}
        .spectrogram-modal h3 {{
            color: var(--accent);
            margin-bottom: 15px;
        }}

        /* Update modal */
        .update-modal {{
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.8);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }}
        .update-modal.visible {{ display: flex; }}
        .update-modal-content {{
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 10px;
            max-width: 500px;
            text-align: center;
        }}
        .update-modal h2 {{ color: var(--accent); margin-bottom: 15px; }}
        .update-modal p {{ margin-bottom: 20px; color: var(--text-secondary); }}
        .update-modal pre {{
            background: var(--bg-primary);
            padding: 15px;
            border-radius: 5px;
            text-align: left;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
            margin-bottom: 20px;
        }}
        .modal-buttons {{ display: flex; gap: 10px; justify-content: center; }}
        .modal-btn {{
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }}
        .modal-btn.primary {{ background: var(--accent); color: #1a1a2e; }}
        .modal-btn.secondary {{ background: var(--text-secondary); color: #eee; }}

        @media (max-width: 600px) {{
            .filters {{ flex-direction: column; }}
            th, td {{ padding: 8px; font-size: 0.85em; }}
            .header {{ flex-direction: column; }}
            .charts-section {{ grid-template-columns: 1fr; }}
            .recent-widget {{ display: none; }}
            .spectrogram-cell {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1 data-i18n="title">BirdNET Vocalization</h1>
                <div class="recent-widget" id="recent-widget">
                    <div class="dot"></div>
                    <span data-i18n="recent_activity">Last 5 min</span>:
                    <div class="recent-counts" id="recent-counts">
                        <span class="song">-</span>
                        <span class="call">-</span>
                        <span class="alarm">-</span>
                    </div>
                </div>
            </div>
            <div class="header-right">
                <select class="lang-select" id="lang-select" onchange="changeLanguage(this.value)">
                    <option value="en">English</option>
                    <option value="nl">Nederlands</option>
                    <option value="de">Deutsch</option>
                    <option value="sv">Svenska</option>
                </select>
                <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌙</button>
                <div class="update-indicator">
                    <span class="version-info" id="version-info"></span>
                    <div class="update-dot" id="update-dot" title="Checking..."></div>
                    <button class="update-btn" id="update-btn" onclick="showUpdateModal()" data-i18n="update_available">Update Available</button>
                </div>
            </div>
        </div>

        <div class="stats" id="stats"></div>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('overview')" data-i18n="overview">Overview</button>
            <button class="tab-btn" onclick="switchTab('behavior')" data-i18n="behavior">Behavior Insights</button>
        </div>

        <div id="tab-overview" class="tab-content active">
            <div class="charts-section">
                <div class="chart-card">
                    <h3>Vocalizations Over Time (Last 7 Days)</h3>
                    <div class="chart-container">
                        <canvas id="timeChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <h3>Top 10 Species</h3>
                    <div class="chart-container">
                        <canvas id="speciesChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="filters">
                <select id="filter-type">
                    <option value="" data-i18n="all_types">All types</option>
                    <option value="song" data-i18n="song">Song</option>
                    <option value="call" data-i18n="call">Call</option>
                    <option value="alarm" data-i18n="alarm">Alarm</option>
                    <option value="unknown">No model</option>
                </select>
                <input type="text" id="filter-species" placeholder="Filter species..." data-i18n-placeholder="filter_species">
                <div class="confidence-filter">
                    <label for="filter-confidence" data-i18n="min_confidence">Min confidence</label>:
                    <input type="range" id="filter-confidence" min="0" max="100" value="0" oninput="updateConfidenceLabel()">
                    <span class="value" id="confidence-value">0%</span>
                </div>
                <button class="refresh-btn" onclick="loadData()" data-i18n="refresh">Refresh</button>
                <div class="export-dropdown">
                    <button class="export-btn" onclick="toggleExportMenu()" data-i18n="export">📥 Export</button>
                    <div class="export-menu" id="export-menu">
                        <button onclick="exportData('csv')">📄 CSV</button>
                        <button onclick="exportData('json')">📋 JSON</button>
                    </div>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th data-i18n="detected">Detected</th>
                        <th data-i18n="species">Species</th>
                        <th data-i18n="type">Type</th>
                        <th data-i18n="confidence">Confidence</th>
                        <th class="spectrogram-cell">Spectrogram</th>
                        <th data-i18n="audio">Audio</th>
                        <th data-i18n="feedback">Feedback</th>
                    </tr>
                </thead>
                <tbody id="results"></tbody>
            </table>
        </div>

        <div id="tab-behavior" class="tab-content">
            <div class="insights-grid">
                <div class="insight-card">
                    <h3 data-i18n="weekly_trends">Weekly Trends</h3>
                    <div id="trends-container">Loading...</div>
                </div>
                <div class="insight-card">
                    <h3 data-i18n="alerts">Alerts</h3>
                    <ul class="alert-list" id="alerts-container">Loading...</ul>
                </div>
                <div class="insight-card">
                    <h3 data-i18n="confidence_distribution">Confidence Distribution</h3>
                    <div id="confidence-histogram">Loading...</div>
                </div>
            </div>

            <div class="insights-grid">
                <div class="insight-card" style="grid-column: span 2;">
                    <h3 data-i18n="activity_by_hour">Activity by Hour (Last 7 Days)</h3>
                    <div class="chart-container" style="height: 200px;">
                        <canvas id="hourlyChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="insight-card">
                <h3 data-i18n="species_breakdown">Species Behavior Breakdown (Last 30 Days)</h3>
                <div class="species-legend">
                    <span class="legend-item"><span class="legend-dot song"></span> <span data-i18n="song">Song</span></span>
                    <span class="legend-item"><span class="legend-dot call"></span> <span data-i18n="call">Call</span></span>
                    <span class="legend-item"><span class="legend-dot alarm"></span> <span data-i18n="alarm">Alarm</span></span>
                </div>
                <div id="species-breakdown" style="margin-top: 15px;">Loading...</div>
            </div>
        </div>
    </div>

    <div class="audio-player" id="audio-player">
        <span class="species-name" id="player-species"></span>
        <audio id="audio-element" controls></audio>
        <button class="close-btn" onclick="closePlayer()">×</button>
    </div>

    <div class="spectrogram-modal" id="spectrogram-modal" onclick="closeSpectrogram(event)">
        <div class="spectrogram-modal-content" onclick="event.stopPropagation()">
            <button class="close-btn" onclick="closeSpectrogram()">×</button>
            <h3 id="spectrogram-title">Spectrogram</h3>
            <img id="spectrogram-image" src="" alt="Spectrogram" style="display:none">
            <div id="spectrogram-install" style="display:none; text-align:center; padding:20px;">
                <p style="color:var(--text-secondary); margin-bottom:15px;">Spectrogram requires matplotlib & librosa</p>
                <button class="modal-btn primary" onclick="installSpectrogramDeps()">Install Dependencies</button>
                <p id="install-status" style="margin-top:10px; font-size:12px;"></p>
            </div>
            <div id="spectrogram-loading" style="display:none; text-align:center; padding:40px; color:var(--text-secondary);">
                Loading spectrogram...
            </div>
        </div>
    </div>

    <div class="update-modal" id="update-modal">
        <div class="update-modal-content">
            <h2 data-i18n="update_available">Update Available</h2>
            <p id="update-message">A new version is available.</p>
            <pre id="update-details"></pre>
            <div class="modal-buttons">
                <button class="modal-btn secondary" onclick="hideUpdateModal()" data-i18n="later">Later</button>
                <button class="modal-btn primary" id="apply-update-btn" onclick="applyUpdate()" data-i18n="update_now">Update Now</button>
            </div>
        </div>
    </div>

    <script>
        // Translations
        const TRANSLATIONS = {translations_json};
        let currentLang = localStorage.getItem('lang') || 'en';

        // Global state
        var updateInfo = null;
        var timeChart = null;
        var speciesChart = null;
        var hourlyChart = null;
        var initialized = false;
        var behaviorLoaded = false;

        // Language
        function changeLanguage(lang) {{
            currentLang = lang;
            localStorage.setItem('lang', lang);
            applyTranslations();
            loadStats();
            loadData();
        }}

        function applyTranslations() {{
            const t = TRANSLATIONS[currentLang] || TRANSLATIONS['en'];
            document.querySelectorAll('[data-i18n]').forEach(el => {{
                const key = el.getAttribute('data-i18n');
                if (t[key]) el.textContent = t[key];
            }});
            document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {{
                const key = el.getAttribute('data-i18n-placeholder');
                if (t[key]) el.placeholder = t[key];
            }});
            document.getElementById('lang-select').value = currentLang;
        }}

        function t(key) {{
            return (TRANSLATIONS[currentLang] || TRANSLATIONS['en'])[key] || key;
        }}

        // Theme
        function toggleTheme() {{
            const body = document.body;
            const btn = document.getElementById('theme-toggle');
            if (body.dataset.theme === 'light') {{
                body.dataset.theme = 'dark';
                btn.textContent = '🌙';
                localStorage.setItem('theme', 'dark');
            }} else {{
                body.dataset.theme = 'light';
                btn.textContent = '☀️';
                localStorage.setItem('theme', 'light');
            }}
            updateChartColors();
        }}

        function initTheme() {{
            const saved = localStorage.getItem('theme') || 'dark';
            document.body.dataset.theme = saved;
            document.getElementById('theme-toggle').textContent = saved === 'light' ? '☀️' : '🌙';
        }}

        function getChartColors() {{
            const isDark = document.body.dataset.theme !== 'light';
            return {{
                text: isDark ? '#eee' : '#333',
                grid: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                song: '#4ecca3',
                call: '#f9ed69',
                alarm: '#f38181'
            }};
        }}

        function updateChartColors() {{
            const colors = getChartColors();
            [timeChart, speciesChart, hourlyChart].forEach(chart => {{
                if (chart) {{
                    chart.options.scales.x.ticks.color = colors.text;
                    chart.options.scales.y.ticks.color = colors.text;
                    chart.options.scales.x.grid.color = colors.grid;
                    chart.options.scales.y.grid.color = colors.grid;
                    if (chart.options.plugins.legend) {{
                        chart.options.plugins.legend.labels.color = colors.text;
                    }}
                    chart.update();
                }}
            }});
        }}

        // Tab switching
        function switchTab(tabName) {{
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.toggle('active', btn.textContent.toLowerCase().includes(tabName.substring(0, 4)));
            }});
            document.querySelectorAll('.tab-content').forEach(content => {{
                content.classList.toggle('active', content.id === 'tab-' + tabName);
            }});
            if (tabName === 'behavior' && !behaviorLoaded) {{
                loadBehaviorData();
                behaviorLoaded = true;
            }}
        }}

        // Recent activity widget
        async function loadRecentActivity() {{
            try {{
                const res = await fetch('/api/recent');
                const data = await res.json();
                const counts = document.getElementById('recent-counts');
                counts.innerHTML = `
                    <span class="song">♫${{data.song || 0}}</span>
                    <span class="call">◐${{data.call || 0}}</span>
                    <span class="alarm">⚠${{data.alarm || 0}}</span>
                `;
            }} catch (e) {{ console.error('Recent activity error:', e); }}
        }}

        // Confidence slider
        function updateConfidenceLabel() {{
            const slider = document.getElementById('filter-confidence');
            document.getElementById('confidence-value').textContent = slider.value + '%';
        }}

        // Export
        function toggleExportMenu() {{
            document.getElementById('export-menu').classList.toggle('visible');
        }}

        function exportData(format) {{
            const type = document.getElementById('filter-type').value;
            const species = document.getElementById('filter-species').value;
            const minConf = document.getElementById('filter-confidence').value / 100;

            let url = `/api/export?format=${{format}}&limit=1000`;
            if (type) url += `&type=${{type}}`;
            if (species) url += `&species=${{encodeURIComponent(species)}}`;
            if (minConf > 0) url += `&min_confidence=${{minConf}}`;

            window.location.href = url;
            document.getElementById('export-menu').classList.remove('visible');
        }}

        // Close export menu on click outside
        document.addEventListener('click', (e) => {{
            if (!e.target.closest('.export-dropdown')) {{
                document.getElementById('export-menu').classList.remove('visible');
            }}
        }});

        // Spectrogram
        let spectrogramAvailable = null;

        async function checkSpectrogramStatus() {{
            if (spectrogramAvailable !== null) return spectrogramAvailable;
            try {{
                const res = await fetch('/api/spectrogram/status');
                const data = await res.json();
                spectrogramAvailable = data.available;
                return spectrogramAvailable;
            }} catch (e) {{
                return false;
            }}
        }}

        async function showSpectrogram(filename, species) {{
            const modal = document.getElementById('spectrogram-modal');
            const img = document.getElementById('spectrogram-image');
            const installDiv = document.getElementById('spectrogram-install');
            const loadingDiv = document.getElementById('spectrogram-loading');

            document.getElementById('spectrogram-title').textContent = species + ' - Spectrogram';
            img.style.display = 'none';
            installDiv.style.display = 'none';
            loadingDiv.style.display = 'block';
            modal.classList.add('visible');

            const available = await checkSpectrogramStatus();
            loadingDiv.style.display = 'none';

            if (available) {{
                img.src = '/api/spectrogram?file=' + encodeURIComponent(filename);
                img.style.display = 'block';
            }} else {{
                installDiv.style.display = 'block';
                document.getElementById('install-status').textContent = '';
            }}
        }}

        async function installSpectrogramDeps() {{
            const statusEl = document.getElementById('install-status');
            statusEl.textContent = 'Installing matplotlib & librosa... (this may take a few minutes)';
            statusEl.style.color = 'var(--accent)';

            try {{
                const res = await fetch('/api/spectrogram/install', {{ method: 'POST' }});
                const data = await res.json();

                if (data.success) {{
                    statusEl.textContent = 'Installed! Service restarting...';
                    statusEl.style.color = 'var(--accent)';
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 3000);
                }} else {{
                    statusEl.textContent = 'Error: ' + data.error;
                    statusEl.style.color = 'var(--danger)';
                }}
            }} catch (e) {{
                statusEl.textContent = 'Error: ' + e.message;
                statusEl.style.color = 'var(--danger)';
            }}
        }}

        function closeSpectrogram(e) {{
            if (!e || e.target === document.getElementById('spectrogram-modal')) {{
                document.getElementById('spectrogram-modal').classList.remove('visible');
            }}
        }}

        // Day/night calculation (simplified)
        function isDaytime(timeStr) {{
            const hour = new Date(timeStr).getHours();
            return hour >= 6 && hour < 21;
        }}

        // Stats
        async function loadStats() {{
            try {{
                const res = await fetch('/api/stats');
                const stats = await res.json();
                const coverage = stats.coverage || {{ covered: 0, total: 0, percent: 0 }};
                document.getElementById('stats').innerHTML = `
                    <div class="stat-card"><h3>${{stats.total}}</h3><p>${{t('total')}}</p></div>
                    <div class="stat-card"><h3>${{stats.song || 0}}</h3><p>${{t('songs')}}</p></div>
                    <div class="stat-card"><h3>${{stats.call || 0}}</h3><p>${{t('calls')}}</p></div>
                    <div class="stat-card"><h3>${{stats.alarm || 0}}</h3><p>${{t('alarms')}}</p></div>
                    <div class="stat-card no-model"><h3>${{stats.no_model || 0}}</h3><p>${{t('no_model')}}</p></div>
                    <div class="stat-card coverage"><h3>${{coverage.covered}}/${{coverage.total}} (${{coverage.percent}}%)</h3><p>${{t('model_coverage')}}</p></div>
                `;
            }} catch (e) {{ console.error('Stats error:', e); }}
        }}

        // Charts
        async function loadCharts() {{
            try {{
                const res = await fetch('/api/charts');
                const data = await res.json();
                const colors = getChartColors();

                const timeCtx = document.getElementById('timeChart').getContext('2d');
                if (timeChart) timeChart.destroy();
                timeChart = new Chart(timeCtx, {{
                    type: 'bar',
                    data: {{
                        labels: data.daily.labels,
                        datasets: [
                            {{ label: t('song'), data: data.daily.song, backgroundColor: colors.song }},
                            {{ label: t('call'), data: data.daily.call, backgroundColor: colors.call }},
                            {{ label: t('alarm'), data: data.daily.alarm, backgroundColor: colors.alarm }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ labels: {{ color: colors.text }} }} }},
                        scales: {{
                            x: {{ stacked: true, ticks: {{ color: colors.text }}, grid: {{ color: colors.grid }} }},
                            y: {{ stacked: true, ticks: {{ color: colors.text }}, grid: {{ color: colors.grid }} }}
                        }}
                    }}
                }});

                const speciesCtx = document.getElementById('speciesChart').getContext('2d');
                if (speciesChart) speciesChart.destroy();
                speciesChart = new Chart(speciesCtx, {{
                    type: 'bar',
                    data: {{
                        labels: data.top_species.labels,
                        datasets: [{{ label: 'Count', data: data.top_species.values, backgroundColor: colors.song }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            x: {{ ticks: {{ color: colors.text }}, grid: {{ color: colors.grid }} }},
                            y: {{ ticks: {{ color: colors.text }}, grid: {{ display: false }} }}
                        }}
                    }}
                }});
            }} catch (e) {{ console.error('Charts error:', e); }}
        }}

        // Data table
        async function loadData() {{
            const type = document.getElementById('filter-type').value;
            const species = document.getElementById('filter-species').value;
            const minConfidence = document.getElementById('filter-confidence').value / 100;
            let url = '/api/vocalizations?limit=100';
            if (type) url += '&type=' + type;
            if (species) url += '&species=' + encodeURIComponent(species);
            if (minConfidence > 0) url += '&min_confidence=' + minConfidence;

            try {{
                const res = await fetch(url);
                const data = await res.json();
                const tbody = document.getElementById('results');

                if (data.length === 0) {{
                    tbody.innerHTML = `<tr><td colspan="7" class="empty">${{t('no_data')}}</td></tr>`;
                    return;
                }}

                tbody.innerHTML = data.map(row => {{
                    let timeStr = row.display_time || row.classified_at;
                    if (!row.detection_time && row.classified_at) {{
                        timeStr = new Date(row.classified_at + 'Z').toLocaleString();
                    }}
                    const dayNight = isDaytime(timeStr) ? '☀️' : '🌙';
                    const typeClass = row.vocalization_type ? 'type-' + row.vocalization_type : 'type-unknown';
                    const typeDisplay = row.vocalization_type_display || row.vocalization_type || 'N/A';
                    const confDisplay = row.confidence ? Math.round(row.confidence * 100) + '%' : '-';

                    return `
                    <tr>
                        <td><span class="time-indicator"><span class="day-night">${{dayNight}}</span> ${{timeStr}}</span></td>
                        <td>${{row.common_name}}</td>
                        <td class="${{typeClass}}">${{typeDisplay.toUpperCase()}}</td>
                        <td><span class="confidence">${{confDisplay}}</span></td>
                        <td class="spectrogram-cell">
                            <div class="spectrogram-preview" onclick="showSpectrogram('${{row.file_name}}', '${{row.common_name}}')" title="View spectrogram">
                                📊
                            </div>
                        </td>
                        <td><button class="play-btn" onclick="playAudio('${{row.file_name}}', '${{row.common_name}}')" ${{row.file_name ? '' : 'disabled'}}>▶</button></td>
                        <td class="feedback-btns" id="feedback-${{row.id}}">
                            <button class="feedback-btn" onclick="sendFeedback(${{row.id}}, true, this)" title="Correct">👍</button>
                            <button class="feedback-btn" onclick="sendFeedback(${{row.id}}, false, this)" title="Incorrect">👎</button>
                        </td>
                    </tr>
                    `;
                }}).join('');
            }} catch (e) {{
                document.getElementById('results').innerHTML = '<tr><td colspan="7" class="empty">Error loading data</td></tr>';
            }}
        }}

        // Behavior data
        async function loadBehaviorData() {{
            try {{
                const res = await fetch('/api/behavior');
                const data = await res.json();
                renderTrends(data.trends);
                renderAlerts(data.alerts);
                renderSpeciesBreakdown(data.species_breakdown);
                renderHourlyChart(data.hourly_patterns);
                loadConfidenceHistogram();
            }} catch (e) {{ console.error('Behavior data error:', e); }}
        }}

        function renderTrends(trends) {{
            const container = document.getElementById('trends-container');
            if (!trends || trends.length === 0) {{
                container.innerHTML = `<p style="color: var(--text-secondary)">${{t('not_enough_data')}}</p>`;
                return;
            }}
            container.innerHTML = trends.map(tr => {{
                const arrow = tr.change_pct > 0 ? '↑' : (tr.change_pct < 0 ? '↓' : '→');
                const cls = tr.change_pct > 0 ? 'up' : (tr.change_pct < 0 ? 'down' : 'neutral');
                return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <span class="type-${{tr.type}}" style="text-transform:capitalize;font-weight:bold;">${{t(tr.type)}}</span>
                    <span class="trend-badge ${{cls}}">${{arrow}} ${{Math.abs(tr.change_pct)}}% (${{tr.this_week}} vs ${{tr.last_week}})</span>
                </div>`;
            }}).join('');
        }}

        function renderAlerts(alerts) {{
            const container = document.getElementById('alerts-container');
            if (!alerts || alerts.length === 0) {{
                container.innerHTML = `<li style="color:var(--text-secondary);padding:10px;">${{t('no_alerts')}}</li>`;
                return;
            }}
            container.innerHTML = alerts.map(a => `
                <li class="alert-item ${{a.severity}}">
                    <span>${{a.type === 'alarm_spike' ? '⚠️' : 'ℹ️'}}</span>
                    <span>${{a.message}}</span>
                </li>
            `).join('');
        }}

        function renderSpeciesBreakdown(species) {{
            const container = document.getElementById('species-breakdown');
            if (!species || species.length === 0) {{
                container.innerHTML = `<p style="color:var(--text-secondary)">${{t('not_enough_data')}}</p>`;
                return;
            }}
            container.innerHTML = species.map(s => `
                <div class="species-row">
                    <div class="species-row-header">
                        <span class="species-row-name">${{s.species}}</span>
                        <span class="species-row-total">${{s.total}} total</span>
                    </div>
                    <div class="species-bar">
                        <div class="species-bar-segment song" style="width:${{s.song_pct}}%"></div>
                        <div class="species-bar-segment call" style="width:${{s.call_pct}}%"></div>
                        <div class="species-bar-segment alarm" style="width:${{s.alarm_pct}}%"></div>
                    </div>
                </div>
            `).join('');
        }}

        function renderHourlyChart(data) {{
            if (!data || !data.labels) return;
            const colors = getChartColors();
            const ctx = document.getElementById('hourlyChart').getContext('2d');
            if (hourlyChart) hourlyChart.destroy();
            hourlyChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: data.labels,
                    datasets: [
                        {{ label: t('song'), data: data.song, borderColor: colors.song, backgroundColor: 'transparent', tension: 0.3 }},
                        {{ label: t('call'), data: data.call, borderColor: colors.call, backgroundColor: 'transparent', tension: 0.3 }},
                        {{ label: t('alarm'), data: data.alarm, borderColor: colors.alarm, backgroundColor: 'transparent', tension: 0.3 }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ labels: {{ color: colors.text }} }} }},
                    scales: {{
                        x: {{ ticks: {{ color: colors.text }}, grid: {{ color: colors.grid }} }},
                        y: {{ ticks: {{ color: colors.text }}, grid: {{ color: colors.grid }}, beginAtZero: true }}
                    }}
                }}
            }});
        }}

        async function loadConfidenceHistogram() {{
            try {{
                const res = await fetch('/api/confidence-histogram');
                const data = await res.json();
                const container = document.getElementById('confidence-histogram');
                const maxCount = Math.max(...data.counts, 1);

                let barsHtml = data.counts.map((count, i) => {{
                    const height = (count / maxCount) * 100;
                    return `<div class="histogram-bar" style="height:${{height}}%" data-count="${{count}} (${{data.labels[i]}})"></div>`;
                }}).join('');

                container.innerHTML = `
                    <div class="histogram-bars">${{barsHtml}}</div>
                    <div class="histogram-labels">
                        <span>0%</span>
                        <span>25%</span>
                        <span>50%</span>
                        <span>75%</span>
                        <span>100%</span>
                    </div>
                `;
            }} catch (e) {{ console.error('Histogram error:', e); }}
        }}

        // Feedback
        async function sendFeedback(id, correct, btn) {{
            try {{
                const res = await fetch('/api/feedback', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ id: id, correct: correct }})
                }});
                const data = await res.json();
                if (data.success) {{
                    const container = document.getElementById('feedback-' + id);
                    container.querySelectorAll('.feedback-btn').forEach(b => {{
                        b.classList.remove('selected', 'faded', 'correct', 'incorrect');
                        if (b === btn) {{
                            b.classList.add('selected', correct ? 'correct' : 'incorrect');
                        }} else {{
                            b.classList.add('faded');
                        }}
                    }});
                }}
            }} catch (e) {{ console.error('Feedback error:', e); }}
        }}

        // Audio
        function playAudio(filename, species) {{
            if (!filename) return;
            const player = document.getElementById('audio-player');
            const audio = document.getElementById('audio-element');
            audio.src = '/api/audio?file=' + encodeURIComponent(filename);
            document.getElementById('player-species').textContent = species;
            player.classList.add('visible');
            audio.play().catch(e => console.log('Playback error:', e));
        }}

        function closePlayer() {{
            document.getElementById('audio-element').pause();
            document.getElementById('audio-player').classList.remove('visible');
        }}

        // Update
        async function checkUpdate() {{
            const dot = document.getElementById('update-dot');
            const btn = document.getElementById('update-btn');
            const versionInfo = document.getElementById('version-info');
            dot.className = 'update-dot';
            try {{
                const res = await fetch('/api/update/check');
                const data = await res.json();
                updateInfo = data;
                versionInfo.textContent = 'v' + data.local_commit.substring(0, 7);
                if (data.update_available) {{
                    dot.classList.add('available');
                    dot.title = 'Update available!';
                    btn.classList.add('visible');
                }} else {{
                    dot.style.background = '#4ecca3';
                    dot.title = 'Up to date';
                }}
            }} catch (e) {{
                dot.style.background = '#f38181';
                dot.title = 'Could not check for updates';
            }}
        }}

        function showUpdateModal() {{
            if (!updateInfo) return;
            document.getElementById('update-message').textContent = 'New version: ' + updateInfo.remote_commit.substring(0, 7);
            document.getElementById('update-details').textContent = updateInfo.commit_message || 'No details';
            document.getElementById('update-modal').classList.add('visible');
        }}

        function hideUpdateModal() {{
            document.getElementById('update-modal').classList.remove('visible');
        }}

        async function applyUpdate() {{
            const btn = document.getElementById('apply-update-btn');
            const details = document.getElementById('update-details');
            btn.disabled = true;
            btn.textContent = 'Updating...';
            details.textContent = 'Pulling latest changes...';
            try {{
                const res = await fetch('/api/update/apply', {{ method: 'POST' }});
                const data = await res.json();
                if (data.success) {{
                    details.textContent = data.output + '\\n\\nReloading...';
                    setTimeout(() => window.location.reload(), 3000);
                }} else {{
                    details.textContent = 'Failed: ' + data.error;
                    btn.disabled = false;
                    btn.textContent = t('update_now');
                }}
            }} catch (e) {{
                details.textContent = 'Error: ' + e.message;
                btn.disabled = false;
                btn.textContent = t('update_now');
            }}
        }}

        // Initialize
        function init() {{
            if (initialized) return;
            initialized = true;

            try {{
                document.getElementById('filter-type').addEventListener('change', loadData);
                document.getElementById('filter-species').addEventListener('input', loadData);
                document.getElementById('filter-confidence').addEventListener('change', loadData);

                initTheme();
                applyTranslations();
                checkUpdate();
                loadStats();
                loadData();
                loadRecentActivity();

                setInterval(loadData, 30000);
                setInterval(loadStats, 60000);
                setInterval(loadRecentActivity, 30000);
                setInterval(checkUpdate, 300000);
            }} catch (e) {{ console.error('Init error:', e); }}
        }}

        document.addEventListener('DOMContentLoaded', init);
        if (document.readyState !== 'loading') init();
    </script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script>
        if (typeof Chart !== 'undefined' && typeof loadCharts === 'function') {{
            loadCharts();
            setInterval(loadCharts, 60000);
        }}
    </script>
</body>
</html>'''

    def send_recent_activity(self):
        """Send recent activity counts (last 5 minutes)."""
        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json({"song": 0, "call": 0, "alarm": 0})
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vocalization_type, COUNT(*) as count
            FROM vocalizations
            WHERE COALESCE(detection_time, classified_at) >= datetime('now', '-5 minutes')
            GROUP BY vocalization_type
        """)
        counts = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()

        self.send_json({
            "song": counts.get("song", 0),
            "call": counts.get("call", 0),
            "alarm": counts.get("alarm", 0)
        })

    def send_confidence_histogram(self):
        """Send confidence distribution data for histogram."""
        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json({"counts": [0] * 10, "labels": []})
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create 10 buckets: 0-10%, 10-20%, etc.
        buckets = [0] * 10
        labels = [f"{i*10}-{(i+1)*10}%" for i in range(10)]

        cursor.execute("SELECT confidence FROM vocalizations WHERE confidence IS NOT NULL")
        for row in cursor.fetchall():
            conf = row[0]
            bucket = min(int(conf * 10), 9)
            buckets[bucket] += 1

        conn.close()
        self.send_json({"counts": buckets, "labels": labels})

    def send_spectrogram(self, query_string):
        """Generate and send a spectrogram image for the audio file."""
        params = parse_qs(query_string)
        filename = params.get("file", [None])[0]

        if not filename:
            self.send_error(404, "File not found")
            return

        # Security check
        if ".." in filename or filename.startswith("/"):
            self.send_error(403, "Forbidden")
            return

        # Find audio file
        audio_path = self._find_audio_file(filename)
        if not audio_path:
            # Return placeholder
            self._send_spectrogram_placeholder()
            return

        try:
            # Try to generate spectrogram using matplotlib and librosa
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import librosa
            import librosa.display
            import numpy as np

            y, sr = librosa.load(str(audio_path), sr=None, duration=3.0)
            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            S_dB = librosa.power_to_db(S, ref=np.max)

            fig, ax = plt.subplots(figsize=(4, 2))
            librosa.display.specshow(S_dB, sr=sr, ax=ax, cmap='magma')
            ax.axis('off')
            plt.tight_layout(pad=0)

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            buf.seek(0)

            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", len(buf.getvalue()))
            self.send_header("Cache-Control", "max-age=3600")
            self.end_headers()
            self.wfile.write(buf.getvalue())

        except ImportError:
            self._send_spectrogram_placeholder(missing_deps=True)
        except Exception as e:
            self._send_spectrogram_placeholder(missing_deps=False)

    def _send_spectrogram_placeholder(self, missing_deps=False):
        """Send a placeholder SVG when spectrogram can't be generated."""
        if missing_deps:
            # SVG placeholder asking to install dependencies
            svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100" viewBox="0 0 400 100">
  <rect width="100%" height="100%" fill="#1a1a2e"/>
  <text x="200" y="35" text-anchor="middle" fill="#888" font-family="sans-serif" font-size="12">Spectrogram requires matplotlib</text>
  <rect x="140" y="50" width="120" height="30" rx="5" fill="#4ecca3" class="install-btn" style="cursor:pointer"/>
  <text x="200" y="70" text-anchor="middle" fill="#1a1a2e" font-family="sans-serif" font-size="12" font-weight="bold" style="pointer-events:none">Install Now</text>
</svg>'''
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", len(svg.encode('utf-8')))
            self.send_header("X-Spectrogram-Status", "missing-deps")
            self.end_headers()
            self.wfile.write(svg.encode('utf-8'))
        else:
            # Simple gray placeholder for other errors
            placeholder = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", len(placeholder))
            self.end_headers()
            self.wfile.write(placeholder)

    def send_spectrogram_status(self):
        """Check if spectrogram dependencies are available."""
        try:
            import matplotlib
            import librosa
            self.send_json({"available": True})
        except ImportError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else "matplotlib/librosa"
            self.send_json({"available": False, "missing": missing})

    def install_spectrogram_deps(self):
        """Install matplotlib and librosa for spectrogram generation."""
        try:
            venv_pip = INSTALL_DIR / "venv" / "bin" / "pip3"
            if not venv_pip.exists():
                self.send_json({"success": False, "error": "Virtual environment not found"})
                return

            result = subprocess.run(
                [str(venv_pip), "install", "matplotlib", "librosa", "--quiet"],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode != 0:
                self.send_json({"success": False, "error": result.stderr})
                return

            self.send_json({"success": True, "message": "Dependencies installed! Restarting service..."})

            # Restart service to pick up new dependencies
            subprocess.Popen(
                ["bash", "-c", "sleep 2 && sudo systemctl restart birdnet-vocalization-viewer"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
            )
        except subprocess.TimeoutExpired:
            self.send_json({"success": False, "error": "Installation timed out"})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def _find_audio_file(self, filename):
        """Find audio file in various locations."""
        search_dirs = []
        if self.birdnet_dir:
            search_dirs.append(self.birdnet_dir / "BirdSongs" / "Extracted" / "By_Date")
        search_dirs.append(Path.home() / "BirdSongs" / "Extracted" / "By_Date")

        for search_dir in search_dirs:
            if search_dir.exists():
                for f in search_dir.rglob(filename):
                    return f
        return None

    def send_export(self, query_string):
        """Export data as CSV or JSON."""
        params = parse_qs(query_string)
        format_type = params.get("format", ["csv"])[0]
        limit = int(params.get("limit", [1000])[0])
        voc_type = params.get("type", [None])[0]
        species = params.get("species", [None])[0]
        min_confidence = float(params.get("min_confidence", [0])[0])

        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_error(404, "No data")
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM vocalizations WHERE 1=1"
        args = []

        if voc_type and voc_type != "unknown":
            query += " AND vocalization_type = ?"
            args.append(voc_type)
        elif voc_type == "unknown":
            query += " AND vocalization_type IS NULL"
        if species:
            query += " AND common_name LIKE ?"
            args.append(f"%{species}%")
        if min_confidence > 0:
            query += " AND confidence >= ?"
            args.append(min_confidence)

        query += " ORDER BY COALESCE(detection_time, classified_at) DESC LIMIT ?"
        args.append(limit)

        cursor.execute(query, args)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if format_type == "json":
            body = json.dumps(rows, indent=2, default=str).encode('utf-8')
            content_type = "application/json"
            filename = "vocalizations.json"
        else:
            output = io.StringIO()
            if rows:
                writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            body = output.getvalue().encode('utf-8')
            content_type = "text/csv"
            filename = "vocalizations.csv"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f"attachment; filename={filename}")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def check_update(self):
        """Check if an update is available."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=INSTALL_DIR
            )
            local_commit = result.stdout.strip() if result.returncode == 0 else "unknown"

            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"User-Agent": "BirdNET-Vocalization-Updater"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                remote_commit = data.get("sha", "")
                commit_message = data.get("commit", {}).get("message", "")

            self.send_json({
                "update_available": local_commit != remote_commit and remote_commit != "",
                "local_commit": local_commit,
                "remote_commit": remote_commit,
                "commit_message": commit_message.split("\n")[0]
            })
        except Exception as e:
            self.send_json({
                "update_available": False,
                "local_commit": "unknown",
                "remote_commit": "unknown",
                "error": str(e)
            })

    def apply_update(self):
        """Apply the update."""
        try:
            subprocess.run(
                ["git", "reset", "--hard", "HEAD"],
                capture_output=True, text=True, cwd=INSTALL_DIR
            )
            result = subprocess.run(
                ["git", "pull", "origin", "master"],
                capture_output=True, text=True, cwd=INSTALL_DIR
            )

            if result.returncode != 0:
                self.send_json({"success": False, "error": result.stderr})
                return

            self.send_json({"success": True, "output": result.stdout})

            subprocess.Popen(
                ["bash", "-c", "sleep 2 && sudo systemctl restart birdnet-vocalization && sudo systemctl restart birdnet-vocalization-viewer"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
            )
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def save_feedback(self):
        """Save user feedback."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            vocalization_id = data.get('id')
            is_correct = data.get('correct')
            correct_type = data.get('correct_type')

            if vocalization_id is None or is_correct is None:
                self.send_json({"success": False, "error": "Missing fields"})
                return

            db_path = self.data_dir / "vocalization.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vocalization_id INTEGER,
                    is_correct BOOLEAN,
                    correct_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vocalization_id) REFERENCES vocalizations(id)
                )
            """)

            cursor.execute(
                "INSERT INTO feedback (vocalization_id, is_correct, correct_type) VALUES (?, ?, ?)",
                (vocalization_id, is_correct, correct_type)
            )
            conn.commit()
            conn.close()

            self.send_json({"success": True})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def send_vocalizations(self, query_string):
        """Send vocalizations as JSON."""
        params = parse_qs(query_string)
        limit = int(params.get("limit", [100])[0])
        voc_type = params.get("type", [None])[0]
        species = params.get("species", [None])[0]
        min_confidence = float(params.get("min_confidence", [0])[0])

        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json([])
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT *, COALESCE(detection_time, classified_at) as display_time FROM vocalizations WHERE 1=1"
        args = []

        if voc_type and voc_type != "unknown":
            query += " AND vocalization_type = ?"
            args.append(voc_type)
        elif voc_type == "unknown":
            query += " AND vocalization_type IS NULL"
        if species:
            query += " AND common_name LIKE ?"
            args.append(f"%{species}%")
        if min_confidence > 0:
            query += " AND confidence >= ?"
            args.append(min_confidence)

        query += " ORDER BY COALESCE(detection_time, classified_at) DESC LIMIT ?"
        args.append(limit)

        cursor.execute(query, args)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        self.send_json(rows)

    def send_stats(self):
        """Send statistics."""
        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json({
                "total": 0, "no_model": 0,
                "coverage": {"covered": 0, "total": 0, "percent": 0}
            })
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM vocalizations")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT vocalization_type, COUNT(*) as count
            FROM vocalizations
            GROUP BY vocalization_type
        """)
        by_type = {}
        no_model = 0
        for row in cursor.fetchall():
            if row[0] is None:
                no_model = row[1]
            else:
                by_type[row[0]] = row[1]

        cursor.execute("SELECT COUNT(DISTINCT common_name) FROM vocalizations WHERE vocalization_type IS NOT NULL")
        species_with_models = cursor.fetchone()[0]
        conn.close()

        model_count = 0
        if self.models_dir and self.models_dir.exists():
            model_count = len(list(self.models_dir.glob("*.pt")))

        coverage = {
            "covered": species_with_models,
            "total": model_count,
            "percent": round(species_with_models / model_count * 100) if model_count > 0 else 0
        }

        self.send_json({"total": total, "no_model": no_model, "coverage": coverage, **by_type})

    def send_charts(self):
        """Send chart data."""
        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json({
                "daily": {"labels": [], "song": [], "call": [], "alarm": []},
                "top_species": {"labels": [], "values": []}
            })
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT date(COALESCE(detection_time, classified_at)) as day, vocalization_type, COUNT(*) as count
            FROM vocalizations
            WHERE COALESCE(detection_time, classified_at) >= date('now', '-7 days')
            AND vocalization_type IS NOT NULL
            GROUP BY day, vocalization_type
            ORDER BY day
        """)
        daily_data = {}
        for row in cursor.fetchall():
            day, vtype, count = row
            if day not in daily_data:
                daily_data[day] = {"song": 0, "call": 0, "alarm": 0}
            if vtype:
                daily_data[day][vtype] = count

        from datetime import timedelta
        labels = []
        song_data = []
        call_data = []
        alarm_data = []
        for i in range(6, -1, -1):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            labels.append(day[-5:])
            data = daily_data.get(day, {"song": 0, "call": 0, "alarm": 0})
            song_data.append(data["song"])
            call_data.append(data["call"])
            alarm_data.append(data["alarm"])

        cursor.execute("""
            SELECT common_name, COUNT(*) as count
            FROM vocalizations
            GROUP BY common_name
            ORDER BY count DESC
            LIMIT 10
        """)
        top_species = cursor.fetchall()
        conn.close()

        self.send_json({
            "daily": {"labels": labels, "song": song_data, "call": call_data, "alarm": alarm_data},
            "top_species": {"labels": [r[0] for r in top_species], "values": [r[1] for r in top_species]}
        })

    def send_behavior_insights(self, query_string):
        """Send behavior insights data."""
        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json({"species_breakdown": [], "hourly_patterns": [], "alerts": [], "trends": []})
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Species breakdown
        cursor.execute("""
            SELECT common_name, vocalization_type, COUNT(*) as count
            FROM vocalizations
            WHERE COALESCE(detection_time, classified_at) >= date('now', '-30 days')
            AND vocalization_type IS NOT NULL
            GROUP BY common_name, vocalization_type
        """)
        species_data = {}
        for row in cursor.fetchall():
            name, vtype, count = row
            if name not in species_data:
                species_data[name] = {"song": 0, "call": 0, "alarm": 0, "total": 0}
            species_data[name][vtype] = count
            species_data[name]["total"] += count

        species_breakdown = []
        for name, data in sorted(species_data.items(), key=lambda x: x[1]["total"], reverse=True)[:15]:
            total = data["total"]
            if total > 0:
                species_breakdown.append({
                    "species": name, "total": total,
                    "song_pct": round(data["song"] / total * 100),
                    "call_pct": round(data["call"] / total * 100),
                    "alarm_pct": round(data["alarm"] / total * 100)
                })

        # Hourly patterns
        cursor.execute("""
            SELECT strftime('%H', COALESCE(detection_time, classified_at)) as hour, vocalization_type, COUNT(*) as count
            FROM vocalizations
            WHERE COALESCE(detection_time, classified_at) >= date('now', '-7 days')
            AND vocalization_type IS NOT NULL
            GROUP BY hour, vocalization_type
        """)
        hourly_data = {str(h).zfill(2): {"song": 0, "call": 0, "alarm": 0} for h in range(24)}
        for row in cursor.fetchall():
            hour, vtype, count = row
            if hour in hourly_data and vtype:
                hourly_data[hour][vtype] = count

        hourly_patterns = {
            "labels": [f"{h}:00" for h in range(24)],
            "song": [hourly_data[str(h).zfill(2)]["song"] for h in range(24)],
            "call": [hourly_data[str(h).zfill(2)]["call"] for h in range(24)],
            "alarm": [hourly_data[str(h).zfill(2)]["alarm"] for h in range(24)]
        }

        # Alerts
        alerts = []
        cursor.execute("""
            SELECT common_name, COUNT(*) as recent_count
            FROM vocalizations
            WHERE vocalization_type = 'alarm'
            AND COALESCE(detection_time, classified_at) >= datetime('now', '-24 hours')
            GROUP BY common_name
        """)
        recent_alarms = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT common_name, COUNT(*) * 1.0 / 7 as avg_daily
            FROM vocalizations
            WHERE vocalization_type = 'alarm'
            AND COALESCE(detection_time, classified_at) >= date('now', '-8 days')
            AND COALESCE(detection_time, classified_at) < date('now', '-1 days')
            GROUP BY common_name
        """)
        avg_alarms = {row[0]: row[1] for row in cursor.fetchall()}

        for species, count in recent_alarms.items():
            avg = avg_alarms.get(species, 0)
            if avg > 0 and count > avg * 3:
                alerts.append({
                    "type": "alarm_spike",
                    "message": f"{species}: {count} alarms in 24h (+{round((count-avg)/avg*100)}%)",
                    "severity": "warning" if count > avg * 5 else "info"
                })

        # Trends
        cursor.execute("""
            SELECT vocalization_type, COUNT(*) FROM vocalizations
            WHERE COALESCE(detection_time, classified_at) >= date('now', '-7 days')
            AND vocalization_type IS NOT NULL
            GROUP BY vocalization_type
        """)
        this_week = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT vocalization_type, COUNT(*) FROM vocalizations
            WHERE COALESCE(detection_time, classified_at) >= date('now', '-14 days')
            AND COALESCE(detection_time, classified_at) < date('now', '-7 days')
            AND vocalization_type IS NOT NULL
            GROUP BY vocalization_type
        """)
        last_week = {row[0]: row[1] for row in cursor.fetchall()}

        trends = []
        for vtype in ["song", "call", "alarm"]:
            this_c = this_week.get(vtype, 0)
            last_c = last_week.get(vtype, 0)
            change = round((this_c - last_c) / last_c * 100) if last_c > 0 else 0
            trends.append({"type": vtype, "this_week": this_c, "last_week": last_c, "change_pct": change})

        conn.close()

        self.send_json({
            "species_breakdown": species_breakdown,
            "hourly_patterns": hourly_patterns,
            "alerts": alerts,
            "trends": trends
        })

    def send_audio(self, query_string):
        """Send audio file."""
        params = parse_qs(query_string)
        filename = params.get("file", [None])[0]

        if not filename or ".." in filename or filename.startswith("/"):
            self.send_error(404, "File not found")
            return

        audio_path = self._find_audio_file(filename)
        if not audio_path or not audio_path.exists():
            self.send_error(404, "Audio file not found")
            return

        content_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
        try:
            with open(audio_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(data))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, str(e))

    def send_json(self, data):
        """Send JSON response."""
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def main():
    parser = argparse.ArgumentParser(description="BirdNET Vocalization Web Viewer")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--birdnet-dir", type=Path, default=Path("/home/pi/BirdNET-Pi"))
    parser.add_argument("--models-dir", type=Path, default=INSTALL_DIR / "models")
    parser.add_argument("--latitude", type=float, default=52.0)
    parser.add_argument("--longitude", type=float, default=5.0)
    args = parser.parse_args()

    VocalizationHandler.data_dir = args.data_dir
    VocalizationHandler.birdnet_dir = args.birdnet_dir
    VocalizationHandler.models_dir = args.models_dir
    VocalizationHandler.latitude = args.latitude
    VocalizationHandler.longitude = args.longitude

    server = HTTPServer(("0.0.0.0", args.port), VocalizationHandler)
    print(f"Vocalization viewer running at http://localhost:{args.port}")
    print(f"Data directory: {args.data_dir}")
    print(f"BirdNET-Pi directory: {args.birdnet_dir}")
    print(f"Models directory: {args.models_dir}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
