import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "StudyGraph API"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    
    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-it")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

settings = Settings()
