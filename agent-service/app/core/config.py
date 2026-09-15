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

settings = Settings()