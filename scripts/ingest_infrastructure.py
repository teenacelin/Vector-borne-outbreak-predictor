import os
import sqlite3
import random

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'vector_predictor.db')

def seed_infrastructure():
    print("Connecting to DB...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT location_id, state_name FROM locations")
    locations = cursor.fetchall()
    
    print(f"Generating proxy infrastructure data for {len(locations)} municipalities...")
    
    # Regions
    north = ['Acre', 'Amapá', 'Amazonas', 'Pará', 'Rondônia', 'Roraima', 'Tocantins']
    northeast = ['Alagoas', 'Bahia', 'Ceará', 'Maranhão', 'Paraíba', 'Pernambuco', 'Piauí', 'Rio Grande do Norte', 'Sergipe']
    center_west = ['Goiás', 'Mato Grosso', 'Mato Grosso do Sul', 'Distrito Federal']
    southeast = ['Espírito Santo', 'Minas Gerais', 'Rio de Janeiro', 'São Paulo']
    south = ['Paraná', 'Rio Grande do Sul', 'Santa Catarina']
    
    records = []
    
    for loc_id, state in locations:
        # Defaults
        base_pop = random.randint(5000, 50000)
        base_density = random.uniform(10.0, 100.0)
        base_sanitation = random.uniform(0.4, 0.7)
        
        # State-specific logic for realistic proxy
        if state in north:
            # Low density, lower sanitation, isolated communities (high vector risk)
            pop = random.randint(2000, 100000)
            density = random.uniform(1.0, 20.0)
            sanitation = random.uniform(0.2, 0.5)
        elif state in southeast:
            # High density, high sanitation
            pop = random.randint(20000, 2000000)
            density = random.uniform(100.0, 5000.0)
            sanitation = random.uniform(0.7, 0.95)
        elif state in south:
            pop = random.randint(10000, 500000)
            density = random.uniform(50.0, 500.0)
            sanitation = random.uniform(0.65, 0.9)
        elif state in northeast:
            pop = random.randint(10000, 300000)
            density = random.uniform(20.0, 150.0)
            sanitation = random.uniform(0.3, 0.6)
        else:
            pop = base_pop
            density = base_density
            sanitation = base_sanitation
            
        # Add random noise
        sanitation = max(0.1, min(0.99, sanitation + random.uniform(-0.05, 0.05)))
        
        records.append((loc_id, pop, density, sanitation))
    
    # Insert or replace
    cursor.executemany('''
        INSERT OR REPLACE INTO infrastructure (location_id, population, urban_density, sanitation_index)
        VALUES (?, ?, ?, ?)
    ''', records)
    
    conn.commit()
    conn.close()
    print("Infrastructure data successfully seeded!")

if __name__ == '__main__':
    seed_infrastructure()
