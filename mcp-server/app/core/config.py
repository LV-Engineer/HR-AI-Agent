from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    database_url: str
    ollama_url: str = 'http://ollama:11434'
    embedding_model: str = 'bge-m3'


settings = Settings()