from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    JSONPLACEHOLDER_BASE_URL: str = "https://jsonplaceholder.typicode.com"
    HTTP_TIMEOUT: float = 5.0
    HTTP_RETRIES: int = 3
    HTTP_BACKOFF: float = 0.3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
