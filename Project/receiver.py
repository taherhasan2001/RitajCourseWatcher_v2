import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import TELEGRAM_API_TOKEN

BOT_TOKEN = TELEGRAM_API_TOKEN

# Ensure USERS directory exists
os.makedirs("USERS", exist_ok=True)

# Load data.json (course list)
try:
    with open("data.json", "r", encoding="utf-8") as file:
        data = json.load(file)
except Exception as e:
    print("❌ Failed to load data.json:", e)
    data = {}

# In-memory state tracking
user_states = {}

QUESTIONS = [
    "📘 الرجاء ادخال رمز المادة (مثال ENCS3320):",
    "📌 الرجاء ادخال رقم الشعبة (مثال 1):",
    "🔢 ادخل العدد الاقصى المسموح والذي عنده سنرسل لك إشعاراً:",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"step": 0, "data": {}}
    await update.message.reply_text("👋 مرحبا! سأقوم بمراقبة الشعب لك.\n" + QUESTIONS[0])

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔹 /start - لبدء تسجيل طلب جديد\n"
        "🔹 فقط اتبع التعليمات بعد كتابة /start\n"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()

    if user_id not in user_states:
        await update.message.reply_text("⚠️ الرجاء كتابة /start للبدء.")
        return

    state = user_states[user_id]
    step = state["step"]

    if step == 0:
        cid = message.upper()
        if cid in data:
            state["data"]["CID"] = cid
            state["step"] += 1
        else:
            await update.message.reply_text("❌ الرمز غير صحيح. مثال ENCS3320")
            return

    elif step == 1:
        if not message.isdigit():
            await update.message.reply_text("❌ أدخل رقم الشعبة بشكل صحيح (مثال 1)")
            return
        sid = int(message)
        cid = state["data"]["CID"]
        if 1 <= sid <= len(data[cid]["sections"]):
            state["data"]["SID"] = sid
            state["step"] += 1
        else:
            await update.message.reply_text("🚫 رقم الشعبة غير موجود حالياً.")
            return

    elif step == 2:
        if not message.isdigit():
            await update.message.reply_text("❌ أدخل رقماً صحيحاً كحد أقصى (مثال 30)")
            return
        state["data"]["MAX"] = int(message)
        state["step"] += 1

    if state["step"] == 3:
        # Save request
        with open(f"USERS/{user_id}.json", "w", encoding="utf-8") as f:
            json.dump(state["data"], f, indent=4, ensure_ascii=False)

        await update.message.reply_text(
            "✅ تم حفظ طلبك! سيتم إشعارك عند توفر مقعد.\n"
            "🔄 لإرسال طلب جديد، اكتب /start"
        )
        del user_states[user_id]
    else:
        await update.message.reply_text(QUESTIONS[state["step"]])

# =========================
# BOT INITIALIZATION
# =========================

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bot is running...")
app.run_polling()
