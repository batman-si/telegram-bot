import logging
import sqlite3
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# SETTINGS
# =========================================================

# =========================================================
# 🔐 BOT TOKEN — توکن جدید ربات را اینجا قرار بده
# =========================================================

TOKEN = "8835412515:AAFK5gmeDqWT1qSKEGu_InnI3YG2BOL0xRc"

ADMIN_ID = 8855028648

CHANNEL_USERNAME = "@Zorvix_vpn"
CHANNEL_LINK = "https://t.me/Zorvix_vpn"

SUPPORT_USERNAME = "@OFF_voidrx"
SUPPORT_LINK = "https://t.me/OFF_voidrx"

DATABASE = "bot.db"

REFERRAL_REWARD = 30000

# قیمت نت سرور ملی
NATIONAL_SERVER_PRICE_PER_GB = 50000


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =========================================================
# DATABASE
# =========================================================

db = sqlite3.connect(
    DATABASE,
    check_same_thread=False
)

cursor = db.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    plan_id TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    volume TEXT NOT NULL,
    duration TEXT NOT NULL,
    price INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    config TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    referred_id INTEGER PRIMARY KEY,
    referrer_id INTEGER NOT NULL,
    reward INTEGER NOT NULL DEFAULT 30000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")


db.commit()


# =========================================================
# PLANS
# =========================================================

PLANS = {
    "1": {
        "name": "کانفیگ 20 گیگ",
        "volume": "20GB",
        "duration": "1 ماه",
        "price": 1000000
    },

    "2": {
        "name": "کانفیگ 40 گیگ",
        "volume": "40GB",
        "duration": "1 ماه",
        "price": 2000000
    },

    "3": {
        "name": "کانفیگ 60 گیگ",
        "volume": "60GB",
        "duration": "1 ماه",
        "price": 3000000
    },

    "4": {
        "name": "کانفیگ 80 گیگ",
        "volume": "80GB",
        "duration": "1 ماه",
        "price": 4000000
    },

    "5": {
        "name": "کانفیگ 100 گیگ",
        "volume": "100GB",
        "duration": "1 ماه",
        "price": 5000000
    },

    "6": {
        "name": "کانفیگ 200 گیگ",
        "volume": "200GB",
        "duration": "3 ماه",
        "price": 10000000
    },

    "7": {
        "name": "کانفیگ 400 گیگ",
        "volume": "400GB",
        "duration": "3 ماه",
        "price": 20000000
    },

    "8": {
        "name": "کانفیگ 600 گیگ",
        "volume": "600GB",
        "duration": "3 ماه",
        "price": 30000000
    },

    "9": {
        "name": "کانفیگ 800 گیگ",
        "volume": "800GB",
        "duration": "3 ماه",
        "price": 40000000
    },

    "10": {
        "name": "کانفیگ 1 ترابایت",
        "volume": "1TB",
        "duration": "3 ماه",
        "price": 50000000
    },
}


# =========================================================
# HELPERS
# =========================================================

def money(amount):
    return f"{amount:,} تومان"


def register_user(user):

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, username, balance)
        VALUES (?, ?, 0)
        """,
        (
            user.id,
            user.username or "ندارد"
        )
    )

    cursor.execute(
        """
        UPDATE users
        SET username = ?
        WHERE user_id = ?
        """,
        (
            user.username or "ندارد",
            user.id
        )
    )

    db.commit()


def get_balance(user_id):

    cursor.execute(
        """
        SELECT balance
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return 0


# =========================================================
# CHANNEL MEMBERSHIP
# =========================================================

async def check_membership(user_id, context):

    try:

        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception as e:

        logger.error(
            f"Membership error: {e}"
        )

        return False


# =========================================================
# BUTTONS
# =========================================================

def join_buttons():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 عضویت در کانال",
                url=CHANNEL_LINK
            )
        ],

        [
            InlineKeyboardButton(
                "✅ بررسی عضویت",
                callback_data="check_membership"
            )
        ]
    ])


