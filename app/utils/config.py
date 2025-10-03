import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/sample_database.db")
    MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/DialoGPT-medium")
    MAX_SQL_LENGTH = int(os.getenv("MAX_SQL_LENGTH", "200"))
    ENABLE_SAFETY_CHECKS = os.getenv("ENABLE_SAFETY_CHECKS", "True").lower() == "true"
    
settings = Settings()