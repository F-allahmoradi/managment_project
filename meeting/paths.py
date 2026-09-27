"""sys.path سرور جلسات: پوشهٔ meeting، ریشهٔ ریپو، و crud.

auth و اتصال Postgres از crud می‌آیند. mcp_server و logging_module
و errors همین پوشه‌اند تا با کراد قاطی نشوند.
"""

from pathlib import Path
import sys

MEETING_ROOT = Path(__file__).resolve().parent
REPO_ROOT = MEETING_ROOT.parent
CRUD_ROOT = REPO_ROOT / "crud"


def ensure_import_path() -> None:
    """ترتیب import را meeting → ریپو → crud می‌گذارد."""
    ordered = [str(MEETING_ROOT), str(REPO_ROOT), str(CRUD_ROOT)]
    for path in ordered:
        if path in sys.path:
            sys.path.remove(path)
    for path in reversed(ordered):
        sys.path.insert(0, path)
