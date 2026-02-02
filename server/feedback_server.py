#!/usr/bin/env python3
"""
BirdNET Vocalization Feedback Server

Centralized feedback collection for model improvement.
Runs on NAS to receive feedback from all installations.

Usage:
    python feedback_server.py [--port 8089]

Environment variables:
    PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASS
"""

import base64
import hashlib
import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration from environment
PG_CONFIG = {
    'host': os.environ.get('PG_HOST', '192.168.1.25'),
    'port': int(os.environ.get('PG_PORT', 5433)),
    'database': os.environ.get('PG_DB', 'emsn'),
    'user': os.environ.get('PG_USER', 'birdpi_zolder'),
    'password': os.environ.get('PG_PASS', ''),
}

DEFAULT_PORT = 8089


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(**PG_CONFIG)


class FeedbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for feedback API."""

    def send_json(self, data, status=200):
        """Send JSON response."""
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def send_dashboard(self):
        """Send HTML dashboard."""
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vocalization Feedback Dashboard</title>
    <style>
        :root {
            --bg: #1a1a2e;
            --card: #16213e;
            --text: #eee;
            --muted: #888;
            --accent: #4ecca3;
            --danger: #f38181;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: var(--accent); margin-bottom: 20px; }
        h2 { color: var(--text); margin: 20px 0 10px; font-size: 1.2em; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: var(--card);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-card h3 { font-size: 2em; color: var(--accent); }
        .stat-card p { color: var(--muted); font-size: 0.9em; }
        .stat-card.danger h3 { color: var(--danger); }
        table {
            width: 100%;
            border-collapse: collapse;
            background: var(--card);
            border-radius: 10px;
            overflow: hidden;
        }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--bg); }
        th { background: var(--bg); color: var(--accent); }
        .correct { color: var(--accent); }
        .incorrect { color: var(--danger); }
        .refresh-btn {
            background: var(--accent);
            color: var(--bg);
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        .refresh-btn:hover { opacity: 0.9; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .loading { color: var(--muted); padding: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐦 Vocalization Feedback Dashboard</h1>
            <button class="refresh-btn" onclick="loadAll()">Refresh</button>
        </div>

        <div class="stats-grid" id="stats">
            <div class="stat-card"><h3>-</h3><p>Total Feedback</p></div>
        </div>

        <h2>Problem Species (need model improvement)</h2>
        <table id="problem-table">
            <thead><tr><th>Species</th><th>Common Name</th><th>Errors</th><th>Total</th></tr></thead>
            <tbody><tr><td colspan="4" class="loading">Loading...</td></tr></tbody>
        </table>

        <h2>Recent Feedback</h2>
        <table id="feedback-table">
            <thead><tr><th>Time</th><th>Species</th><th>Predicted</th><th>Correct?</th><th>Source</th></tr></thead>
            <tbody><tr><td colspan="5" class="loading">Loading...</td></tr></tbody>
        </table>
    </div>

    <script>
        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                const o = data.overall;
                document.getElementById('stats').innerHTML = `
                    <div class="stat-card"><h3>${o.total}</h3><p>Total Feedback</p></div>
                    <div class="stat-card"><h3>${o.correct}</h3><p>Correct</p></div>
                    <div class="stat-card danger"><h3>${o.incorrect}</h3><p>Incorrect</p></div>
                    <div class="stat-card"><h3>${o.accuracy}%</h3><p>Accuracy</p></div>
                    <div class="stat-card"><h3>${o.species_count}</h3><p>Species</p></div>
                    <div class="stat-card"><h3>${o.installations}</h3><p>Installations</p></div>
                `;

                const tbody = document.querySelector('#problem-table tbody');
                if (data.problem_species && data.problem_species.length > 0) {
                    tbody.innerHTML = data.problem_species.map(s => `
                        <tr>
                            <td>${s.species_scientific}</td>
                            <td>${s.species_common || '-'}</td>
                            <td class="incorrect">${s.errors}</td>
                            <td>${s.total}</td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="4">No problem species yet!</td></tr>';
                }
            } catch (e) {
                console.error('Stats error:', e);
            }
        }

        async function loadFeedback() {
            try {
                const res = await fetch('/api/feedback?limit=50');
                const data = await res.json();
                const tbody = document.querySelector('#feedback-table tbody');

                if (data.feedback && data.feedback.length > 0) {
                    tbody.innerHTML = data.feedback.map(f => `
                        <tr>
                            <td>${new Date(f.created_at).toLocaleString()}</td>
                            <td>${f.species_scientific}</td>
                            <td>${f.predicted_type}${f.correct_type ? ' → ' + f.correct_type : ''}</td>
                            <td class="${f.is_correct ? 'correct' : 'incorrect'}">${f.is_correct ? '✓' : '✗'}</td>
                            <td>${f.source_id ? f.source_id.slice(0, 8) : '-'}</td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5">No feedback yet</td></tr>';
                }
            } catch (e) {
                console.error('Feedback error:', e);
            }
        }

        function loadAll() {
            loadStats();
            loadFeedback();
        }

        loadAll();
        setInterval(loadAll, 30000);
    </script>
</body>
</html>'''
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)

        if parsed.path == '/':
            self.send_dashboard()
        elif parsed.path == '/api':
            self.send_json({
                'service': 'BirdNET Vocalization Feedback Server',
                'version': '1.0.0',
                'endpoints': {
                    'POST /api/feedback': 'Submit feedback',
                    'GET /api/stats': 'Get feedback statistics',
                    'GET /api/feedback': 'List recent feedback',
                }
            })
        elif parsed.path == '/api/stats':
            self.get_stats()
        elif parsed.path == '/api/feedback':
            self.list_feedback(parsed.query)
        elif parsed.path == '/health':
            self.send_json({'status': 'ok'})
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)

        if parsed.path == '/api/feedback':
            self.submit_feedback()
        else:
            self.send_json({'error': 'Not found'}, 404)

    def submit_feedback(self):
        """Submit new feedback."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            # Required fields
            species_scientific = data.get('species_scientific')
            predicted_type = data.get('predicted_type')
            is_correct = data.get('is_correct')

            if not all([species_scientific, predicted_type, is_correct is not None]):
                self.send_json({'error': 'Missing required fields'}, 400)
                return

            # Optional fields
            species_common = data.get('species_common')
            correct_type = data.get('correct_type')
            confidence = data.get('confidence')
            audio_filename = data.get('audio_filename')
            source_id = data.get('source_id')
            birdnet_confidence = data.get('birdnet_confidence')
            detection_time = data.get('detection_time')

            # Handle optional audio data (base64 encoded)
            audio_data = None
            audio_hash = None
            if data.get('audio_base64'):
                audio_data = base64.b64decode(data['audio_base64'])
                audio_hash = hashlib.sha256(audio_data).hexdigest()[:16]
            elif audio_filename:
                # Generate hash from filename if no audio data
                audio_hash = hashlib.sha256(audio_filename.encode()).hexdigest()[:16]

            # Parse detection time
            detection_ts = None
            if detection_time:
                try:
                    detection_ts = datetime.fromisoformat(detection_time.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass

            # Insert into database
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO vocalization_feedback (
                    species_scientific, species_common, predicted_type,
                    correct_type, is_correct, confidence, audio_hash,
                    audio_filename, audio_data, source_id,
                    birdnet_confidence, detection_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                species_scientific, species_common, predicted_type,
                correct_type, is_correct, confidence, audio_hash,
                audio_filename, audio_data, source_id,
                birdnet_confidence, detection_ts
            ))

            feedback_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()

            self.send_json({
                'success': True,
                'id': feedback_id,
                'message': 'Thank you for your feedback!'
            })

        except json.JSONDecodeError:
            self.send_json({'error': 'Invalid JSON'}, 400)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def get_stats(self):
        """Get feedback statistics."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Overall stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN NOT is_correct THEN 1 ELSE 0 END) as incorrect,
                    COUNT(DISTINCT species_scientific) as species_count,
                    COUNT(DISTINCT source_id) as source_count
                FROM vocalization_feedback
            """)
            overall = cursor.fetchone()

            # Per type stats
            cursor.execute("""
                SELECT
                    predicted_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                    ROUND(100.0 * SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy
                FROM vocalization_feedback
                GROUP BY predicted_type
                ORDER BY total DESC
            """)
            by_type = cursor.fetchall()

            # Species needing most improvement
            cursor.execute("""
                SELECT
                    species_scientific,
                    species_common,
                    COUNT(*) as total,
                    SUM(CASE WHEN NOT is_correct THEN 1 ELSE 0 END) as errors
                FROM vocalization_feedback
                GROUP BY species_scientific, species_common
                HAVING SUM(CASE WHEN NOT is_correct THEN 1 ELSE 0 END) > 0
                ORDER BY errors DESC
                LIMIT 10
            """)
            problem_species = cursor.fetchall()

            conn.close()

            accuracy = 0
            if overall['total'] > 0:
                accuracy = round(100.0 * overall['correct'] / overall['total'], 1)

            self.send_json({
                'overall': {
                    'total': overall['total'],
                    'correct': overall['correct'],
                    'incorrect': overall['incorrect'],
                    'accuracy': accuracy,
                    'species_count': overall['species_count'],
                    'installations': overall['source_count']
                },
                'by_type': by_type,
                'problem_species': problem_species
            })

        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def list_feedback(self, query_string):
        """List recent feedback."""
        try:
            params = parse_qs(query_string)
            limit = min(int(params.get('limit', [50])[0]), 500)
            species = params.get('species', [None])[0]
            incorrect_only = params.get('incorrect', ['false'])[0].lower() == 'true'

            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    id, species_scientific, species_common,
                    predicted_type, correct_type, is_correct,
                    confidence, audio_filename, source_id,
                    created_at
                FROM vocalization_feedback
                WHERE 1=1
            """
            args = []

            if species:
                query += " AND species_scientific ILIKE %s"
                args.append(f"%{species}%")

            if incorrect_only:
                query += " AND NOT is_correct"

            query += " ORDER BY created_at DESC LIMIT %s"
            args.append(limit)

            cursor.execute(query, args)
            rows = cursor.fetchall()
            conn.close()

            # Convert datetime to string
            for row in rows:
                if row.get('created_at'):
                    row['created_at'] = row['created_at'].isoformat()

            self.send_json({'feedback': rows, 'count': len(rows)})

        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def log_message(self, format, *args):
        """Log with timestamp."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Vocalization Feedback Server')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    # Test database connection
    try:
        conn = get_db_connection()
        conn.close()
        print(f"Database connection OK")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return

    server = HTTPServer(('0.0.0.0', args.port), FeedbackHandler)
    print(f"Feedback server running on http://0.0.0.0:{args.port}")
    print(f"Endpoints:")
    print(f"  POST /api/feedback  - Submit feedback")
    print(f"  GET  /api/stats     - View statistics")
    print(f"  GET  /api/feedback  - List recent feedback")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
