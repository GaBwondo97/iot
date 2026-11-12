import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    app_name: str = "CityPulse AI"
    app_version: str = "0.1.0"
    app_description: str = (
        "AI-powered urban monitoring and risk assessment platform"
    )
    database_url: str = os.getenv("DATABASE_URL", "")


env_config = Settings()