def main_buttons():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🛒 خرید کانفیگ",
                callback_data="buy"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 کیف پول",
                callback_data="wallet"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 زیرمجموعه‌گیری",
                callback_data="referral"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 سفارش‌های من",
                callback_data="orders"
            )
        ],

        [
            InlineKeyboardButton(
                "💬 پشتیبانی",
                url=SUPPORT_LINK
            )
        ]

    ])


def buy_buttons():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🇮🇷 نت سرور ملی | هر گیگ ۵۰,۰۰۰ تومان",
                callback_data="national_server"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 طرح‌های ۱ ماهه",
                callback_data="monthly"
            )
        ],

        [
            InlineKeyboardButton(
                "🚀 طرح‌های ۳ ماهه",
                callback_data="large"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 برگشت",
                callback_data="home"
            )
        ]

    ])


def monthly_buttons():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "1️⃣ 20GB | 1,000,000 تومان",
                callback_data="plan_1"
            )
        ],

        [
            InlineKeyboardButton(
                "2️⃣ 40GB | 2,000,000 تومان",
                callback_data="plan_2"
            )
        ],

        [
            InlineKeyboardButton(
                "3️⃣ 60GB | 3,000,000 تومان",
                callback_data="plan_3"
            )
        ],

        [
            InlineKeyboardButton(
                "4️⃣ 80GB | 4,000,000 تومان",
                callback_data="plan_4"
            )
        ],

        [
            InlineKeyboardButton(
                "5️⃣ 100GB | 5,000,000 تومان",
                callback_data="plan_5"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 برگشت",
                callback_data="buy"
            )
        ]

    ])


def large_buttons():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "6️⃣ 200GB | 10,000,000 تومان",
                callback_data="plan_6"
            )
        ],

        [
            InlineKeyboardButton(
                "7️⃣ 400GB | 20,000,000 تومان",
                callback_data="plan_7"
            )
        ],

        [
            InlineKeyboardButton(
                "8️⃣ 600GB | 30,000,000 تومان",
                callback_data="plan_8"
            )
        ],

        [
            InlineKeyboardButton(
                "9️⃣ 800GB | 40,000,000 تومان",
                callback_data="plan_9"
            )
        ],

        [
            InlineKeyboardButton(
                "🔟 1TB | 50,000,000 تومان",
                callback_data="plan_10"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 برگشت",
                callback_data="buy"
            )
        ]

    ])


def wallet_buttons():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "➕ درخواست شارژ",
                url=SUPPORT_LINK
            )
        ],

        [
            InlineKeyboardButton(
                "🔄 بروزرسانی",
                callback_data="wallet"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 برگشت",
                callback_data="home"
            )
        ]

    ])


# =========================================================
# REFERRAL
# =========================================================

async def process_referral(
    user,
    context,
    referrer_id
):

    if referrer_id == user.id:
        return

    cursor.execute(
        """
        SELECT referred_id
        FROM referrals
        WHERE referred_id = ?
        """,
        (user.id,)
    )

    if cursor.fetchone():
        return

    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        """,
        (referrer_id,)
    )

    if not cursor.fetchone():
        return

    cursor.execute(
        """
        INSERT INTO referrals
        (
            referred_id,
            referrer_id,
            reward
        )
        VALUES (?, ?, ?)
        """,
        (
            user.id,
            referrer_id,
            REFERRAL_REWARD
        )
    )

    cursor.execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE user_id = ?
        """,
        (
            REFERRAL_REWARD,
            referrer_id
        )
    )

    db.commit()

    new_balance = get_balance(
        referrer_id
    )

    try:

        await context.bot.send_message(
            chat_id=referrer_id,
            text=(
                "🎉 زیرمجموعه جدید!\n\n"

                f"👤 کاربر: "
                f"@{user.username or 'ندارد'}\n"

                f"🎁 پاداش: "
                f"{money(REFERRAL_REWARD)}\n"

                f"💰 موجودی جدید: "
                f"{money(new_balance)}"
            )
        )

    except Exception as e:

        logger.error(
            f"Referral notification error: {e}"
        )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    register_user(user)

    if context.args:

        arg = context.args[0]

        if arg.startswith("ref_"):

            try:

                referrer_id = int(
                    arg.replace(
                        "ref_",
                        "",
                        1
                    )
                )

                await process_referral(
                    user,
                    context,
                    referrer_id
                )

            except ValueError:
                pass

    member = await check_membership(
        user.id,
        context
    )

    if not member:

        await update.message.reply_text(

            "🔐 برای استفاده از ربات "
            "ابتدا باید عضو کانال شوید.\n\n"

            f"📢 {CHANNEL_USERNAME}\n\n"

            "بعد از عضویت روی "
            "«بررسی عضویت» بزنید.",

            reply_markup=join_buttons()
        )

        return

    await update.message.reply_text(

        "🤖 به ربات فروش کانفیگ خوش آمدید!\n\n"

        "یکی از گزینه‌های زیر را انتخاب کنید:",

        reply_markup=main_buttons()
    )


