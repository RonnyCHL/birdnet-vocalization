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
import os
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


class VocalizationHandler(BaseHTTPRequestHandler):
    """HTTP handler for vocalization viewer."""

    # Class variables set by main()
    data_dir = DEFAULT_DATA_DIR
    birdnet_dir = None
    models_dir = None

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
        elif parsed.path == "/api/update/check":
            self.check_update()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/update/apply":
            self.apply_update()
        elif parsed.path == "/api/feedback":
            self.save_feedback()
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
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-tertiary: #0f3460;
            --text-primary: #eee;
            --text-secondary: #888;
            --accent: #4ecca3;
            --accent-hover: #3db892;
            --warning: #f9ed69;
            --danger: #f38181;
        }
        [data-theme="light"] {
            --bg-primary: #f5f5f5;
            --bg-secondary: #ffffff;
            --bg-tertiary: #e8e8e8;
            --text-primary: #333;
            --text-secondary: #666;
            --accent: #2d9a78;
            --accent-hover: #238565;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
            transition: background 0.3s, color 0.3s;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        .header-left { display: flex; align-items: center; gap: 15px; }
        h1 { color: var(--accent); }
        .header-right { display: flex; align-items: center; gap: 15px; }
        .theme-toggle {
            background: var(--bg-secondary);
            border: none;
            padding: 8px 12px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 1.2em;
            transition: background 0.3s;
        }
        .theme-toggle:hover { background: var(--bg-tertiary); }
        .update-indicator { display: flex; align-items: center; gap: 10px; }
        .update-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #666;
        }
        .update-dot.available {
            background: var(--warning);
            animation: pulse 2s infinite;
        }
        .update-dot.checking {
            background: var(--accent);
            animation: pulse 0.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .update-btn {
            background: var(--warning);
            color: #1a1a2e;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            display: none;
        }
        .update-btn:hover { opacity: 0.9; }
        .update-btn.visible { display: inline-block; }
        .version-info { font-size: 0.8em; color: var(--text-secondary); }

        /* Stats cards */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transition: background 0.3s;
        }
        .stat-card h3 { color: var(--accent); font-size: 2em; }
        .stat-card p { color: var(--text-secondary); margin-top: 5px; }
        .stat-card.coverage { border: 2px solid var(--accent); }
        .stat-card.coverage h3 { font-size: 1.5em; }

        /* Charts section */
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .chart-card {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 10px;
        }
        .chart-card h3 {
            color: var(--accent);
            margin-bottom: 15px;
            font-size: 1em;
        }
        .chart-container { position: relative; height: 200px; }

        /* Filters */
        .filters {
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        .filters select, .filters input {
            padding: 10px;
            border-radius: 5px;
            border: none;
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        .refresh-btn {
            background: var(--accent);
            color: #1a1a2e;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        .refresh-btn:hover { background: var(--accent-hover); }

        /* Table */
        table {
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-secondary);
            border-radius: 10px;
            overflow: hidden;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid var(--bg-primary);
        }
        th { background: var(--bg-tertiary); color: var(--accent); }
        tr:hover { background: var(--bg-primary); }
        tr.clickable { cursor: pointer; }
        .type-song { color: var(--accent); }
        .type-call { color: var(--warning); }
        .type-alarm { color: var(--danger); }
        .confidence {
            background: var(--bg-tertiary);
            border-radius: 20px;
            padding: 5px 12px;
            font-size: 0.9em;
        }
        .play-btn {
            background: var(--accent);
            color: #1a1a2e;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
        }
        .play-btn:hover { background: var(--accent-hover); }
        .play-btn:disabled { background: var(--text-secondary); cursor: not-allowed; }
        .empty { text-align: center; padding: 50px; color: var(--text-secondary); }
        .feedback-btns { display: flex; gap: 5px; }
        .feedback-btn {
            background: var(--bg-tertiary);
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.2s;
        }
        .feedback-btn:hover { transform: scale(1.1); }
        .feedback-btn.correct { background: var(--accent); }
        .feedback-btn.incorrect { background: var(--danger); }
        .feedback-btn.selected { opacity: 1; transform: scale(1.2); }
        .feedback-btn.faded { opacity: 0.3; }

        /* Tabs */
        .tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--bg-tertiary);
            padding-bottom: 10px;
        }
        .tab-btn {
            background: var(--bg-secondary);
            border: none;
            padding: 10px 20px;
            border-radius: 5px 5px 0 0;
            cursor: pointer;
            color: var(--text-secondary);
            font-weight: bold;
            transition: all 0.3s;
        }
        .tab-btn:hover { background: var(--bg-tertiary); }
        .tab-btn.active {
            background: var(--accent);
            color: #1a1a2e;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* Behavior Insights */
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .insight-card {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 10px;
        }
        .insight-card h3 {
            color: var(--accent);
            margin-bottom: 15px;
            font-size: 1em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .trend-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .trend-badge.up { background: rgba(78, 204, 163, 0.2); color: var(--accent); }
        .trend-badge.down { background: rgba(243, 129, 129, 0.2); color: var(--danger); }
        .trend-badge.neutral { background: var(--bg-tertiary); color: var(--text-secondary); }

        .alert-list { list-style: none; }
        .alert-item {
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .alert-item.warning { background: rgba(249, 237, 105, 0.2); border-left: 3px solid var(--warning); }
        .alert-item.info { background: rgba(78, 204, 163, 0.1); border-left: 3px solid var(--accent); }
        .alert-icon { font-size: 1.2em; }

        .species-bar {
            display: flex;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin: 5px 0;
        }
        .species-bar-segment {
            transition: width 0.3s;
        }
        .species-bar-segment.song { background: var(--accent); }
        .species-bar-segment.call { background: var(--warning); }
        .species-bar-segment.alarm { background: var(--danger); }
        .species-row {
            margin-bottom: 15px;
        }
        .species-row-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        .species-row-name { font-weight: bold; }
        .species-row-total { color: var(--text-secondary); font-size: 0.9em; }
        .species-legend {
            display: flex;
            gap: 15px;
            font-size: 0.8em;
            color: var(--text-secondary);
            margin-top: 5px;
        }
        .legend-item { display: flex; align-items: center; gap: 5px; }
        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .legend-dot.song { background: var(--accent); }
        .legend-dot.call { background: var(--warning); }
        .legend-dot.alarm { background: var(--danger); }

        /* Audio player */
        .audio-player {
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
        }
        .audio-player.visible { display: flex; }
        .audio-player .species-name { color: var(--accent); font-weight: bold; }
        .audio-player audio { height: 30px; }
        .audio-player .close-btn {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 1.2em;
        }

        /* Modal */
        .update-modal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.8);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .update-modal.visible { display: flex; }
        .update-modal-content {
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 10px;
            max-width: 500px;
            text-align: center;
        }
        .update-modal h2 { color: var(--accent); margin-bottom: 15px; }
        .update-modal p { margin-bottom: 20px; color: var(--text-secondary); }
        .update-modal pre {
            background: var(--bg-primary);
            padding: 15px;
            border-radius: 5px;
            text-align: left;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        .modal-buttons { display: flex; gap: 10px; justify-content: center; }
        .modal-btn {
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        .modal-btn.primary { background: var(--accent); color: #1a1a2e; }
        .modal-btn.secondary { background: var(--text-secondary); color: #eee; }

        @media (max-width: 600px) {
            .filters { flex-direction: column; }
            th, td { padding: 10px; font-size: 0.9em; }
            .header { flex-direction: column; }
            .charts-section { grid-template-columns: 1fr; }
            .chart-card { min-width: 0; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>BirdNET Vocalization</h1>
            </div>
            <div class="header-right">
                <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌙</button>
                <div class="update-indicator">
                    <span class="version-info" id="version-info"></span>
                    <div class="update-dot" id="update-dot" title="Checking for updates..."></div>
                    <button class="update-btn" id="update-btn" onclick="showUpdateModal()">Update Available</button>
                </div>
            </div>
        </div>

        <div class="stats" id="stats">
            <div class="stat-card"><h3>-</h3><p>Total</p></div>
            <div class="stat-card"><h3>-</h3><p>Songs</p></div>
            <div class="stat-card"><h3>-</h3><p>Calls</p></div>
            <div class="stat-card"><h3>-</h3><p>Alarms</p></div>
            <div class="stat-card coverage"><h3>-</h3><p>Model Coverage</p></div>
        </div>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
            <button class="tab-btn" onclick="switchTab('behavior')">Behavior Insights</button>
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
                    <th>Audio</th>
                    <th>Feedback</th>
                </tr>
            </thead>
            <tbody id="results"></tbody>
        </table>
        </div>

        <div id="tab-behavior" class="tab-content">
            <div class="insights-grid">
                <div class="insight-card">
                    <h3>Weekly Trends</h3>
                    <div id="trends-container">Loading...</div>
                </div>
                <div class="insight-card">
                    <h3>Alerts</h3>
                    <ul class="alert-list" id="alerts-container">Loading...</ul>
                </div>
            </div>

            <div class="insights-grid">
                <div class="insight-card" style="grid-column: span 2;">
                    <h3>Activity by Hour (Last 7 Days)</h3>
                    <div class="chart-container" style="height: 200px;">
                        <canvas id="hourlyChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="insight-card">
                <h3>Species Behavior Breakdown (Last 30 Days)</h3>
                <div class="species-legend">
                    <span class="legend-item"><span class="legend-dot song"></span> Song</span>
                    <span class="legend-item"><span class="legend-dot call"></span> Call</span>
                    <span class="legend-item"><span class="legend-dot alarm"></span> Alarm</span>
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

    <div class="update-modal" id="update-modal">
        <div class="update-modal-content">
            <h2>Update Available</h2>
            <p id="update-message">A new version is available.</p>
            <pre id="update-details"></pre>
            <div class="modal-buttons">
                <button class="modal-btn secondary" onclick="hideUpdateModal()">Later</button>
                <button class="modal-btn primary" id="apply-update-btn" onclick="applyUpdate()">Update Now</button>
            </div>
        </div>
    </div>

    <script>
        // All code in global scope for onclick handlers
        var updateInfo = null;
        var timeChart = null;
        var speciesChart = null;
        var hourlyChart = null;
        var initialized = false;
        var behaviorLoaded = false;

        // Tab switching
        function switchTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.textContent.toLowerCase().includes(tabName));
            });
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.toggle('active', content.id === 'tab-' + tabName);
            });
            // Load behavior data on first switch
            if (tabName === 'behavior' && !behaviorLoaded) {
                loadBehaviorData();
                behaviorLoaded = true;
            }
        }

        // Behavior Insights
        async function loadBehaviorData() {
            try {
                const res = await fetch('/api/behavior');
                const data = await res.json();
                renderTrends(data.trends);
                renderAlerts(data.alerts);
                renderSpeciesBreakdown(data.species_breakdown);
                renderHourlyChart(data.hourly_patterns);
            } catch (e) {
                console.error('Behavior data error:', e);
            }
        }

        function renderTrends(trends) {
            const container = document.getElementById('trends-container');
            if (!trends || trends.length === 0) {
                container.innerHTML = '<p style="color: var(--text-secondary)">Not enough data yet</p>';
                return;
            }
            container.innerHTML = trends.map(t => {
                const arrow = t.change_pct > 0 ? '↑' : (t.change_pct < 0 ? '↓' : '→');
                const cls = t.change_pct > 0 ? 'up' : (t.change_pct < 0 ? 'down' : 'neutral');
                return `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span class="type-${t.type}" style="text-transform: capitalize; font-weight: bold;">${t.type}</span>
                        <span class="trend-badge ${cls}">${arrow} ${Math.abs(t.change_pct)}% (${t.this_week} vs ${t.last_week})</span>
                    </div>
                `;
            }).join('');
        }

        function renderAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<li style="color: var(--text-secondary); padding: 10px;">No alerts - all normal</li>';
                return;
            }
            container.innerHTML = alerts.map(a => `
                <li class="alert-item ${a.severity}">
                    <span class="alert-icon">${a.type === 'alarm_spike' ? '⚠️' : 'ℹ️'}</span>
                    <span>${a.message}</span>
                </li>
            `).join('');
        }

        function renderSpeciesBreakdown(species) {
            const container = document.getElementById('species-breakdown');
            if (!species || species.length === 0) {
                container.innerHTML = '<p style="color: var(--text-secondary)">Not enough data yet</p>';
                return;
            }
            container.innerHTML = species.map(s => `
                <div class="species-row">
                    <div class="species-row-header">
                        <span class="species-row-name">${s.species}</span>
                        <span class="species-row-total">${s.total} total</span>
                    </div>
                    <div class="species-bar">
                        <div class="species-bar-segment song" style="width: ${s.song_pct}%"></div>
                        <div class="species-bar-segment call" style="width: ${s.call_pct}%"></div>
                        <div class="species-bar-segment alarm" style="width: ${s.alarm_pct}%"></div>
                    </div>
                </div>
            `).join('');
        }

        function renderHourlyChart(data) {
            if (!data || !data.labels) return;
            const colors = getChartColors();
            const ctx = document.getElementById('hourlyChart').getContext('2d');
            if (hourlyChart) hourlyChart.destroy();
            hourlyChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [
                        { label: 'Song', data: data.song, borderColor: colors.song, backgroundColor: 'transparent', tension: 0.3 },
                        { label: 'Call', data: data.call, borderColor: colors.call, backgroundColor: 'transparent', tension: 0.3 },
                        { label: 'Alarm', data: data.alarm, borderColor: colors.alarm, backgroundColor: 'transparent', tension: 0.3 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: colors.text } } },
                    scales: {
                        x: { ticks: { color: colors.text }, grid: { color: colors.grid } },
                        y: { ticks: { color: colors.text }, grid: { color: colors.grid }, beginAtZero: true }
                    }
                }
            });
        }

        // Theme management - must be global for onclick
        function toggleTheme() {
            const body = document.body;
            const btn = document.getElementById('theme-toggle');
            if (body.dataset.theme === 'light') {
                body.dataset.theme = 'dark';
                btn.textContent = '🌙';
                localStorage.setItem('theme', 'dark');
            } else {
                body.dataset.theme = 'light';
                btn.textContent = '☀️';
                localStorage.setItem('theme', 'light');
            }
            updateChartColors();
        }

        function initTheme() {
            const saved = localStorage.getItem('theme') || 'dark';
            document.body.dataset.theme = saved;
            document.getElementById('theme-toggle').textContent = saved === 'light' ? '☀️' : '🌙';
        }

        function getChartColors() {
            const isDark = document.body.dataset.theme !== 'light';
            return {
                text: isDark ? '#eee' : '#333',
                grid: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                song: '#4ecca3',
                call: '#f9ed69',
                alarm: '#f38181'
            };
        }

        function updateChartColors() {
            const colors = getChartColors();
            if (timeChart) {
                timeChart.options.scales.x.ticks.color = colors.text;
                timeChart.options.scales.y.ticks.color = colors.text;
                timeChart.options.scales.x.grid.color = colors.grid;
                timeChart.options.scales.y.grid.color = colors.grid;
                timeChart.update();
            }
            if (speciesChart) {
                speciesChart.options.scales.x.ticks.color = colors.text;
                speciesChart.options.scales.y.ticks.color = colors.text;
                speciesChart.options.scales.x.grid.color = colors.grid;
                speciesChart.options.scales.y.grid.color = colors.grid;
                speciesChart.update();
            }
            if (hourlyChart) {
                hourlyChart.options.scales.x.ticks.color = colors.text;
                hourlyChart.options.scales.y.ticks.color = colors.text;
                hourlyChart.options.scales.x.grid.color = colors.grid;
                hourlyChart.options.scales.y.grid.color = colors.grid;
                hourlyChart.options.plugins.legend.labels.color = colors.text;
                hourlyChart.update();
            }
        }

        // Update check
        async function checkUpdate() {
            const dot = document.getElementById('update-dot');
            const btn = document.getElementById('update-btn');
            const versionInfo = document.getElementById('version-info');

            dot.className = 'update-dot checking';
            try {
                const res = await fetch('/api/update/check');
                const data = await res.json();
                updateInfo = data;
                versionInfo.textContent = 'v' + data.local_commit.substring(0, 7);
                if (data.update_available) {
                    dot.className = 'update-dot available';
                    dot.title = 'Update available!';
                    btn.classList.add('visible');
                } else {
                    dot.className = 'update-dot';
                    dot.style.background = '#4ecca3';
                    dot.title = 'Up to date';
                    btn.classList.remove('visible');
                }
            } catch (e) {
                dot.className = 'update-dot';
                dot.style.background = '#f38181';
                dot.title = 'Could not check for updates';
            }
        }

        function showUpdateModal() {
            if (!updateInfo) return;
            document.getElementById('update-message').textContent =
                `New version available: ${updateInfo.remote_commit.substring(0, 7)}`;
            document.getElementById('update-details').textContent =
                updateInfo.commit_message || 'No commit message';
            document.getElementById('update-modal').classList.add('visible');
        }

        function hideUpdateModal() {
            document.getElementById('update-modal').classList.remove('visible');
        }

        async function applyUpdate() {
            const btn = document.getElementById('apply-update-btn');
            const details = document.getElementById('update-details');
            btn.disabled = true;
            btn.textContent = 'Updating...';
            details.textContent = 'Pulling latest changes...';
            try {
                const res = await fetch('/api/update/apply', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    details.textContent = data.output + '\\n\\nReloading...';
                    setTimeout(() => window.location.reload(), 3000);
                } else {
                    details.textContent = 'Failed: ' + data.error;
                    btn.disabled = false;
                    btn.textContent = 'Retry';
                }
            } catch (e) {
                details.textContent = 'Error: ' + e.message;
                btn.disabled = false;
                btn.textContent = 'Retry';
            }
        }

        // Stats and coverage
        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const stats = await res.json();
                const coverage = stats.coverage || { covered: 0, total: 0, percent: 0 };
                document.getElementById('stats').innerHTML = `
                    <div class="stat-card"><h3>${stats.total}</h3><p>Total</p></div>
                    <div class="stat-card"><h3>${stats.song || 0}</h3><p>Songs</p></div>
                    <div class="stat-card"><h3>${stats.call || 0}</h3><p>Calls</p></div>
                    <div class="stat-card"><h3>${stats.alarm || 0}</h3><p>Alarms</p></div>
                    <div class="stat-card coverage"><h3>${coverage.covered}/${coverage.total} (${coverage.percent}%)</h3><p>Model Coverage</p></div>
                `;
            } catch (e) {
                console.error('Stats error:', e);
            }
        }

        // Charts
        async function loadCharts() {
            try {
                const res = await fetch('/api/charts');
                const data = await res.json();
                const colors = getChartColors();

                // Time chart
                const timeCtx = document.getElementById('timeChart').getContext('2d');
                if (timeChart) timeChart.destroy();
                timeChart = new Chart(timeCtx, {
                    type: 'bar',
                    data: {
                        labels: data.daily.labels,
                        datasets: [
                            { label: 'Song', data: data.daily.song, backgroundColor: colors.song },
                            { label: 'Call', data: data.daily.call, backgroundColor: colors.call },
                            { label: 'Alarm', data: data.daily.alarm, backgroundColor: colors.alarm }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { labels: { color: colors.text } } },
                        scales: {
                            x: { stacked: true, ticks: { color: colors.text }, grid: { color: colors.grid } },
                            y: { stacked: true, ticks: { color: colors.text }, grid: { color: colors.grid } }
                        }
                    }
                });

                // Species chart
                const speciesCtx = document.getElementById('speciesChart').getContext('2d');
                if (speciesChart) speciesChart.destroy();
                speciesChart = new Chart(speciesCtx, {
                    type: 'bar',
                    data: {
                        labels: data.top_species.labels,
                        datasets: [{
                            label: 'Count',
                            data: data.top_species.values,
                            backgroundColor: colors.song
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { ticks: { color: colors.text }, grid: { color: colors.grid } },
                            y: { ticks: { color: colors.text }, grid: { display: false } }
                        }
                    }
                });
            } catch (e) { console.error('Charts error:', e); }
        }

        // Data table
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
                    tbody.innerHTML = '<tr><td colspan="6" class="empty">No vocalizations yet. Waiting for BirdNET-Pi detections...</td></tr>';
                    return;
                }

                tbody.innerHTML = data.map(row => `
                    <tr class="clickable">
                        <td>${new Date(row.classified_at).toLocaleString()}</td>
                        <td>${row.common_name}</td>
                        <td class="type-${row.vocalization_type}">${(row.vocalization_type_display || row.vocalization_type).toUpperCase()}</td>
                        <td><span class="confidence">${Math.round(row.confidence * 100)}%</span></td>
                        <td><button class="play-btn" onclick="playAudio('${row.file_name}', '${row.common_name}')" ${row.file_name ? '' : 'disabled'}>▶ Play</button></td>
                        <td class="feedback-btns" id="feedback-${row.id}">
                            <button class="feedback-btn" onclick="sendFeedback(${row.id}, true, this)" title="Correct">👍</button>
                            <button class="feedback-btn" onclick="sendFeedback(${row.id}, false, this)" title="Incorrect">👎</button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) {
                document.getElementById('results').innerHTML = '<tr><td colspan="6" class="empty">Error loading data</td></tr>';
            }
        }

        // Feedback
        async function sendFeedback(id, correct, btn) {
            try {
                const res = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: id, correct: correct })
                });
                const data = await res.json();
                if (data.success) {
                    // Update button appearance
                    const container = document.getElementById('feedback-' + id);
                    const btns = container.querySelectorAll('.feedback-btn');
                    btns.forEach(b => {
                        b.classList.remove('selected', 'faded');
                        if (b === btn) {
                            b.classList.add('selected');
                            b.classList.add(correct ? 'correct' : 'incorrect');
                        } else {
                            b.classList.add('faded');
                        }
                    });
                }
            } catch (e) {
                console.error('Feedback error:', e);
            }
        }

        // Audio player
        function playAudio(filename, species) {
            if (!filename) return;
            const player = document.getElementById('audio-player');
            const audio = document.getElementById('audio-element');
            const speciesName = document.getElementById('player-species');

            audio.src = '/api/audio?file=' + encodeURIComponent(filename);
            speciesName.textContent = species;
            player.classList.add('visible');
            audio.play().catch(e => console.log('Playback error:', e));
        }

        function closePlayer() {
            const player = document.getElementById('audio-player');
            const audio = document.getElementById('audio-element');
            audio.pause();
            player.classList.remove('visible');
        }

        // Initialize after page load
        function init() {
            if (initialized) return;
            initialized = true;

            try {
                // Event listeners
                document.getElementById('filter-type').addEventListener('change', loadData);
                document.getElementById('filter-species').addEventListener('input', loadData);

                initTheme();
                checkUpdate();
                loadStats();
                loadData();

                // Chart.js loads asynchronously after init
                // Charts will be loaded when Chart.js script completes

                // Periodic refresh
                setInterval(loadData, 30000);
                setInterval(loadStats, 60000);
                setInterval(checkUpdate, 300000);
            } catch (e) {
                console.error('Init error:', e);
            }
        }

        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', init);
        if (document.readyState !== 'loading') init();
    </script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script>
        if (typeof Chart !== 'undefined' && typeof loadCharts === 'function') {
            loadCharts();
            setInterval(loadCharts, 60000);
        }
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(html))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        # Headers for Edge Local Network Access compatibility
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(html.encode())

    def check_update(self):
        """Check if an update is available."""
        try:
            # Get local commit
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=INSTALL_DIR
            )
            local_commit = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Get remote commit from GitHub API
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"User-Agent": "BirdNET-Vocalization-Updater"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                remote_commit = data.get("sha", "")
                commit_message = data.get("commit", {}).get("message", "")

            update_available = local_commit != remote_commit and remote_commit != ""

            self.send_json({
                "update_available": update_available,
                "local_commit": local_commit,
                "remote_commit": remote_commit,
                "commit_message": commit_message.split("\n")[0]  # First line only
            })
        except Exception as e:
            self.send_json({
                "update_available": False,
                "local_commit": "unknown",
                "remote_commit": "unknown",
                "error": str(e)
            })

    def apply_update(self):
        """Apply the update by pulling from git and restarting services."""
        try:
            # Pull latest changes (explicitly specify origin/master to avoid tracking issues)
            result = subprocess.run(
                ["git", "pull", "origin", "master"],
                capture_output=True,
                text=True,
                cwd=INSTALL_DIR
            )

            if result.returncode != 0:
                self.send_json({
                    "success": False,
                    "error": result.stderr
                })
                return

            output = result.stdout

            # Send success response FIRST, before restarting
            self.send_json({
                "success": True,
                "output": output
            })

            # Restart services in background with delay so response can be sent
            # Using nohup and sleep to ensure this process completes even after we return
            subprocess.Popen(
                ["bash", "-c", "sleep 2 && sudo systemctl restart birdnet-vocalization && sudo systemctl restart birdnet-vocalization-viewer"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e)
            })

    def save_feedback(self):
        """Save user feedback on classification accuracy."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            vocalization_id = data.get('id')
            is_correct = data.get('correct')  # True = 👍, False = 👎
            correct_type = data.get('correct_type')  # Optional: what it should have been

            if vocalization_id is None or is_correct is None:
                self.send_json({"success": False, "error": "Missing required fields"})
                return

            db_path = self.data_dir / "vocalization.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create feedback table if it doesn't exist
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

            cursor.execute("""
                INSERT INTO feedback (vocalization_id, is_correct, correct_type)
                VALUES (?, ?, ?)
            """, (vocalization_id, is_correct, correct_type))

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
        """Send statistics as JSON including model coverage."""
        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json({"total": 0, "coverage": {"covered": 0, "total": 0, "percent": 0}})
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

        # Get unique species from vocalizations
        cursor.execute("SELECT COUNT(DISTINCT common_name) FROM vocalizations")
        species_with_models = cursor.fetchone()[0]
        conn.close()

        # Count available models
        model_count = 0
        if self.models_dir and self.models_dir.exists():
            model_count = len(list(self.models_dir.glob("*.pt")))

        # Calculate coverage (species classified vs models available)
        coverage = {
            "covered": species_with_models,
            "total": model_count,
            "percent": round(species_with_models / model_count * 100) if model_count > 0 else 0
        }

        self.send_json({"total": total, "coverage": coverage, **by_type})

    def send_charts(self):
        """Send chart data for visualizations."""
        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json({
                "daily": {"labels": [], "song": [], "call": [], "alarm": []},
                "top_species": {"labels": [], "values": []}
            })
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Daily counts for last 7 days
        cursor.execute("""
            SELECT date(classified_at) as day, vocalization_type, COUNT(*) as count
            FROM vocalizations
            WHERE classified_at >= date('now', '-7 days')
            GROUP BY day, vocalization_type
            ORDER BY day
        """)
        daily_data = {}
        for row in cursor.fetchall():
            day, vtype, count = row
            if day not in daily_data:
                daily_data[day] = {"song": 0, "call": 0, "alarm": 0}
            daily_data[day][vtype] = count

        # Fill in missing days
        from datetime import datetime, timedelta
        labels = []
        song_data = []
        call_data = []
        alarm_data = []
        for i in range(6, -1, -1):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            labels.append(day[-5:])  # MM-DD format
            data = daily_data.get(day, {"song": 0, "call": 0, "alarm": 0})
            song_data.append(data["song"])
            call_data.append(data["call"])
            alarm_data.append(data["alarm"])

        # Top 10 species
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
            "daily": {
                "labels": labels,
                "song": song_data,
                "call": call_data,
                "alarm": alarm_data
            },
            "top_species": {
                "labels": [row[0] for row in top_species],
                "values": [row[1] for row in top_species]
            }
        })

    def send_behavior_insights(self, query_string):
        """Send behavior insights data for species analysis."""
        params = parse_qs(query_string)
        species_filter = params.get("species", [None])[0]

        db_path = self.data_dir / "vocalization.db"
        if not db_path.exists():
            self.send_json({
                "species_breakdown": [],
                "hourly_patterns": [],
                "alerts": [],
                "trends": []
            })
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Species breakdown: % song/call/alarm per species (last 30 days)
        cursor.execute("""
            SELECT common_name, vocalization_type, COUNT(*) as count
            FROM vocalizations
            WHERE classified_at >= date('now', '-30 days')
            GROUP BY common_name, vocalization_type
            ORDER BY common_name
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
                    "species": name,
                    "total": total,
                    "song_pct": round(data["song"] / total * 100),
                    "call_pct": round(data["call"] / total * 100),
                    "alarm_pct": round(data["alarm"] / total * 100)
                })

        # 2. Hourly patterns (when are birds most active?)
        cursor.execute("""
            SELECT strftime('%H', classified_at) as hour, vocalization_type, COUNT(*) as count
            FROM vocalizations
            WHERE classified_at >= date('now', '-7 days')
            GROUP BY hour, vocalization_type
            ORDER BY hour
        """)
        hourly_data = {str(h).zfill(2): {"song": 0, "call": 0, "alarm": 0} for h in range(24)}
        for row in cursor.fetchall():
            hour, vtype, count = row
            if hour in hourly_data:
                hourly_data[hour][vtype] = count

        hourly_patterns = {
            "labels": [f"{h}:00" for h in range(24)],
            "song": [hourly_data[str(h).zfill(2)]["song"] for h in range(24)],
            "call": [hourly_data[str(h).zfill(2)]["call"] for h in range(24)],
            "alarm": [hourly_data[str(h).zfill(2)]["alarm"] for h in range(24)]
        }

        # 3. Anomaly detection: unusual alarm activity
        alerts = []

        # Check for alarm spikes in last 24h vs previous week average
        cursor.execute("""
            SELECT common_name, COUNT(*) as recent_count
            FROM vocalizations
            WHERE vocalization_type = 'alarm'
            AND classified_at >= datetime('now', '-24 hours')
            GROUP BY common_name
        """)
        recent_alarms = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT common_name, COUNT(*) * 1.0 / 7 as avg_daily
            FROM vocalizations
            WHERE vocalization_type = 'alarm'
            AND classified_at >= date('now', '-8 days')
            AND classified_at < date('now', '-1 days')
            GROUP BY common_name
        """)
        avg_alarms = {row[0]: row[1] for row in cursor.fetchall()}

        for species, count in recent_alarms.items():
            avg = avg_alarms.get(species, 0)
            if avg > 0 and count > avg * 3:  # 3x more than usual
                increase_pct = round((count - avg) / avg * 100)
                alerts.append({
                    "type": "alarm_spike",
                    "species": species,
                    "message": f"{species}: {count} alarm calls in 24h (+{increase_pct}% vs normal)",
                    "severity": "warning" if count > avg * 5 else "info"
                })

        # Check for unusual silence (species normally active but not heard)
        cursor.execute("""
            SELECT common_name, COUNT(*) as count
            FROM vocalizations
            WHERE classified_at >= date('now', '-8 days')
            AND classified_at < date('now', '-1 days')
            GROUP BY common_name
            HAVING count >= 7
        """)
        normally_active = {row[0]: row[1] / 7 for row in cursor.fetchall()}

        cursor.execute("""
            SELECT common_name, COUNT(*) as count
            FROM vocalizations
            WHERE classified_at >= date('now', '-1 days')
            GROUP BY common_name
        """)
        today_active = {row[0]: row[1] for row in cursor.fetchall()}

        for species, avg in normally_active.items():
            today = today_active.get(species, 0)
            if avg >= 3 and today == 0:  # Usually 3+/day, but 0 today
                alerts.append({
                    "type": "silence",
                    "species": species,
                    "message": f"{species}: No detections today (usually ~{round(avg)}/day)",
                    "severity": "info"
                })

        # 4. Trends: weekly comparison
        cursor.execute("""
            SELECT vocalization_type, COUNT(*) as count
            FROM vocalizations
            WHERE classified_at >= date('now', '-7 days')
            GROUP BY vocalization_type
        """)
        this_week = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT vocalization_type, COUNT(*) as count
            FROM vocalizations
            WHERE classified_at >= date('now', '-14 days')
            AND classified_at < date('now', '-7 days')
            GROUP BY vocalization_type
        """)
        last_week = {row[0]: row[1] for row in cursor.fetchall()}

        trends = []
        for vtype in ["song", "call", "alarm"]:
            this_count = this_week.get(vtype, 0)
            last_count = last_week.get(vtype, 0)
            if last_count > 0:
                change = round((this_count - last_count) / last_count * 100)
                trends.append({
                    "type": vtype,
                    "this_week": this_count,
                    "last_week": last_count,
                    "change_pct": change
                })
            else:
                trends.append({
                    "type": vtype,
                    "this_week": this_count,
                    "last_week": 0,
                    "change_pct": 0
                })

        conn.close()

        self.send_json({
            "species_breakdown": species_breakdown,
            "hourly_patterns": hourly_patterns,
            "alerts": alerts,
            "trends": trends
        })

    def send_audio(self, query_string):
        """Send audio file from BirdNET-Pi extracted folder."""
        params = parse_qs(query_string)
        filename = params.get("file", [None])[0]

        if not filename or not self.birdnet_dir:
            self.send_error(404, "File not found")
            return

        # Security: prevent path traversal
        if ".." in filename or filename.startswith("/"):
            self.send_error(403, "Forbidden")
            return

        # Search for the file in BirdNET-Pi extracted folder
        extracted_dir = self.birdnet_dir / "extracted" / "By_Date"
        audio_path = None

        # Try direct path first
        direct_path = self.birdnet_dir / filename
        if direct_path.exists():
            audio_path = direct_path
        else:
            # Search in extracted directory
            for f in extracted_dir.rglob(filename):
                audio_path = f
                break

        if not audio_path or not audio_path.exists():
            self.send_error(404, "Audio file not found")
            return

        # Determine content type
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
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run on")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="Data directory")
    parser.add_argument("--birdnet-dir", type=Path, default=Path("/home/pi/BirdNET-Pi"),
                        help="BirdNET-Pi installation directory (for audio playback)")
    parser.add_argument("--models-dir", type=Path, default=INSTALL_DIR / "models",
                        help="Models directory (for coverage stats)")
    args = parser.parse_args()

    VocalizationHandler.data_dir = args.data_dir
    VocalizationHandler.birdnet_dir = args.birdnet_dir
    VocalizationHandler.models_dir = args.models_dir

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
