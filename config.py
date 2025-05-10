# Copyright (c) 2025 devgagan : https://github.com/devgaganin.
# Licensed under the GNU General Public License v3.0.
# See LICENSE file in the repository root for full license text.

import os
from dotenv import load_dotenv

load_dotenv()

# VPS --- FILL COOKIES 🍪 in """ ... """

INST_COOKIES = """
# write up here insta cookies
"""

YTUB_COOKIES = """
# write here yt cookies
"""

API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_DB", "")
OWNER_ID = [int(x) for x in os.getenv("OWNER_ID", "5914434064").split() if x.isdigit()]  # list separated via space
DB_NAME = os.getenv("DB_NAME", "telegram_downloader")
STRING = os.getenv("STRING", None)  # optional

def parse_int_env(var_name):
    val = os.getenv(var_name, None)
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None

LOG_GROUP = parse_int_env("LOG_GROUP", "-1002633547185")  # optional with -100
FORCE_SUB = parse_int_env("FORCE_SUB", "-1002558537382")  # optional with -100

YT_COOKIES = os.getenv("YT_COOKIES", YTUB_COOKIES)
INSTA_COOKIES = os.getenv("INSTA_COOKIES", INST_COOKIES)
