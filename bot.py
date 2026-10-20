import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("queen bee online 🐝")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.lower()
    if "wake up bee" in txt:
        await update.message.reply_text("queen bee awake! 👑🐝")
        return
    await update.message.reply_text(f"Bee: {update.message.text}")

tg_app = ApplicationBuilder().token(TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bee bot is alive 🐝"

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return "ok"

@app.route("/setwebhook", methods=["GET"])
async def set_webhook():
    url = request.host_url.rstrip("/") + f"/{TOKEN}"
    await tg_app.bot.set_webhook(url)
    return f"Webhook set to {url}"

if __name__ == "__main__":
    tg_app.run_polling()
