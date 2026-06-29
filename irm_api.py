"""
Industrial Color AI Platform (ICAP) — Application Entry Point
==========================================================
Version: 0.1.1 Enterprise
"""

import uvicorn
import os
from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("ICAP_PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
