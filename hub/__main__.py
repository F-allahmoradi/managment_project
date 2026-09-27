"""اجرای سرور API.

از ریشه ریپو:
    python -m hub
"""

import logging

from hub.bootstrap import install_hub_import_path

install_hub_import_path()

import uvicorn

from hub.app import app
from hub.config import load_settings


def main() -> None:
    """سرور را روی API_HOST و API_PORT بالا می‌آورد."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = load_settings()
    uvicorn.run(app, host=settings["host"], port=settings["port"])


if __name__ == "__main__":
    main()
