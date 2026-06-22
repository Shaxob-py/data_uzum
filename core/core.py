from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_DATABASE: str
    DB_PORT : str


    ADMIN_PHONE: str
    ADMIN_PASSWORD: str
    ADMIN_TELEGRAM_ID: int

    BOT_TOKEN: str

    class Config:
        env_file = ".env"

    def postgres_async_url(self):
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:"
                f"{self.DB_PORT}/{self.DB_DATABASE}")


settings = Settings()
