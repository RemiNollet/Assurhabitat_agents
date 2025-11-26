import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

BASE_MODEL = "mistralai/Devstral-Small-2507"
MAX_NEW_TOKENS = 4096
