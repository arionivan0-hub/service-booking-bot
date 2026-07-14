import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not set. Create .env file with BOT_TOKEN=your_token", file=sys.stderr)
    sys.exit(1)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///database/bookings.db",
)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

# Admin Telegram IDs (comma-separated) for bot admin commands
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]

# Working hours
WORK_START = int(os.getenv("WORK_START", "9"))
WORK_END = int(os.getenv("WORK_END", "18"))
SAT_WORK_END = int(os.getenv("SAT_WORK_END", "14"))
SUNDAY_CLOSED = os.getenv("SUNDAY_CLOSED", "true").lower() == "true"

# Timezone offset from UTC (default: Moscow UTC+3)
TZ_OFFSET = int(os.getenv("TZ_OFFSET", "3"))

# Advance booking: how many days ahead a user can book
BOOKING_AHEAD_DAYS = int(os.getenv("BOOKING_AHEAD_DAYS", "14"))

# Reminder hours before appointment (comma-separated, e.g. "24,2")
REMINDER_HOURS: list[int] = [
    int(x.strip()) for x in os.getenv("REMINDER_HOURS", "24,2").split(",") if x.strip().isdigit()
]

# Redis for FSM storage (fallback to MemoryStorage if not set)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
