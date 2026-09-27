"""کمک تست STT: بازیگر موقت از conftest کراد."""

from pathlib import Path
import importlib.util
import sys

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

_CRUD_CONFTEST = _ROOT.parent / "crud" / "tests" / "conftest.py"
_spec = importlib.util.spec_from_file_location("crud_test_helpers", _CRUD_CONFTEST)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

bind_actor_as_role = _mod.bind_actor_as_role
