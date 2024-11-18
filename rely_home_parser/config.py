import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (если используется)
load_dotenv()

# Логирование
logging.getLogger("urllib3").setLevel(logging.ERROR)

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
logging.basicConfig(format=LOG_FORMAT)
log = logging.getLogger("relyhome.parser")

LOG_LEVEL = os.getenv("LOGLEVEL", "DEBUG").upper()
if LOG_LEVEL not in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"):
    raise ValueError(f"Invalid LOGLEVEL: {LOG_LEVEL}")
log.setLevel(LOG_LEVEL)

# Google API Settings
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SAMPLE_SPREADSHEET_ID = os.getenv("SAMPLE_SPREADSHEET_ID", "default_spreadsheet_id")
SAMPLE_RANGE_NAME = os.getenv("SAMPLE_RANGE_NAME", "CHOICE!B2:B")
TOKEN_FILE = os.getenv("TOKEN_FILE", "token.json")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "credentials.json")

# Application settings
MAIN_URL = os.getenv("MAIN_URL", "https://relyhome.com/login/")
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
if not LOGIN or not PASSWORD:
    raise EnvironmentError("LOGIN and PASSWORD must be set in environment variables.")

SYSTEMS_WITH_VALUE = {
    "Dryer": 1,
    "Microwave": 1,
}
CITIES_WITH_VALUE = {
    "Dallas": 1,
    "Irving": 1,
    "Arlington": 1,
    "Garland": 0,
    "Sachse": 0,
    "Wylie": 0,
    "Rowlett": 0,
    "Mesquite": 0,
}
ZIP_CODES = {}

# Отладочная информация
log.info(
    f"Configuration loaded: LOGLEVEL={LOG_LEVEL}, SAMPLE_SPREADSHEET_ID={SAMPLE_SPREADSHEET_ID}, "
    f"SAMPLE_RANGE_NAME={SAMPLE_RANGE_NAME}, FILE_PATH={FILE_PATH}, MAIN_URL={MAIN_URL}"
)
