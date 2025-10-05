import json
import os
import asyncio
import logging
from telegram import Bot
from config import TELEGRAM_API_TOKEN, CHECK_EVERY

# =========================
# CONFIG & CONSTANTS
# =========================

BOT_TOKEN = TELEGRAM_API_TOKEN
USERS_DIR = "USERS"
DATA_FILE = "data.json"

# Telegram message template
MESSAGE_TEMPLATE = (
    "📢 تنبيه \n"
    "شعبة {cid}\n"
    "يوجد فيها {current_capacity} والعدد الاقصى هو {max_capacity}\n"
    "سارع بالتسجيل"
)

# =========================
# LOGGING SETUP
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# =========================
# UTILITY FUNCTIONS
# =========================

def load_json(path):
    """Load JSON safely with error handling."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Failed to read JSON: {path} - {e}")
        return None

async def send_message(bot, user_id, cid, current_capacity, max_capacity):
    """Send Telegram message."""
    text = MESSAGE_TEMPLATE.format(
        cid=cid, current_capacity=current_capacity, max_capacity=max_capacity
    )
    try:
        await bot.send_message(chat_id=user_id, text=text)
        logging.info(f"✅ Message sent to {user_id}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to send message to {user_id}: {e}")
        return False

# =========================
# CORE LOGIC
# =========================

async def check_and_send_notifications(bot):
    """Check all users' request files and notify if criteria match."""

    data = load_json(DATA_FILE)
    if not data:
        logging.error("❌ Skipping notification check due to missing DATA_FILE.")
        return

    for file_name in os.listdir(USERS_DIR):
        if not file_name.endswith('.json'):
            continue

        user_file = os.path.join(USERS_DIR, file_name)
        request = load_json(user_file)
        if not request:
            continue

        try:
            cid = request["CID"]
            sid = int(request["SID"])
            max_capacity = int(request["MAX"])
            current_capacity = int(data[cid]['sections'][sid - 1]['capacity'])
        except Exception as e:
            logging.error(f"❌ Invalid data structure in {file_name}: {e}")
            continue

        logging.info(f"Checking {file_name}: {cid} - Section {sid}, Current: {current_capacity}, Max: {max_capacity}")

        if current_capacity < max_capacity:
            user_id = int(file_name.split('.')[0])
            success = await send_message(bot, user_id, cid, current_capacity, max_capacity)

            if success:
                try:
                    os.remove(user_file)
                    logging.info(f"🗑️ Deleted request file: {file_name}")
                except Exception as e:
                    logging.error(f"❌ Failed to delete {file_name}: {e}")

# =========================
# MAIN LOOP
# =========================

async def main():
    bot = Bot(token=BOT_TOKEN)
    logging.info("🚀 Bot started. Waiting for notifications...")

    try:
        while True:
            await check_and_send_notifications(bot)
            await asyncio.sleep(CHECK_EVERY)
    except KeyboardInterrupt:
        logging.warning("🛑 Manual stop triggered.")
    finally:
        logging.info("Shutting down bot...")
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