# =========================================================
# NATIONAL SERVER VOLUME
# =========================================================

async def national_server_volume(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "waiting_national_volume"
    ):
        return

    user = update.effective_user

    register_user(user)

    text = update.message.text.strip()

    try:

        volume = int(text)

    except ValueError:

        await update.message.reply_text(
            "❌ فقط عدد وارد کن.\n\n"
            "مثال:\n"
            "7"
        )

        return

    if volume <= 0:

        await update.message.reply_text(
            "❌ حجم باید بیشتر از صفر باشد."
        )

        return

    price = (
        volume *
        NATIONAL_SERVER_PRICE_PER_GB
    )

    context.user_data[
        "national_volume"
    ] = volume

    context.user_data[
        "national_price"
    ] = price

    context.user_data[
        "waiting_national_volume"
    ] = False

    balance = get_balance(
        user.id
    )

    # موجودی کافی نیست
    if balance < price:

        needed = price - balance

        await update.message.reply_text(

            "❌ موجودی کیف پول کافی نیست.\n\n"

            "🇮🇷 نت سرور ملی\n"

            f"📊 حجم: {volume}GB\n"

            f"💵 هر گیگ: "
            f"{money(NATIONAL_SERVER_PRICE_PER_GB)}\n"

            f"💰 قیمت: "
            f"{money(price)}\n\n"

            f"💳 موجودی شما: "
            f"{money(balance)}\n"

            f"➕ کمبود: "
            f"{money(needed)}",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "➕ شارژ کیف پول",
                        url=SUPPORT_LINK
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 برگشت",
                        callback_data="buy"
                    )
                ]

            ])
        )

        return

    # تأیید خرید
    await update.message.reply_text(

        "🛒 تأیید خرید\n\n"

        "🇮🇷 نت سرور ملی\n"

        f"📊 حجم: {volume}GB\n"

        f"💵 هر گیگ: "
        f"{money(NATIONAL_SERVER_PRICE_PER_GB)}\n"

        f"💰 قیمت نهایی: "
        f"{money(price)}\n\n"

        f"💳 موجودی شما: "
        f"{money(balance)}\n\n"

        "آیا خرید را تأیید می‌کنید؟",

        reply_markup=InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "✅ تأیید خرید",
                    callback_data="national_confirm"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 برگشت",
                    callback_data="buy"
                )
            ]

        ])
    )


