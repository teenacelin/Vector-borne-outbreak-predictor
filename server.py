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
        if self.path.startswith('/api/get_dashboard_data.php'):
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
            

            from urllib.parse import urlparse, parse_qs
            parsed_path = urlparse(self.path)
            query = parse_qs(parsed_path.query)
            
            state = query.get('state', ['ALL'])[0]
            risk = query.get('risk', ['ALL'])[0]
            start_date = query.get('start_date', [None])[0]
            end_date = query.get('end_date', [None])[0]
            
            where_pred = ["p.prediction_date = (SELECT MAX(prediction_date) FROM predictions)"]
            where_feat = ["f.date = (SELECT MAX(date) FROM features)"]
            where_feat_trend = ["1=1"]
            where_malaria = ["1=1"]
            
            params_pred = []
            params_feat = []
            params_feat_trend = []
            params_malaria = []
            
            if state != 'ALL':
                where_pred.append("l.state_name = ?")
                params_pred.append(state)
                where_feat.append("l.state_name = ?")
                params_feat.append(state)
                where_feat_trend.append("location_id IN (SELECT location_id FROM locations WHERE state_name = ?)")
                params_feat_trend.append(state)
                where_malaria.append("location_id IN (SELECT location_id FROM locations WHERE state_name = ?)")
                params_malaria.append(state)
                
            if risk != 'ALL':
                where_pred.append("p.risk_level = ?")
                params_pred.append(risk)
                
            if start_date:
                where_feat_trend.append("f.date >= ?")
                params_feat_trend.append(start_date)
                
            if end_date:
                where_feat_trend.append("f.date <= ?")
                params_feat_trend.append(end_date)
                
            where_pred_sql = " AND ".join(where_pred)
            where_feat_sql = " AND ".join(where_feat)
            where_feat_trend_sql = " AND ".join(where_feat_trend)
            where_malaria_sql = " AND ".join(where_malaria)

            try:
                conn = sqlite3.connect(DB_FILE)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Overview KPIs
                state_sql = "WHERE state_name = ?" if state != 'ALL' else ""
                state_param = [state] if state != 'ALL' else []
                cursor.execute(f"SELECT COUNT(*) as cnt FROM locations {state_sql}", state_param)
                response_data['overview']['trackedMunicipalities'] = cursor.fetchone()['cnt']
                
                high_risk_cond = ["p.risk_level IN ('HIGH', 'VERY HIGH')", "p.prediction_date = (SELECT MAX(prediction_date) FROM predictions)"]
                high_risk_params = []
                if state != 'ALL':
                    high_risk_cond.append('l.state_name = ?')
                    high_risk_params.append(state)
                high_risk_sql = " AND ".join(high_risk_cond)
                
                cursor.execute(f"SELECT COUNT(*) as cnt FROM predictions p JOIN locations l ON p.location_id = l.location_id WHERE {high_risk_sql}", high_risk_params)
                response_data['overview']['highRiskMunicipalities'] = cursor.fetchone()['cnt']

                # 2. Map Data
                cursor.execute(f"""
                    SELECT l.location_id, l.municipality, l.state_name, l.latitude, l.longitude, l.geometry,
                           p.risk_probability, p.risk_level
                    FROM locations l
                    JOIN predictions p ON l.location_id = p.location_id
                    WHERE {where_pred_sql}
                """, params_pred)
                response_data['map_data'] = [dict(row) for row in cursor.fetchall()]

                # 3. Hotspots
                cursor.execute(f"""
                    SELECT l.municipality, l.state_name, f.malaria_cases_current as cases, 
                           f.rainfall_anomaly, f.temperature_anomaly
                    FROM locations l
                    JOIN features f ON l.location_id = f.location_id
                    WHERE {where_feat_sql}
                    ORDER BY f.malaria_cases_current DESC
                    LIMIT 10
                """, params_feat)
                response_data['municipality_stats']['hotspots'] = [dict(row) for row in cursor.fetchall()]
                
                # 3b. Actions
                cursor.execute(f"""
                    SELECT l.municipality, l.state_name, p.risk_level, p.risk_probability 
                    FROM locations l
                    JOIN predictions p ON l.location_id = p.location_id
                    WHERE {where_pred_sql}
                    ORDER BY p.risk_probability DESC
                    LIMIT 10
                """, params_pred)
                response_data['municipality_stats']['actions'] = [dict(row) for row in cursor.fetchall()]

                # 4. Climate & Disease Trends
                cursor.execute(f"""
                    SELECT date, 
                           AVG(temperature_1) as avg_temp, 
                           AVG(rainfall_1) as avg_rain, 
                           SUM(malaria_cases_current) as total_cases
                    FROM features f
                    WHERE {where_feat_trend_sql}
                    GROUP BY date
                    ORDER BY date ASC
                """, params_feat_trend)
                response_data['climate_disease_trends'] = [dict(row) for row in cursor.fetchall()]
                
                # 5. Seasonal Risk
                cursor.execute(f"""
                    SELECT month, SUM(cases) as total_cases
                    FROM malaria_cases
                    WHERE {where_malaria_sql}
                    GROUP BY month
                    ORDER BY month ASC
                """, params_malaria)
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
