<<<<<<< HEAD
# QueryCraft
=======
NL-to-SQL Generator
===================

A small Streamlit app that converts natural-language questions about an employee dataset into SQL, executes the SQL against a local SQLite database, and shows the results with a friendly UI. It includes a schema manager, a model-backed SQL generator (with a rule-based fallback), query history with favorites, and CSV export of query results.

Quick features
--------------
- Natural language -> SQL generation (LLM prompt + rule-based fallback)
- Schema introspection (table/column context used in prompts)
- Query execution against a local SQLite DB (auto-created from sample data)
- Query history persisted to `data/sample_database.db` (table: `query_history`)
- Favorite queries (star) and run-once replay (▶)
- Download results as CSV

Requirements
------------
- Python 3.10+ (3.11 recommended)
- Windows PowerShell (instructions below assume PowerShell)

Install dependencies
--------------------
Create and activate a virtual environment, then install requirements (PowerShell):

```powershell
cd C:\Users\KIIT0001\Desktop\nl-to-sql-generator
python -m venv .venv
# If you get a policy error activating the venv, run PowerShell as Admin and set-executionpolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the app (Streamlit)
-----------------------
```powershell
# from the repository root
streamlit run app\main.py
```

What the app does on start
--------------------------
- Connects to the SQLite database configured by `DATABASE_URL` (default: `sqlite:///./data/sample_database.db`).
- If the `employees` table does not exist, the app will create `data/sample_database.db` and populate it with embedded sample rows using `app/database/data_loader.py`.
- Ensures a `query_history` table exists (used to persist query history and favorites).

Configuration / Environment variables
-------------------------------------
You can set these via a `.env` file or environment variables.
- DATABASE_URL - SQLAlchemy connection string (default: `sqlite:///./data/sample_database.db`)
- MODEL_NAME - transformers model ID used for SQL generation (default is set in `app/utils/config.py`)
- MAX_SQL_LENGTH - max length for generated SQL tokens
- ENABLE_SAFETY_CHECKS - `True`/`False` to enable LLM safety checks

Files of interest
-----------------
- `app/main.py` - Streamlit app UI and main logic
- `app/database/connection.py` - DB connection helpers, query execution, history persistence
- `app/database/data_loader.py` - creates and populates sample SQLite DB
- `app/models/sql_generator.py` - wrapper for the LLM + rule-based fallback
- `app/models/schema_manager.py` - inspects DB schema and returns context for prompts
- `requirements.txt` - Python dependencies

How query history works
-----------------------
- Every executed query is saved into the `query_history` table with columns: id, timestamp, user_query, sql_query, result (JSON), error, favorite.
- Sidebar "Recent Queries" shows the most recent rows. The UI prefers showing the natural-language `user_query` when available, otherwise it falls back to the generated SQL. If both are empty, the UI shows a short preview extracted from the stored `result` JSON.
- To clear history manually, either delete `data/sample_database.db` (will recreate sample data on next run) or connect to the DB and run:

```sql
DELETE FROM query_history;
VACUUM;
```

Troubleshooting
---------------
- "no such table: employees" — the app tries to create the sample DB automatically, but if you set a custom `DATABASE_URL` or the process cannot write to `data/`, create the DB manually by running `python data/create_sample_data.py` or ensure the configured DB path is writable.
- Missing Python packages — install from `requirements.txt` using the steps above.
- Streamlit hot-reload — Streamlit should auto-reload on file changes. If not, stop and re-run the `streamlit run` command.

Developer notes
---------------
- The SQL generator uses Hugging Face transformers if available. If the model cannot be loaded, a deterministic rule-based fallback is used.
- The app currently stores query results as JSON in the `result` column for quick previews. If you change the schema for `query_history`, keep backward compatibility in mind.
- Explain/EXPLAIN plan code exists in `app/database/connection.py` but the UI does not currently expose it — it can be re-enabled if desired.

Extending the project
---------------------
Ideas (incremental):
- Fine-tune a SQL generation model (LoRA or full fine-tune). Add a `training/` folder with a dataset and training script.
- Improve JOIN generation by inferring foreign keys from column naming conventions and including join-candidates in the prompt.
- Add advanced visualization suggestions (Altair) based on result shape.
- Add multi-user authentication and per-user history (requires changing `query_history` schema to include `user_id`).

Contributing
------------
Feel free to open issues or PRs. Keep changes small and include tests if you modify core behavior.

License
-------
This project is provided as-is. Add your preferred license file if you plan to publish.

Contact / Help
--------------
If you want me to implement any of the next features (visualization, optimization tips, model fine-tuning, or auth), tell me which one and I'll propose a short plan and implement it.
>>>>>>> 6b5610ba (added)