# =========================================================
# CALLBACK HANDLER
# =========================================================

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    user_id = user.id

    data = query.data

    register_user(user)


    # =====================================================
    # CHECK MEMBERSHIP
    # =====================================================

    if data == "check_membership":

        member = await check_membership(
            user_id,
            context
        )

        if not member:

            await query.answer(
                "❌ هنوز عضو کانال نیستید.",
                show_alert=True
            )

            return

        await query.edit_message_text(

            "✅ عضویت شما تأیید شد!\n\n"
            "حالا می‌توانید از ربات استفاده کنید.",

            reply_markup=main_buttons()
        )

        return


    # =====================================================
    # HOME
    # =====================================================

    if data == "home":

        context.user_data[
            "waiting_national_volume"
        ] = False

        await query.edit_message_text(

            "🏠 منوی اصلی\n\n"
            "گزینه مورد نظر را انتخاب کنید:",

            reply_markup=main_buttons()
        )

        return


    # =====================================================
    # BUY
    # =====================================================

    if data == "buy":

        context.user_data[
            "waiting_national_volume"
        ] = False

        member = await check_membership(
            user_id,
            context
        )

        if not member:

            await query.edit_message_text(

                "🔐 ابتدا عضو کانال شوید.",

                reply_markup=join_buttons()
            )

            return

        await query.edit_message_text(

            "🛒 نوع سرویس را انتخاب کنید:",

            reply_markup=buy_buttons()
        )

        return


    # =====================================================
    # NATIONAL SERVER
    # =====================================================

    if data == "national_server":

        context.user_data[
            "waiting_national_volume"
        ] = True

        context.user_data.pop(
            "national_volume",
            None
        )

        context.user_data.pop(
            "national_price",
            None
        )

        await query.edit_message_text(

            "🇮🇷 نت سرور ملی\n\n"

            "📊 حجم موردنظر را "
            "به گیگ وارد کنید.\n\n"

            "مثلاً اگر 7 گیگ می‌خواهی، "
            "فقط بنویس:\n\n"

            "7\n\n"

            "💵 قیمت هر 1 گیگ: "
            "50,000 تومان"
        )

        return


    # =====================================================
    # NATIONAL CONFIRM
    # =====================================================

    if data == "national_confirm":

        volume = context.user_data.get(
            "national_volume"
        )

        price = context.user_data.get(
            "national_price"
        )

        if not volume or not price:

            await query.answer(
                "❌ اطلاعات خرید پیدا نشد.",
                show_alert=True
            )

            return

        # کم کردن موجودی به شکل امن
        cursor.execute(

            """
            UPDATE users
            SET balance = balance - ?
            WHERE user_id = ?
            AND balance >= ?
            """,

            (
                price,
                user_id,
                price
            )
        )

        if cursor.rowcount != 1:

            db.rollback()

            await query.answer(
                "❌ موجودی کافی نیست.",
                show_alert=True
            )

            return


        # ساخت سفارش
        cursor.execute(

            """
            INSERT INTO orders
            (
                user_id,
                username,
                plan_id,
                plan_name,
                volume,
                duration,
                price,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,

            (
                user_id,
                user.username or "ندارد",
                "national",
                "نت سرور ملی",
                f"{volume}GB",
                "طبق سرویس",
                price,
                "pending"
            )
        )

        order_id = cursor.lastrowid

        db.commit()


        new_balance = get_balance(
            user_id
        )


        # پاک کردن اطلاعات موقت
        context.user_data.pop(
            "national_volume",
            None
        )

        context.user_data.pop(
            "national_price",
            None
        )

        context.user_data[
            "waiting_national_volume"
        ] = False


        # اطلاع به ادمین
        try:

            await context.bot.send_message(

                chat_id=ADMIN_ID,

                text=(

                    "🔔 سفارش جدید!\n\n"

                    f"🆔 سفارش: #{order_id}\n"

                    f"👤 کاربر: "
                    f"@{user.username or 'ندارد'}\n"

                    f"🔢 User ID: "
                    f"{user_id}\n\n"

                    "🇮🇷 نت سرور ملی\n"

                    f"📊 حجم: "
                    f"{volume}GB\n"

                    f"💵 هر گیگ: "
                    f"{money(NATIONAL_SERVER_PRICE_PER_GB)}\n"

                    f"💰 مبلغ: "
                    f"{money(price)}\n\n"

                    "💳 پرداخت از کیف پول انجام شد.\n\n"

                    "برای تحویل کد:\n"

                    f"/setconfig "
                    f"{order_id} CODE"
                )
            )

        except Exception as e:

            logger.error(
                f"Admin notification error: {e}"
            )


        # پیام کاربر
        await query.edit_message_text(

            "✅ سفارش با موفقیت ثبت شد!\n\n"

            f"🆔 شماره سفارش: "
            f"#{order_id}\n"

            "🇮🇷 نت سرور ملی\n"

            f"📊 حجم: "
            f"{volume}GB\n"

            f"💰 مبلغ: "
            f"{money(price)}\n\n"

            f"💵 موجودی باقی‌مانده: "
            f"{money(new_balance)}\n\n"

            "⏳ کد کانفیگ پس از "
            "آماده‌شدن برای شما ارسال می‌شود.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "📦 سفارش‌های من",
                        callback_data="orders"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 منوی اصلی",
                        callback_data="home"
                    )
                ]

            ])
        )

        return


    # =====================================================
    # MONTHLY
    # =====================================================

    if data == "monthly":

        await query.edit_message_text(

            "📦 طرح‌های یک ماهه\n\n"
            "طرح موردنظر را انتخاب کنید:",

            reply_markup=monthly_buttons()
        )

        return


    # =====================================================
    # LARGE
    # =====================================================

    if data == "large":

        await query.edit_message_text(

            "🚀 طرح‌های سه ماهه\n\n"
            "طرح موردنظر را انتخاب کنید:",

            reply_markup=large_buttons()
        )

        return


    # =====================================================
    # WALLET
    # =====================================================

    if data == "wallet":

        balance = get_balance(
            user_id
        )

        await query.edit_message_text(

            "💰 کیف پول\n\n"

            f"💵 موجودی شما:\n"
            f"{money(balance)}\n\n"

            "برای شارژ کیف پول "
            "با پشتیبانی تماس بگیرید.",

            reply_markup=wallet_buttons()
        )

        return


    # =====================================================
    # REFERRAL
    # =====================================================

    if data == "referral":

        bot_username = context.bot.username

        referral_link = (
            f"https://t.me/"
            f"{bot_username}"
            f"?start=ref_{user_id}"
        )


        cursor.execute(

            """
            SELECT COUNT(*)
            FROM referrals
            WHERE referrer_id = ?
            """,

            (user_id,)
        )

        count = cursor.fetchone()[0]


        cursor.execute(

            """
            SELECT COALESCE(
                SUM(reward),
                0
            )
            FROM referrals
            WHERE referrer_id = ?
            """,

            (user_id,)
        )

        total = cursor.fetchone()[0]


        await query.edit_message_text(

            "👥 زیرمجموعه‌گیری\n\n"

            f"🎁 پاداش هر نفر: "
            f"{money(REFERRAL_REWARD)}\n\n"

            f"👤 تعداد زیرمجموعه: "
            f"{count}\n"

            f"💰 درآمد از زیرمجموعه‌ها: "
            f"{money(total)}\n\n"

            "🔗 لینک اختصاصی شما:\n"

            f"{referral_link}\n\n"

            "این لینک را برای دوستان "
            "خود ارسال کنید.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "📤 اشتراک لینک",
                        url=(
                            "https://t.me/share/url"
                            f"?url={referral_link}"
                        )
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 برگشت",
                        callback_data="home"
                    )
                ]

            ])
        )

        return


    # =====================================================
    # ORDERS
    # =====================================================

    if data == "orders":

        cursor.execute(

            """
            SELECT
                id,
                plan_name,
                volume,
                duration,
                price,
                status,
                config
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
            """,

            (user_id,)
        )

        orders = cursor.fetchall()


        if not orders:

            await query.edit_message_text(

                "📦 شما هنوز سفارشی ندارید.",

                reply_markup=InlineKeyboardMarkup([

                    [
                        InlineKeyboardButton(
                            "🛒 خرید کانفیگ",
                            callback_data="buy"
                        )
                    ],

                    [
                        InlineKeyboardButton(
                            "🔙 برگشت",
                            callback_data="home"
                        )
                    ]

                ])
            )

            return


        status_names = {

            "pending":
                "⏳ در انتظار تحویل",

            "approved":
                "✅ تکمیل شده",

            "rejected":
                "❌ رد شده"

        }


        text = "📦 سفارش‌های شما:\n\n"


        for order in orders:

            (
                order_id,
                name,
                volume,
                duration,
                price,
                status,
                config
            ) = order


            text += (

                f"🆔 سفارش #{order_id}\n"

                f"📦 {name}\n"

                f"📊 حجم: {volume}\n"

                f"⏱ مدت: {duration}\n"

                f"💰 قیمت: "
                f"{money(price)}\n"

                f"📌 وضعیت: "
                f"{status_names.get(status, status)}\n"
            )


            if config:

                text += (
                    f"\n🔑 کد کانفیگ:\n"
                    f"{config}\n"
                )


            text += (
                "\n────────────\n\n"
            )


        await query.edit_message_text(

            text,

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 برگشت",
                        callback_data="home"
                    )
                ]

            ])
        )

        return


    # =====================================================
    # NORMAL PLAN
    # =====================================================

    if data.startswith("plan_"):

        plan_id = data.split(
            "_",
            1
        )[1]


        if plan_id not in PLANS:

            await query.answer(
                "❌ طرح پیدا نشد.",
                show_alert=True
            )

            return


        plan = PLANS[plan_id]

        price = plan["price"]

        balance = get_balance(
            user_id
        )


        if balance < price:

            needed = (
                price - balance
            )

            await query.edit_message_text(

                "❌ موجودی کیف پول کافی نیست.\n\n"

                f"🔢 کد طرح: {plan_id}\n"

                f"📦 {plan['name']}\n"

                f"📊 حجم: "
                f"{plan['volume']}\n"

                f"⏱ مدت: "
                f"{plan['duration']}\n"

                f"💰 قیمت: "
                f"{money(price)}\n\n"

                f"💵 موجودی: "
                f"{money(balance)}\n"

                f"➕ کمبود: "
                f"{money(needed)}",

                reply_markup=InlineKeyboardMarkup([

                    [
                        InlineKeyboardButton(
                            "➕ شارژ کیف پول",
                            url=SUPPORT_LINK
                        )
                    ],

                    [
                        InlineKeyboardButton(
                            "🔙 برگشت",
                            callback_data="buy"
                        )
                    ]

                ])
            )

            return


        await query.edit_message_text(

            "🛒 تأیید خرید\n\n"

            f"🔢 کد طرح: {plan_id}\n"

            f"📦 {plan['name']}\n"

            f"📊 حجم: "
            f"{plan['volume']}\n"

            f"⏱ مدت: "
            f"{plan['duration']}\n"

            f"💰 قیمت: "
            f"{money(price)}\n\n"

            f"💵 موجودی شما: "
            f"{money(balance)}\n\n"

            "آیا خرید را تأیید می‌کنید؟",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "✅ تأیید خرید",
                        callback_data=(
                            f"buy_confirm_{plan_id}"
                        )
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 برگشت",
                        callback_data="buy"
                    )
                ]

            ])
        )

        return


    # =====================================================
    # NORMAL PLAN CONFIRM
    # =====================================================

    if data.startswith("buy_confirm_"):

        plan_id = data.split(
            "_",
            2
        )[2]


        if plan_id not in PLANS:
            return


        plan = PLANS[plan_id]

        price = plan["price"]


        cursor.execute(

            """
            UPDATE users
            SET balance = balance - ?
            WHERE user_id = ?
            AND balance >= ?
            """,

            (
                price,
                user_id,
                price
            )
        )


        if cursor.rowcount != 1:

            db.rollback()

            await query.answer(
                "❌ موجودی کافی نیست.",
                show_alert=True
            )

            return


        cursor.execute(

            """
            INSERT INTO orders
            (
                user_id,
                username,
                plan_id,
                plan_name,
                volume,
                duration,
                price,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,

            (
                user_id,
                user.username or "ندارد",
                plan_id,
                plan["name"],
                plan["volume"],
                plan["duration"],
                price,
                "pending"
            )
        )


        order_id = cursor.lastrowid

        db.commit()


        new_balance = get_balance(
            user_id
        )


        try:

            await context.bot.send_message(

                chat_id=ADMIN_ID,

                text=(

                    "🔔 سفارش جدید!\n\n"

                    f"🆔 سفارش: #{order_id}\n"

                    f"👤 کاربر: "
                    f"@{user.username or 'ندارد'}\n"

                    f"🔢 User ID: "
                    f"{user_id}\n\n"

                    f"🔢 کد طرح: "
                    f"{plan_id}\n"

                    f"📦 {plan['name']}\n"

                    f"📊 حجم: "
                    f"{plan['volume']}\n"

                    f"⏱ مدت: "
                    f"{plan['duration']}\n"

                    f"💰 مبلغ: "
                    f"{money(price)}\n\n"

                    "💳 پرداخت از کیف پول انجام شد.\n\n"

                    "برای تحویل کد:\n"

                    f"/setconfig "
                    f"{order_id} CODE"
                )
            )

        except Exception as e:

            logger.error(
                f"Admin notification error: {e}"
            )


        await query.edit_message_text(

            "✅ سفارش با موفقیت ثبت شد!\n\n"

            f"🆔 شماره سفارش: "
            f"#{order_id}\n"

            f"🔢 کد طرح: "
            f"{plan_id}\n"

            f"📦 {plan['name']}\n"

            f"📊 حجم: "
            f"{plan['volume']}\n"

            f"⏱ مدت: "
            f"{plan['duration']}\n"

            f"💰 مبلغ: "
            f"{money(price)}\n\n"

            f"💵 موجودی باقی‌مانده: "
            f"{money(new_balance)}\n\n"

            "⏳ کد کانفیگ پس از "
            "آماده‌شدن برای شما ارسال می‌شود.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "📦 سفارش‌های من",
                        callback_data="orders"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🏠 منوی اصلی",
                        callback_data="home"
                    )
                ]

            ])
        )

        return


