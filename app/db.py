import os
import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "churn_dashboard.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(ml_engine=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            tenure INTEGER NOT NULL,
            monthly_charges REAL NOT NULL,
            contract TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            internet_service TEXT NOT NULL,
            num_services INTEGER NOT NULL,
            support_calls INTEGER NOT NULL,
            churn_status TEXT DEFAULT 'No',
            churn_probability REAL DEFAULT 0.0,
            risk_level TEXT DEFAULT 'Low',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Create predictions history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            tenure INTEGER NOT NULL,
            monthly_charges REAL NOT NULL,
            contract TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            internet_service TEXT NOT NULL,
            num_services INTEGER NOT NULL,
            support_calls INTEGER NOT NULL,
            prediction_result TEXT NOT NULL,
            churn_probability REAL NOT NULL,
            risk_level TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Seed default admin user if not exists
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        admin_pass = generate_password_hash("admin123")
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', admin_pass))
        print("Default admin user created: admin / admin123")
        
    # Seed sample customer data if customers table is empty
    cursor.execute('SELECT COUNT(*) as count FROM customers')
    row_count = cursor.fetchone()['count']
    
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset", "churn_dataset.csv")
    if row_count == 0 and os.path.exists(csv_path):
        print("Seeding initial customers table from CSV dataset...")
        df = pd.read_csv(csv_path)
        
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
        
        customers_to_insert = []
        for idx, row in df.iterrows():
            fname = first_names[idx % len(first_names)]
            lname = last_names[(idx * 7) % len(last_names)]
            full_name = f"{fname} {lname}"
            email = f"{fname.lower()}.{lname.lower()}{idx}@example.com"
            
            # Predict churn using ML engine if provided, else use csv label
            if ml_engine:
                pred_dict = ml_engine.predict_one({
                    'Age': int(row['Age']),
                    'Gender': str(row['Gender']),
                    'Tenure': int(row['Tenure']),
                    'MonthlyCharges': float(row['MonthlyCharges']),
                    'Contract': str(row['Contract']),
                    'PaymentMethod': str(row['PaymentMethod']),
                    'InternetService': str(row['InternetService']),
                    'NumberOfServices': int(row['NumberOfServices']),
                    'SupportCalls': int(row['SupportCalls'])
                })
                churn_status = pred_dict['prediction']
                churn_prob = pred_dict['probability']
                risk_level = pred_dict['risk_level']
            else:
                churn_status = str(row['Churn'])
                churn_prob = 75.0 if churn_status == 'Yes' else 15.0
                risk_level = 'High' if churn_prob >= 65 else ('Medium' if churn_prob >= 35 else 'Low')
                
            customers_to_insert.append((
                str(row['CustomerID']),
                full_name,
                email,
                str(row['Gender']),
                int(row['Age']),
                int(row['Tenure']),
                float(row['MonthlyCharges']),
                str(row['Contract']),
                str(row['PaymentMethod']),
                str(row['InternetService']),
                int(row['NumberOfServices']),
                int(row['SupportCalls']),
                churn_status,
                churn_prob,
                risk_level
            ))
            
        cursor.executemany('''
            INSERT INTO customers (
                customer_id, name, email, gender, age, tenure, monthly_charges,
                contract, payment_method, internet_service, num_services, support_calls,
                churn_status, churn_probability, risk_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', customers_to_insert)
        
        print(f"Successfully seeded {len(customers_to_insert)} customers.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
