from pydantic import BaseModel
import os


class Settings(BaseModel):
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "swldb")
    db_user: str = os.getenv("DB_USER", "swluser")
    db_password: str = os.getenv("DB_PASSWORD", "swlpass")
    db_sslmode: str = os.getenv("DB_SSLMODE", "disable")
    api_port: int = int(os.getenv("API_PORT", "8080"))

    def dsn(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?sslmode={self.db_sslmode}"
        )


settings = Settings()