# =========================================================
# BALANCE COMMAND
# =========================================================

async def balance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    register_user(user)

    balance = get_balance(
        user.id
    )

    await update.message.reply_text(

        "💰 کیف پول شما\n\n"

        f"💵 موجودی: "
        f"{money(balance)}",

        reply_markup=wallet_buttons()
    )


# =========================================================
# ADD BALANCE
# =========================================================

async def add_balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ شما ادمین نیستید."
        )

        return


    if len(context.args) != 2:

        await update.message.reply_text(

            "فرمت صحیح:\n\n"
            "/addbalance USER_ID AMOUNT"
        )

        return


    try:

        target_id = int(
            context.args[0]
        )

        amount = int(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ اطلاعات واردشده صحیح نیست."
        )

        return


    if amount <= 0:

        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )

        return


    cursor.execute(

        """
        INSERT OR IGNORE INTO users
        (user_id, username, balance)
        VALUES (?, ?, 0)
        """,

        (
            target_id,
            "unknown"
        )
    )


    cursor.execute(

        """
        UPDATE users
        SET balance = balance + ?
        WHERE user_id = ?
        """,

        (
            amount,
            target_id
        )
    )


    db.commit()


    new_balance = get_balance(
        target_id
    )


    await update.message.reply_text(

        "✅ موجودی اضافه شد.\n\n"

        f"👤 User ID: "
        f"{target_id}\n"

        f"➕ مبلغ: "
        f"{money(amount)}\n"

        f"💰 موجودی جدید: "
        f"{money(new_balance)}"
    )


    try:

        await context.bot.send_message(

            chat_id=target_id,

            text=(

                "💰 کیف پول شما شارژ شد!\n\n"

                f"➕ مبلغ: "
                f"{money(amount)}\n"

                f"💵 موجودی جدید: "
                f"{money(new_balance)}"
            )
        )

    except Exception as e:

        logger.error(
            f"Balance notification error: {e}"
        )


