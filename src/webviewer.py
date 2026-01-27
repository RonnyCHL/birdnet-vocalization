#!/usr/bin/env python3
"""
BirdNET Vocalization Web Viewer

Simple web interface to view vocalization classification results.
Runs on port 8088 by default.

Usage:
    python webviewer.py [--port 8088] [--data-dir /path/to/data]
"""

import argparse
import json
import sqlite3
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_PORT = 8088
DEFAULT_DATA_DIR = Path("/opt/birdnet-vocalization/data")


class VocalizationHandler(SimpleHTTPRequestHandler):
    """HTTP handler for vocalization viewer."""

    data_dir = DEFAULT_DATA_DIR

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_html_page()
        elif parsed.path == "/api/vocalizations":
            self.send_vocalizations(parsed.query)
        elif parsed.path == "/api/stats":
            self.send_stats()
        else:
            self.send_error(404, "Not Found")

    def send_html_page(self):
        """Send the main HTML page."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BirdNET Vocalization Viewer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            text-align: center;
            margin-bottom: 20px;
            color: #4ecca3;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #16213e;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-card h3 { color: #4ecca3; font-size: 2em; }
        .stat-card p { color: #888; margin-top: 5px; }
        .filters {
            background: #16213e;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .filters select, .filters input {
            padding: 10px;
            border-radius: 5px;
            border: none;
            background: #1a1a2e;
            color: #eee;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #16213e;
            border-radius: 10px;
            overflow: hidden;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #1a1a2e;
        }
        th { background: #0f3460; color: #4ecca3; }
        tr:hover { background: #1a1a2e; }
        .type-song { color: #4ecca3; }
        .type-call { color: #f9ed69; }
        .type-alarm { color: #f38181; }
        .confidence {
            background: #0f3460;
            border-radius: 20px;
            padding: 5px 12px;
            font-size: 0.9em;
        }
        .refresh-btn {
            background: #4ecca3;
            color: #1a1a2e;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        .refresh-btn:hover { background: #3db892; }
        .empty { text-align: center; padding: 50px; color: #666; }
        @media (max-width: 600px) {
            .filters { flex-direction: column; }
            th, td { padding: 10px; font-size: 0.9em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>BirdNET Vocalization</h1>

        <div class="stats" id="stats">
            <div class="stat-card"><h3>-</h3><p>Total</p></div>
            <div class="stat-card"><h3>-</h3><p>Songs</p></div>
            <div class="stat-card"><h3>-</h3><p>Calls</p></div>
            <div class="stat-card"><h3>-</h3><p>Alarms</p></div>
        </div>

        <div class="filters">
            <select id="filter-type">
                <option value="">All types</option>
                <option value="song">Song</option>
                <option value="call">Call</option>
                <option value="alarm">Alarm</option>
            </select>
            <input type="text" id="filter-species" placeholder="Filter species...">
            <button class="refresh-btn" onclick="loadData()">Refresh</button>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Species</th>
                    <th>Type</th>
                    <th>Confidence</th>
                </tr>
            </thead>
            <tbody id="results"></tbody>
        </table>
    </div>

    <script>
        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const stats = await res.json();
                document.getElementById('stats').innerHTML = `
                    <div class="stat-card"><h3>${stats.total}</h3><p>Total</p></div>
                    <div class="stat-card"><h3>${stats.song || 0}</h3><p>Songs</p></div>
                    <div class="stat-card"><h3>${stats.call || 0}</h3><p>Calls</p></div>
                    <div class="stat-card"><h3>${stats.alarm || 0}</h3><p>Alarms</p></div>
                `;
            } catch (e) { console.error('Stats error:', e); }
        }

        async function loadData() {
            const type = document.getElementById('filter-type').value;
            const species = document.getElementById('filter-species').value;
            let url = '/api/vocalizations?limit=100';
            if (type) url += '&type=' + type;
            if (species) url += '&species=' + encodeURIComponent(species);

            try {
                const res = await fetch(url);
                const data = await res.json();
                const tbody = document.getElementById('results');

                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="empty">No vocalizations yet. Waiting for BirdNET-Pi detections...</td></tr>';
                    return;
                }

                tbody.innerHTML = data.map(row => `
                    <tr>
                        <td>${new Date(row.classified_at).toLocaleString()}</td>
                        <td>${row.common_name}</td>
                        <td class="type-${row.vocalization_type}">${(row.vocalization_type_display || row.vocalization_type).toUpperCase()}</td>
                        <td><span class="confidence">${Math.round(row.confidence * 100)}%</span></td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error('Data error:', e);
                document.getElementById('results').innerHTML =
                    '<tr><td colspan="4" class="empty">Error loading data</td></tr>';
            }
        }

        document.getElementById('filter-type').addEventListener('change', loadData);
        document.getElementById('filter-species').addEventListener('input', loadData);

        loadStats();
        loadData();
        setInterval(loadData, 30000);
        setInterval(loadStats, 30000);
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(html))
        self.end_headers()
        self.wfile.write(html.encode())

    def send_vocalizations(self, query_string):
        """Send vocalizations as JSON."""
        params = parse_qs(query_string)
        limit = int(params.get("limit", [100])[0])
        voc_type = params.get("type", [None])[0]
        species = params.get("species", [None])[0]

        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json([])
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM vocalizations WHERE 1=1"
        args = []

        if voc_type:
            query += " AND vocalization_type = ?"
            args.append(voc_type)
        if species:
            query += " AND common_name LIKE ?"
            args.append(f"%{species}%")

        query += " ORDER BY classified_at DESC LIMIT ?"
        args.append(limit)

        cursor.execute(query, args)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        self.send_json(rows)

    def send_stats(self):
        """Send statistics as JSON."""
        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json({"total": 0})
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
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()

        self.send_json({"total": total, **by_type})

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
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run on")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Data directory")
    args = parser.parse_args()

    VocalizationHandler.data_dir = args.data_dir

    server = HTTPServer(("0.0.0.0", args.port), VocalizationHandler)
    print(f"Vocalization viewer running at http://localhost:{args.port}")
    print(f"Data directory: {args.data_dir}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
