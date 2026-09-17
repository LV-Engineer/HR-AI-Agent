from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / '.env'

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra='ignore')

    app_env: str = 'development'
    company_email_domain: str
    database_url: str

    redis_url: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    anthropic_api_key: str
    mcp_server_url: str = 'http://mcp-server:8000/mcp'

    ollama_url: str = 'http://ollama:11434'
    embedding_model: str = 'bge-m3'
    cv_storage_dir: str = '/app/storage/cv'
    policy_storage_dir: str = '/app/storage/policies'
    reports_dir: str = '/app/storage/reports'
    frontend_origin: str = 'http://localhost:5173'

settings = Settings()