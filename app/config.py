import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
    TEMPLATE_FOLDER = os.getenv("TEMPLATE_FOLDER")
    SECRET_TOKEN = os.getenv("SECRET_TOKEN")
    VPS_URL = os.getenv("VPS_URL")