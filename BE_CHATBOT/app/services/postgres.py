import urllib.parse

from sqlmodel import create_engine

from config.base_config import APP_CONFIG


def get_postgres_uri() -> str:
    user = APP_CONFIG.postgres_config.user
    password = urllib.parse.quote_plus(APP_CONFIG.postgres_config.password.get_secret_value())
    host = APP_CONFIG.postgres_config.server
    port = APP_CONFIG.postgres_config.port
    db = APP_CONFIG.postgres_config.db
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(get_postgres_uri())
