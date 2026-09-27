"""سازگاری؛ اتصال واقعی در repository است."""

from repository.connection import load_database_config, open_connection

__all__ = ["load_database_config", "open_connection"]
