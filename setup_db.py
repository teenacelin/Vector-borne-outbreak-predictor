import sqlite3

def setup():
    conn = sqlite3.connect('data/cleaned/vector_predictor.db')
    cursor = conn.cursor()

    cursor.executescript('''
    DROP TABLE IF EXISTS predictions;
    DROP TABLE IF EXISTS features;
    DROP TABLE IF EXISTS temperature;
    DROP TABLE IF EXISTS precipitation;
    DROP TABLE IF EXISTS malaria_cases;
    DROP TABLE IF EXISTS dengue_cases;
    DROP TABLE IF EXISTS locations;
    DROP TABLE IF EXISTS gadm_locations;

    CREATE TABLE locations (
        location_id INTEGER PRIMARY KEY AUTOINCREMENT,
        country VARCHAR(100),
        state_code VARCHAR(10),
        state_name VARCHAR(100),
        municipality VARCHAR(150),
        ibge_code VARCHAR(20),
        latitude DECIMAL(10,8),
        longitude DECIMAL(11,8),
        geometry TEXT
    );

    CREATE TABLE dengue_cases (
        dengue_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER,
        report_date DATE,
        year INTEGER,
        month INTEGER,
        week INTEGER,
        cases INTEGER,
        source VARCHAR(150),
        source_url TEXT,
        FOREIGN KEY (location_id) REFERENCES locations(location_id)
    );

    CREATE TABLE malaria_cases (
        malaria_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER,
        notification_date DATE,
        year INTEGER,
        month INTEGER,
        week INTEGER,
        cases INTEGER,
        laboratory_result VARCHAR(50),
        source VARCHAR(150),
        source_url TEXT,
        FOREIGN KEY (location_id) REFERENCES locations(location_id)
    );

    CREATE TABLE precipitation (
        precipitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER,
        observation_date DATE,
        year INTEGER,
        month INTEGER,
        week INTEGER,
        rainfall_mm DECIMAL(8,2),
        source VARCHAR(150),
        FOREIGN KEY (location_id) REFERENCES locations(location_id)
    );

    CREATE TABLE IF NOT EXISTS temperature (
        temperature_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER,
        observation_date DATE,
        year INTEGER,
        month INTEGER,
        week INTEGER,
        temperature_c DECIMAL(5,2),
        source VARCHAR(150),
        FOREIGN KEY (location_id) REFERENCES locations(location_id)
    );

    CREATE TABLE IF NOT EXISTS infrastructure (
        location_id INTEGER PRIMARY KEY,
        population INTEGER,
        urban_density REAL,
        sanitation_index REAL,
        FOREIGN KEY (location_id) REFERENCES locations(location_id)
    );

    CREATE TABLE features (
        feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER,
        date DATE,
        dengue_lag_1 INTEGER,
        dengue_lag_2 INTEGER,
        dengue_lag_4 INTEGER,
        dengue_rolling_4 INTEGER,
        malaria_lag_1 INTEGER,
        malaria_lag_4 INTEGER,
        rainfall_1 DECIMAL(8,2),
        rainfall_2 DECIMAL(8,2),
        rainfall_4 DECIMAL(8,2),
        rainfall_8 DECIMAL(8,2),
        temperature_1 DECIMAL(5,2),
        temperature_2 DECIMAL(5,2),
        temperature_4 DECIMAL(5,2),
        rainfall_anomaly DECIMAL(8,2),
        temperature_anomaly DECIMAL(5,2),
        population INTEGER,
        urban_density REAL,
        sanitation_index REAL,
        outbreak_target INTEGER,
        FOREIGN KEY (location_id) REFERENCES locations(location_id)
    );

    CREATE TABLE predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER,
        prediction_date DATE,
        target_date DATE,
        disease VARCHAR(50),
        risk_probability DECIMAL(5,4),
        risk_level VARCHAR(20),
        model_version VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (location_id) REFERENCES locations(location_id)
    );
    ''')

    conn.commit()
    conn.close()
    print("SQLite database 'data/cleaned/vector_predictor.db' created successfully with the expanded schema.")

if __name__ == '__main__':
    setup()
