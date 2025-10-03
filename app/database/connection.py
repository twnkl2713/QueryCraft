# app/database/connection.py
import sqlite3
import pandas as pd
import json
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from app.utils.config import settings

class DatabaseConnection:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with sample data if needed"""
        try:
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                # Check whether the main table exists; if not, create and populate the DB
                try:
                    inspector = inspect(self.engine)
                    tables = inspector.get_table_names()
                except Exception:
                    # Fallback for drivers where inspector might not work as expected
                    tables = []

                if 'employees' not in tables:
                    from app.database.data_loader import DataLoader
                    loader = DataLoader()
                    loader.create_database()
                # Ensure query history table exists
                try:
                    conn.execute(text('''
                        CREATE TABLE IF NOT EXISTS query_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT,
                            user_query TEXT,
                            sql_query TEXT,
                            result TEXT,
                            error TEXT,
                            favorite INTEGER DEFAULT 0
                        )
                    '''))
                except Exception:
                    # If creating via SQLAlchemy text fails for some dialects, fall back to raw connection
                    pass
        except Exception:
            # Database doesn't exist, create it
            from app.database.data_loader import DataLoader
            loader = DataLoader()
            loader.create_database()
            # After creating DB via sqlite3, also ensure history table exists there
            try:
                conn = sqlite3.connect('data/sample_database.db')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS query_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        user_query TEXT,
                        sql_query TEXT,
                        result TEXT,
                        error TEXT,
                        favorite INTEGER DEFAULT 0
                    )
                ''')
                conn.commit()
            except Exception:
                pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def get_engine(self):
        return self.engine
    
    def execute_query(self, sql_query: str):
        """Execute SQL query and return results"""
        try:
            with self.engine.connect() as conn:
                # Basic detection: SELECT/PRAGMA/EXPLAIN/WITH -> return rows
                sql = sql_query.strip()
                first_word = sql.split()[0].lower() if sql else ''

                if first_word in ('select', 'pragma', 'explain', 'with', 'show'):
                    # Use pandas to get results as DataFrame for queries that return rows
                    result = pd.read_sql_query(sql_query, conn)
                    return result, None
                else:
                    # For DDL/DML statements (INSERT/UPDATE/DELETE/CREATE/etc.) execute and commit
                    trans = conn.begin()
                    try:
                        result = conn.execute(text(sql_query))
                        trans.commit()
                    except Exception as e:
                        trans.rollback()
                        return None, str(e)

                    # Return an empty DataFrame for non-select statements (no rows to display)
                    return pd.DataFrame(), None
        except Exception as e:
            return None, str(e)

    def save_query_history(self, user_query: str, sql_query: str, result_df: pd.DataFrame | None, error: str | None, favorite: bool = False) -> int:
        """Persist a query and its results into the query_history table. Returns the inserted row id."""
        result_text = ''
        try:
            if result_df is not None:
                # store as JSON records to keep it compact and inspectable
                result_text = result_df.to_json(orient='records')
        except Exception:
            result_text = ''

        timestamp = datetime.utcnow().isoformat()
        fav_val = 1 if favorite else 0

        try:
            with self.engine.begin() as conn:
                insert_sql = text(
                    "INSERT INTO query_history (timestamp, user_query, sql_query, result, error, favorite) VALUES (:ts, :uq, :sq, :res, :err, :fav)"
                )
                res = conn.execute(insert_sql, {
                    'ts': timestamp,
                    'uq': user_query,
                    'sq': sql_query,
                    'res': result_text,
                    'err': error or '',
                    'fav': fav_val
                })
                # SQLAlchemy 1.4+ returns inserted_primary_key sometimes; fallback to lastrowid
                try:
                    rowid = res.lastrowid
                except Exception:
                    # Fallback: query the latest id
                    row = conn.execute(text('SELECT last_insert_rowid()')).scalar()
                    rowid = int(row) if row is not None else -1
                return int(rowid)
        except Exception:
            # Best-effort fallback using sqlite3 directly
            try:
                conn = sqlite3.connect('data/sample_database.db')
                cur = conn.cursor()
                cur.execute('''INSERT INTO query_history (timestamp, user_query, sql_query, result, error, favorite) VALUES (?, ?, ?, ?, ?, ?)''',
                            (timestamp, user_query, sql_query, result_text, error or '', fav_val))
                conn.commit()
                rowid = cur.lastrowid
                return int(rowid)
            except Exception:
                return -1
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_query_history(self, limit: int = 20):
        """Return the most recent queries from history as list of dicts. Includes the stored result JSON if present."""
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(
                    text('SELECT id, timestamp, user_query, sql_query, result, error, favorite FROM query_history ORDER BY id DESC LIMIT :lim'),
                    conn,
                    params={'lim': limit}
                )
                return df.to_dict('records')
        except Exception:
            # Fallback to sqlite3
            try:
                conn = sqlite3.connect('data/sample_database.db')
                cur = conn.cursor()
                cur.execute('SELECT id, timestamp, user_query, sql_query, result, error, favorite FROM query_history ORDER BY id DESC LIMIT ?', (limit,))
                rows = cur.fetchall()
                keys = ['id', 'timestamp', 'user_query', 'sql_query', 'result', 'error', 'favorite']
                return [dict(zip(keys, row)) for row in rows]
            except Exception:
                return []
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def toggle_favorite(self, history_id: int) -> bool:
        """Toggle the favorite flag for a history row. Returns the new state (True/False) or False on error."""
        try:
            with self.engine.begin() as conn:
                cur = conn.execute(text('SELECT favorite FROM query_history WHERE id = :id'), {'id': history_id})
                row = cur.fetchone()
                if not row:
                    return False
                new_val = 0 if int(row[0]) == 1 else 1
                conn.execute(text('UPDATE query_history SET favorite = :fav WHERE id = :id'), {'fav': new_val, 'id': history_id})
                return bool(new_val)
        except Exception:
            try:
                conn = sqlite3.connect('data/sample_database.db')
                cur = conn.cursor()
                cur.execute('SELECT favorite FROM query_history WHERE id = ?', (history_id,))
                r = cur.fetchone()
                if not r:
                    return False
                new_val = 0 if int(r[0]) == 1 else 1
                cur.execute('UPDATE query_history SET favorite = ? WHERE id = ?', (new_val, history_id))
                conn.commit()
                return bool(new_val)
            except Exception:
                return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def explain_query(self, sql_query: str):
        """Return an explanation/plan for the given SQL query (best-effort)."""
        try:
            # For SQLite we can use EXPLAIN QUERY PLAN
            if 'sqlite' in settings.DATABASE_URL:
                explain_sql = f'EXPLAIN QUERY PLAN {sql_query}'
                with self.engine.connect() as conn:
                    df = pd.read_sql_query(text(explain_sql), conn)
                    # Return a readable string
                    return df.to_string(index=False)
            else:
                # Generic fallback: run EXPLAIN <sql>
                explain_sql = f'EXPLAIN {sql_query}'
                with self.engine.connect() as conn:
                    df = pd.read_sql_query(text(explain_sql), conn)
                    return df.to_string(index=False)
        except Exception as e:
            return f'Could not generate explain plan: {e}'
    
    def get_table_info(self):
        """Get information about tables in database"""
        try:
            with self.engine.connect() as conn:
                # For SQLite
                if 'sqlite' in settings.DATABASE_URL:
                    tables = pd.read_sql_query(
                        "SELECT name FROM sqlite_master WHERE type='table'", 
                        conn
                    )
                    table_info = {}
                    for table in tables['name']:
                        columns = pd.read_sql_query(
                            f"PRAGMA table_info({table})", 
                            conn
                        )
                        table_info[table] = columns[['name', 'type']].to_dict('records')
                    return table_info
                else:
                    # For other databases
                    inspector = inspect(self.engine)
                    return inspector.get_table_names()
        except Exception as e:
            print(f"Error getting table info: {e}")
            return {}