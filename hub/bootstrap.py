"""مسیر import هاب HTTP.

هاب خودش فقط auth و اتصال crud را لازم دارد. هر دامنه در فرآیند
جدا بالا می‌آید چون logging_module و errors بین پوشه‌ها هم‌نام‌اند.
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
CRUD_ROOT = REPO_ROOT / "crud"


def install_hub_import_path() -> None:
    """ریشهٔ ریپو و crud را طوری می‌چیند که auth و repository پیدا شوند."""
    ordered = [str(CRUD_ROOT), str(REPO_ROOT)]
    for path in ordered:
        if path in sys.path:
            sys.path.remove(path)
    for path in reversed(ordered):
        sys.path.insert(0, path)
