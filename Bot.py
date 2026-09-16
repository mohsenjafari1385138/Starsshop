# -*- coding: utf-8 -*-
"""
نمونه‌کار: ربات فروش استارز و پرمیوم تلگرام + مینی‌اپ
------------------------------------------------------
این یک نسخه‌ی دمو/نمونه‌کاره برای نشون دادن مهارت به کارفرما.
بخش‌های زیر عمداً شبیه‌سازی (mock) شدن و باید در نسخه‌ی واقعی
جایگزین بشن:
  - اتصال به تامین‌کننده واقعی استارز/پرمیوم (مثل Fragment API)
  - اتصال به درگاه پرداخت واقعی (زرین‌پال/آیدی‌پی)
  - ذخیره‌سازی سفارش‌ها در دیتابیس واقعی (اینجا فقط حافظه موقت)

نصب پیش‌نیاز:
    pip install python-telegram-bot==21.4

اجرا:
    python bot.py

نکته: مینی‌اپ (پوشه miniapp/) باید روی یک آدرس https میزبانی بشه
(مثلاً GitHub Pages، Netlify، یا هر هاست ساده‌ای که SSL داره) چون
Telegram Web App فقط با https کار می‌کنه، نه با فایل لوکال.
"""

import json
import logging
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

# ---------------------- تنظیمات ----------------------

BOT_TOKEN = "TOKEN_ربات_خودتو_اینجا_بذار"
ADMIN_CHAT_ID = 123456789  # آیدی عددی ادمین برای دریافت اعلان سفارش

# آدرس مینی‌اپی که آپلود کردی (باید https باشه)
MINI_APP_URL = "https://example.com/telegram-stars-demo/"

# حافظه‌ی موقت سفارش‌ها (در نسخه واقعی: دیتابیس)
orders = []


# ---------------------- دستورات ربات ----------------------

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


# ---------------------- دریافت داده از مینی‌اپ ----------------------

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی کاربر تو مینی‌اپ سفارش می‌ده، این هندلر صداش رو می‌شنوه."""
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

    # ---- اینجا در نسخه واقعی درگاه پرداخت صدا زده میشه ----
    # payment_link = create_payment_link(order["price"])
    # فعلاً برای دمو مستقیم پیام تایید می‌فرستیم:

    await update.message.reply_text(
        f"✅ سفارش شما ثبت شد:\n\n"
        f"بسته: {label}\n"
        f"گیرنده: @{order['username']}\n"
        f"مبلغ: {order['price']:,} تومان\n\n"
        f"در نسخه‌ی نهایی، اینجا لینک پرداخت درگاه ارسال میشه و "
        f"بعد از تایید پرداخت، سفارش به‌صورت خودکار برای تامین‌کننده ارسال "
        f"و همون لحظه تحویل داده میشه."
    )

    # اعلان برای ادمین
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


# ---------------------- اجرای ربات ----------------------

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", my_orders))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    log.info("ربات در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()
