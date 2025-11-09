"""Runtime build stamp to verify running code version.

The value is generated at import time so it changes on each process
restart. It helps confirm that the bot is running the expected code.
"""
from datetime import datetime


BUILD_STAMP = datetime.utcnow().strftime("v%Y-%m-%d %H:%M UTC")

