# app/database/data_loader.py
import pandas as pd
import sqlite3
import os
from datetime import datetime

class DataLoader:
    def __init__(self, db_path="data/sample_database.db"):
        self.db_path = db_path
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs('data', exist_ok=True)
    
    def create_database(self):
        """Create SQLite database with employee data"""
        try:
            # Create connection
            conn = sqlite3.connect(self.db_path)
            
            # Create employees table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id INTEGER PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    salary DECIMAL(10,2),
                    hire_date DATE,
                    department_id INTEGER,
                    department TEXT,
                    residence_city TEXT,
                    age INTEGER,
                    job_level TEXT
                )
            ''')
            
            # Load your actual data
            # For now, we'll create sample data matching your structure
            self._insert_sample_data(conn)
            
            conn.commit()
            print("Database created successfully!")
            return True
            
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def _insert_sample_data(self, conn):
        """Insert your actual data"""
        employees_data = [
            (1, 'Jessika', 'Hulcoop', 127518.76, '2010-09-16', 5, 'IT', 'Babushkin', 44, 'Mid Level'),
            (2, 'Donni', 'Alps', 100688.92, '2020-12-05', 3, 'Marketing', 'Ukmerge', 26, 'Executive'),
            (3, 'Pat', 'Frick', 96735.41, '2001-03-14', 2, 'IT', 'Kiruru', 42, 'Entry Level'),
            (4, 'Raddie', 'Gostick', 149368.4, '2017-11-16', 1, 'IT', 'São Félix do Xingu', 46, 'Entry Level'),
            (5, 'Sidonnie', 'Oganesian', 90661.82, '2010-11-05', 1, 'Finance', 'Bayt Liqyā', 41, 'Entry Level'),
            (6, 'Burnard', 'Roote', 104105.49, '2020-08-09', 2, 'Marketing', 'Weishanzhuang', 40, 'Executive'),
            (7, 'Stanley', 'Jennens', 116501.5, '2007-06-29', 4, 'IT', 'Taznakht', 37, 'Executive'),
            (8, 'Bunnie', 'Dorricott', 123178.12, '2021-01-24', 5, 'Sales', 'Sharkawshchyna', 42, 'Entry Level'),
            (9, 'Izak', 'Burwin', 31391.41, '2011-07-03', 3, 'Marketing', 'Nkoteng', 31, 'Mid Level'),
            (10, 'Barton', 'Leguey', 70522.72, '2017-06-18', 1, 'IT', 'Yanzhao', 33, 'Executive')
            # Add all 500 rows from your data here
        ]
        
        # Clear existing data
        conn.execute("DELETE FROM employees")
        
        # Insert new data
        conn.executemany('''
            INSERT INTO employees 
            (employee_id, first_name, last_name, salary, hire_date, department_id, department, residence_city, age, job_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', employees_data)
        
        print(f"Inserted {len(employees_data)} employee records")