# =========================================================
# REMOVE BALANCE
# =========================================================

async def remove_balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ شما ادمین نیستید."
        )

        return


    if len(context.args) != 2:

        await update.message.reply_text(
            "/removebalance USER_ID AMOUNT"
        )

        return


    try:

        target_id = int(
            context.args[0]
        )

        amount = int(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ اطلاعات اشتباه است."
        )

        return


    if amount <= 0:

        await update.message.reply_text(
            "❌ مبلغ نامعتبر است."
        )

        return


    balance = get_balance(
        target_id
    )


    if balance < amount:

        await update.message.reply_text(
            "❌ موجودی کاربر کافی نیست."
        )

        return


    cursor.execute(

        """
        UPDATE users
        SET balance = balance - ?
        WHERE user_id = ?
        """,

        (
            amount,
            target_id
        )
    )


    db.commit()


    new_balance = get_balance(
        target_id
    )


    await update.message.reply_text(

        "✅ موجودی کم شد.\n\n"

        f"👤 User ID: "
        f"{target_id}\n"

        f"➖ مبلغ: "
        f"{money(amount)}\n"

        f"💰 موجودی جدید: "
        f"{money(new_balance)}"
    )


# =========================================================
# SET CONFIG
# =========================================================

async def set_config(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ شما ادمین نیستید."
        )

        return


    if len(context.args) < 2:

        await update.message.reply_text(

            "❌ فرمت صحیح:\n\n"

            "/setconfig ORDER_ID CODE\n\n"

            "مثال:\n"

            "/setconfig 25 ABC-123-XYZ"
        )

        return


    try:

        order_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ شماره سفارش نامعتبر است."
        )

        return


    config = " ".join(
        context.args[1:]
    ).strip()


    cursor.execute(

        """
        SELECT
            user_id,
            plan_name
        FROM orders
        WHERE id = ?
        """,

        (order_id,)
    )


    order = cursor.fetchone()


    if not order:

        await update.message.reply_text(
            "❌ سفارش پیدا نشد."
        )

        return


    customer_id, plan_name = order


    cursor.execute(

        """
        UPDATE orders
        SET
            config = ?,
            status = 'approved'
        WHERE id = ?
        """,

        (
            config,
            order_id
        )
    )


    db.commit()


    await update.message.reply_text(

        "✅ کد ثبت شد.\n\n"

        f"🆔 سفارش: #{order_id}\n"

        f"📦 {plan_name}\n"

        f"🔑 کد:\n{config}"
    )


    try:

        await context.bot.send_message(

            chat_id=customer_id,

            text=(

                "🎉 کانفیگ شما آماده شد!\n\n"

                f"🆔 سفارش: #{order_id}\n"

                f"📦 {plan_name}\n\n"

                "🔑 کد کانفیگ:\n"

                f"{config}\n\n"

                "✅ وضعیت سفارش: تکمیل شده"
            )
        )

    except Exception as e:

        logger.error(
            f"Could not send config: {e}"
        )


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:

        print(
            "❌ BOT_TOKEN تنظیم نشده است."
        )

        return


    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    # Commands

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "balance",
            balance_command
        )
    )

    app.add_handler(
        CommandHandler(
            "addbalance",
            add_balance
        )
    )

    app.add_handler(
        CommandHandler(
            "removebalance",
            remove_balance
        )
    )

    app.add_handler(
        CommandHandler(
            "setconfig",
            set_config
        )
    )


    # Text messages
    # برای گرفتن حجم نت سرور ملی

    app.add_handler(

        MessageHandler(

            filters.TEXT &
            ~filters.COMMAND,

            national_server_volume
        )
    )


    # Buttons

    app.add_handler(

        CallbackQueryHandler(
            callback_handler
        )
    )


    print(
        "🤖 BOT IS RUNNING"
    )

    print(

        "🇮🇷 National Server: "

        f"{money(NATIONAL_SERVER_PRICE_PER_GB)} "

        "/ GB"
    )


    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()