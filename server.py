import http.server
import socketserver
import json
import sqlite3
import os

PORT = 8000
DB_FILE = os.path.join(os.path.dirname(__file__), 'data', 'cleaned', 'vector_predictor.db')
METRICS_FILE = os.path.join(os.path.dirname(__file__), 'public', 'metrics.json')

class DashboardAPIHandler(http.server.SimpleHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Suppress noisy per-request logs, only show errors
        pass
    
    def do_GET(self):
        # Redirect root to the dashboard
        if self.path == '/' or self.path == '/index.html':
            self.send_response(301)
            self.send_header('Location', '/public/index.html')
            self.end_headers()
            return
            
        # API endpoint
        if self.path == '/api/get_dashboard_data.php':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Load real model metrics
            try:
                with open(METRICS_FILE, 'r') as f:
                    perf = json.load(f)
            except Exception:
                perf = {'precision': 0, 'recall': 0, 'f1_score': 0, 'pr_auc': 0}
            
            response_data = {
                'overview': {'trackedMunicipalities': 0, 'highRiskMunicipalities': 0},
                'map_data': [],
                'municipality_stats': {'hotspots': [], 'actions': []},
                'climate_disease_trends': [],
                'seasonal_risk': [],
                'model_performance': perf
            }
            
            try:
                conn = sqlite3.connect(DB_FILE)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Overview KPIs
                cursor.execute("SELECT COUNT(*) as cnt FROM locations")
                response_data['overview']['trackedMunicipalities'] = cursor.fetchone()['cnt']
                
                cursor.execute("SELECT COUNT(*) as cnt FROM predictions WHERE risk_level IN ('HIGH', 'VERY HIGH')")
                response_data['overview']['highRiskMunicipalities'] = cursor.fetchone()['cnt']

                # 2. Map Data — use state_name since state_code is NULL
                cursor.execute("""
                    SELECT l.location_id, l.municipality, l.state_name, l.latitude, l.longitude, 
                           p.risk_probability, p.risk_level
                    FROM locations l
                    JOIN predictions p ON l.location_id = p.location_id
                """)
                response_data['map_data'] = [dict(row) for row in cursor.fetchall()]

                # 3. Hotspots — top 10 municipalities by most recent case volume
                cursor.execute("""
                    SELECT l.municipality, l.state_name, f.dengue_rolling_4 as cases, 
                           f.rainfall_anomaly, f.temperature_anomaly
                    FROM locations l
                    JOIN features f ON l.location_id = f.location_id
                    WHERE f.date = (SELECT MAX(date) FROM features)
                    ORDER BY f.dengue_rolling_4 DESC
                    LIMIT 10
                """)
                response_data['municipality_stats']['hotspots'] = [dict(row) for row in cursor.fetchall()]
                
                # 3b. Actions — top 10 highest risk predictions
                cursor.execute("""
                    SELECT l.municipality, l.state_name, p.risk_level, p.risk_probability 
                    FROM locations l
                    JOIN predictions p ON l.location_id = p.location_id
                    ORDER BY p.risk_probability DESC
                    LIMIT 10
                """)
                response_data['municipality_stats']['actions'] = [dict(row) for row in cursor.fetchall()]

                # 4. Climate & Disease Trends — aggregated by date
                cursor.execute("""
                    SELECT date, 
                           AVG(temperature_1) as avg_temp, 
                           AVG(rainfall_1) as avg_rain, 
                           SUM(dengue_rolling_4) as total_cases
                    FROM features
                    GROUP BY date
                    ORDER BY date ASC
                """)
                response_data['climate_disease_trends'] = [dict(row) for row in cursor.fetchall()]
                
                # 5. Seasonal Risk — real malaria cases by month
                cursor.execute("""
                    SELECT month, SUM(cases) as total_cases
                    FROM malaria_cases
                    GROUP BY month
                    ORDER BY month ASC
                """)
                response_data['seasonal_risk'] = [dict(row) for row in cursor.fetchall()]

                conn.close()
                
            except Exception as e:
                response_data['error'] = str(e)
                
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        return super().do_GET()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DashboardAPIHandler) as httpd:
        print(f"=== VectorPredict Server ===")
        print(f"Dashboard: http://localhost:{PORT}")
        print(f"API:       http://localhost:{PORT}/api/get_dashboard_data.php")
        print(f"Press Ctrl+C to stop.")
        httpd.serve_forever()
