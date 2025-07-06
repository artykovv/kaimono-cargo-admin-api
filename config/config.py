import os
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

load_dotenv()

SECRET = os.environ.get("POSTGRESQL_PASSWORD")

DB_HOST = os.environ.get("POSTGRESQL_HOST")
DB_PORT = os.environ.get("POSTGRESQL_PORT")
DB_NAME = os.environ.get("POSTGRESQL_DBNAME")
DB_USER = os.environ.get("POSTGRESQL_USER")
DB_PASS = os.environ.get("POSTGRESQL_PASSWORD")


TELEGRAM_API_URL = os.environ.get("TELEGRAM_API_URL")
TELEGRAM_API_KEY = os.environ.get("TELEGRAM_API_KEY")

TRANSIT_API_URL = f"{TELEGRAM_API_URL}/api/v1/notification/transit"
CHINA_API_URL = f"{TELEGRAM_API_URL}/api/v1/notification/china"
BISHKEK_API_URL = f"{TELEGRAM_API_URL}/api/v1/notification/bishkek"


ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
ENDPOINT_URL = os.environ.get("ENDPOINT_URL")
BUCKET_NAME = os.environ.get("BUCKET_NAME")