from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("ROBOOPS_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = Path(os.getenv("ROBOOPS_UPLOAD_DIR", DATA_DIR / "uploads"))
DATABASE_PATH = Path(os.getenv("ROBOOPS_DATABASE", DATA_DIR / "roboops.sqlite"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
