from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'certificates.db'}"
GENERATED_DIR = BASE_DIR / "generated"
TEMPLATE_DIR = BASE_DIR / "app" / "templates"

GENERATED_DIR.mkdir(exist_ok=True)
