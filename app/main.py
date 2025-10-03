import streamlit as st
import pandas as pd
import time
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseConnection
from app.models.schema_manager import SchemaManager
from app.models.sql_generator import SQLGenerator

class NLToSQLApp:
    def __init__(self):
        self.setup_page()
        self.initialize_system()
    
    def setup_page(self):
        st.set_page_config(
            page_title="NL to SQL Generator - Employee Data",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
            text-align: center;
            margin-bottom: 2rem;
        }
        .success-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .error-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def initialize_system(self):
        """Initialize the NL to SQL system"""
        try:
            with st.spinner("🔄 Initializing database connection..."):
                self.db_connection = DatabaseConnection()
                engine = self.db_connection.get_engine()
                self.schema_manager = SchemaManager(engine)
                self.sql_generator = SQLGenerator(self.schema_manager)
            
            st.sidebar.success("✅ System initialized successfully!")
            
            # Show database info
            st.sidebar.subheader("📊 Database Info")
            tables = self.schema_manager.get_available_tables()
            for table in tables:
                cols = self.schema_manager.schema[table]['columns']
                st.sidebar.write(f"**{table}**: {', '.join(cols.keys())}")
                
        except Exception as e:
            st.error(f"❌ Failed to initialize system: {str(e)}")
            st.stop()
    
    def render_sidebar(self):
        """Render sidebar with examples"""
        st.sidebar.title("💡 Example Queries")
        
        examples = [
            "Show all employees in IT department",
            "What is the average salary by department?",
            "Find the top 5 highest paid employees", 
            "Count employees in each job level",
            "Show employees hired in the last 5 years",
            "What is the salary distribution by age?",
            "List all unique cities where employees live",
            "Find executives earning more than 100,000"
        ]
        
        for example in examples:
            if st.sidebar.button(example, use_container_width=True):
                st.session_state.user_query = example
                st.rerun()
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 Tools")
        
        if st.sidebar.button("Refresh Schema"):
            self.schema_manager._refresh_schema()
            st.sidebar.success("Schema refreshed!")
            st.rerun()
        
        # Render query history
        try:
            self.render_history()
        except Exception as e:
            # Non-fatal: show history errors in sidebar
            st.sidebar.error(f"Could not load query history: {e}")
    
    def render_main(self):
        """Render main application area"""
        st.markdown('<h1 class="main-header">💬 Talk to Your Employee Data</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Ask natural language questions about your employee database</p>', unsafe_allow_html=True)
        
        # Query input
        user_query = st.text_area(
            "**Ask a question about your employee data:**",
            value=st.session_state.get('user_query', ''),
            height=100,
            placeholder="e.g., Show me the average salary by department...",
            key="query_input"
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🚀 Generate & Execute SQL", type="primary", use_container_width=True):
                if user_query.strip():
                    self.process_query(user_query.strip())
                else:
                    st.warning("Please enter a question first!")
        
        with col2:
            if st.button("🔄 Clear Results", use_container_width=True):
                if 'last_result' in st.session_state:
                    del st.session_state.last_result
                st.rerun()
        
        # Display previous results if available
        if 'last_result' in st.session_state:
            self.display_results(st.session_state.last_result)
    
    def process_query(self, user_query: str):
        """Process natural language query"""
        with st.spinner("🤖 Generating SQL query..."):
            start_time = time.time()
            
            # Generate SQL
            sql_query, error = self.sql_generator.generate_sql(user_query)
            
            if error:
                st.error(f"**SQL Generation Error:** {error}")
                return
            
            generation_time = time.time() - start_time
            
            # Execute SQL
            with st.spinner("🔍 Executing query..."):
                execution_start = time.time()
                result, execution_error = self.db_connection.execute_query(sql_query)
                execution_time = time.time() - execution_start
                # Persist to history
                try:
                    history_id = self.db_connection.save_query_history(user_query, sql_query, result, execution_error)
                except Exception:
                    history_id = -1
            
            # Store results
            st.session_state.last_result = {
                'user_query': user_query,
                'sql_query': sql_query,
                'result': result,
                'error': execution_error,
                'generation_time': generation_time,
                'execution_time': execution_time
                , 'history_id': history_id
            }
    
    def display_results(self, results: dict):
        """Display query results"""
        st.markdown("---")
        
        # Display SQL query
        st.subheader("📋 Generated SQL")
        st.code(results['sql_query'], language="sql")
        
        # Performance metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("SQL Generation", f"{results['generation_time']:.2f}s")
        with col2:
            if results['result'] is not None:
                st.metric("Rows Returned", len(results['result']))
        
        # Display results or error
        if results['error']:
            st.error(f"**Execution Error:** {results['error']}")
        else:
            st.subheader("📊 Results")
            st.dataframe(results['result'], use_container_width=True)
            
            # Export options
            if not results['result'].empty:
                csv = results['result'].to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        # (Explain plans removed from UI by user request)

    def render_history(self):
        """Render recent query history in the sidebar with run/explain/favorite controls"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("\u23f2 Recent Queries")

        history = self.db_connection.get_query_history(limit=20)
        if not history:
            st.sidebar.info("No recent queries")
            return

        for h in history:
            hid = h.get('id')
            ts = h.get('timestamp', '')
            uq = h.get('user_query', '')
            fav = True if int(h.get('favorite', 0)) == 1 else False

            cols = st.sidebar.columns([0.5, 5, 1])
            # Run button
            if cols[0].button("▶", key=f"run_{hid}"):
                st.session_state.user_query = uq
                # Immediately process the query
                self.process_query(uq)
                st.rerun()

            # Query summary: prefer natural language user_query, fall back to the generated SQL if empty
            display_text = uq.strip() if uq and uq.strip() else (h.get('sql_query', '') or '')
            # If still empty, try to build a small preview from stored result JSON
            if not display_text:
                try:
                    raw = h.get('result') or ''
                    if raw:
                        import json
                        parsed = json.loads(raw)
                        # parsed is a list of row dicts; show column names or first-row preview
                        if isinstance(parsed, list) and len(parsed) > 0:
                            first = parsed[0]
                            # show up to first 3 columns
                            preview_cols = list(first.keys())[:3]
                            vals = [str(first.get(c)) for c in preview_cols]
                            display_text = f"Preview: {', '.join(f'{c}={v}' for c,v in zip(preview_cols, vals))}"
                        else:
                            display_text = "(result preview)"
                    else:
                        display_text = "(no visible query)"
                except Exception:
                    display_text = "(no visible query)"
            # Truncate for display
            max_len = 120
            if len(display_text) > max_len:
                display_text = display_text[:max_len-3] + '...'
            cols[1].markdown(f"**{display_text}**")

            # Favorite toggle
            star_label = "★" if fav else "☆"
            if cols[2].button(star_label, key=f"fav_{hid}"):
                self.db_connection.toggle_favorite(hid)
                st.experimental_rerun()
    
    def run(self):
        """Main application runner"""
        self.render_sidebar()
        self.render_main()

if __name__ == "__main__":
    if 'user_query' not in st.session_state:
        st.session_state.user_query = ""
    
    app = NLToSQLApp()
    app.run()