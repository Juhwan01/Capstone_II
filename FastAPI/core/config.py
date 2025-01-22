import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class DefaultConfig(BaseSettings):
    postgresql_endpoint: str = os.getenv("POSTGRESQL_ENDPOINT", "localhost")
    postgresql_port: int = os.getenv("POSTGRESQL_PORT", "5432")
    postgresql_table: str = os.getenv("POSTGRESQL_TABLE", "postgres")
    postgresql_user: str = os.getenv("POSTGRESQL_USER", "postgres")
    postgresql_password: str = os.getenv("POSTGRESQL_PASSWORD", "3321")

    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "5c2fea6305c8c209714e73b265958703e65c4b40dec4c388dddac06f3f791ec7",
    )
    jwt_expire_minutes: int = os.getenv("JWT_TOKEN_EXPIRE_MINUTES", 600)


@lru_cache
def get_config():
    return DefaultConfig()