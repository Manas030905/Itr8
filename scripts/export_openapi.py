"""Write the FastAPI OpenAPI schema to apps/api/openapi.json (input for the typed web client).

Run from apps/api:  uv run python ../../scripts/export_openapi.py
No database connection is made; only the app's route definitions are read.
"""

import json
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402

out = API_ROOT / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
print(f"wrote {out.relative_to(API_ROOT.parents[1])}")
