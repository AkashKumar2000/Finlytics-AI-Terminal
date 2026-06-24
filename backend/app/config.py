from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    """
    
    BaseSettings automatically:
    1. Looks at your .env file
    2. Finds KITE_API_KEY=abc123xyz
    3. Overrides the empty default with the real value
    """
    APP_NAME: str = "Investment Research Dashboard"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/investdb"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@db:5432/investdb"

    # JWT Auth
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # AI / LLM
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1

    # External APIs
    NEWS_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    # Zerodha Kite Connect
    KITE_API_KEY: str = ""
    KITE_API_SECRET: str = ""
    KITE_ACCESS_TOKEN: str = ""

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:               # class Config is pydantic's way to configure how BaseSettings behaves:
        env_file = ".env"  # env_file = ".env" — tells it to read variables from the .env file in your project root
        case_sensitive = True # case_sensitive = True — means KITE_API_KEY in .env must exactly match KITE_API_KEY in config.py — kite_api_key or
                                # Kite_Api_Key would NOT work


settings = Settings()