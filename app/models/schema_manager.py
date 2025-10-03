# app/models/schema_manager.py
from sqlalchemy import inspect, text
import pandas as pd
from app.utils.config import settings

class SchemaManager:
    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)
        self._refresh_schema()
    
    def _refresh_schema(self):
        """Extract and cache database schema"""
        self.tables = self.inspector.get_table_names()
        self.schema = {}
        
        for table in self.tables:
            columns = self.inspector.get_columns(table)
            
            self.schema[table] = {
                'columns': {col['name']: str(col['type']) for col in columns},
                'sample_data': self._get_sample_data(table, limit=3)
            }
    
    def _get_sample_data(self, table_name: str, limit: int = 3):
        """Get sample data for better context"""
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql_query(
                    text(f"SELECT * FROM {table_name} LIMIT {limit}"), 
                    conn
                )
                return result.to_dict('records')
        except Exception as e:
            print(f"Could not get sample data for {table_name}: {e}")
            return []
    
    def get_schema_context(self):
        """Generate comprehensive schema context for LLM"""
        context = "Database Schema:\n\n"
        
        for table, info in self.schema.items():
            context += f"📊 Table: {table}\n"
            context += "   Columns:\n"
            for col_name, col_type in info['columns'].items():
                context += f"     - {col_name} ({col_type})\n"
            
            if info['sample_data']:
                context += "   Sample Data:\n"
                for i, sample in enumerate(info['sample_data']):
                    context += f"     {i+1}. {sample}\n"
            
            context += "\n"
        
        return context
    
    def get_available_tables(self):
        return self.tables