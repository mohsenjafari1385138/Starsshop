# -*- coding: utf-8 -*-
"""
ربات فروش استارز و پرمیوم تلگرام + مینی‌اپ
نسخه‌ی دمو برای Render
"""

import os
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", 0))
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://example.com/telegram-stars-demo/")

orders = []


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass


def run_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    log.info(f"Health server started on port {port}")
    server.serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🛍 ورود به فروشگاه",
            web_app=WebAppInfo(url=MINI_APP_URL),
        )]
    ])
    await update.message.reply_text(
        "به استارلین خوش اومدی! ⭐️\n\n"
        "از اینجا می‌تونی استارز یا اشتراک پرمیوم تلگرام رو "
        "به‌صورت خودکار و آنی خریداری کنی.\n\n"
        "برای شروع، روی دکمه‌ی زیر بزن:",
        reply_markup=keyboard,
    )


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_orders = [o for o in orders if o["user_id"] == user_id]

    if not user_orders:
        await update.message.reply_text("هنوز سفارشی ثبت نکردی.")
        return

    lines = ["📦 سفارش‌های اخیر تو:\n"]
    for o in user_orders[-5:]:
        label = f"{o['amount']} استارز" if o["type"] == "stars" else f"پرمیوم {o['months']} ماهه"
        lines.append(f"• {label} — {o['price']:,} تومان — {o['status']}")

    await update.message.reply_text("\n".join(lines))


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.effective_message.web_app_data.data
    try:
        order = json.loads(raw)
    except json.JSONDecodeError:
        await update.message.reply_text("خطا در دریافت سفارش. دوباره تلاش کن.")
        return

    order["user_id"] = update.effective_user.id
    order["username_teleg"] = update.effective_user.username
    order["created_at"] = datetime.now().isoformat(timespec="seconds")
    order["status"] = "در انتظار پرداخت"
    orders.append(order)

    label = (
        f"{order['amount']} استارز"
        if order["type"] == "stars"
        else f"پرمیوم {order['months']} ماهه"
    )

    await update.message.reply_text(
        f"✅ سفارش شما ثبت شد:\n\n"
        f"بسته: {label}\n"
        f"گیرنده: @{order['username']}\n"
        f"مبلغ: {order['price']:,} تومان\n\n"
        f"در نسخه‌ی نهایی، اینجا لینک پرداخت درگاه ارسال میشه."
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"🔔 سفارش جدید\n"
                f"بسته: {label}\n"
                f"گیرنده: @{order['username']}\n"
                f"مبلغ: {order['price']:,} تومان\n"
                f"از طرف: @{order['username_teleg']} ({order['user_id']})"
            ),
        )
    except Exception as e:
        log.error(f"ارسال به ادمین fail شد: {e}")


def main():
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", my_orders))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    log.info("ربات در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()
