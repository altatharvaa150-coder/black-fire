"""Generate the committed API contract from the application without starting it."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "services" / "api"))
from blackfire.main import app  # noqa: E402

path = root / "contracts" / "openapi.json"
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
print("Generated contracts/openapi.json")
