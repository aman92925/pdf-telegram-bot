import logging, json, os, io, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from PIL import Image

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATA_FILE = "users_data.json"

DEFAULT_USER = {
    "plan": "FREE",
    "invites": 0,
    "invited_users": [],
    "lang": "en",
    "photos": []
}

LANGS = {
    "en": {
        "welcome": "🚀 **Welcome to PDF Converter Bot!**\n\nSend me photos to create a PDF.\n\n📌 **Plan:** {plan}\n🔗 **Your Invite Link:** {link}\n👥 **Invites:** {invites}/3\n\n*Invite 3 friends to get VIP PRO Plan (Up to 50 photos per PDF)!*",
        "set_lang": "🌐 Choose your preferred language category:",
        "lang_changed": "✅ Language updated successfully!",
        "photo_added": "📸 Photo received ({count}/{max_photos}). Send more or click **Make PDF**.",
        "limit_reached": "⚠️ Limit reached for {plan} plan ({max_photos} photos max).\n\nUpgrade to **PRO** by inviting 3 friends!",
        "no_photos": "❌ No photos uploaded yet!",
        "pdf_creating": "⏳ Creating your PDF...",
        "pdf_success": "✅ **Here is your PDF!**",
        "name_prompt": "✏️ Send me the name for your PDF file:",
        "name_saved": "✅ File name set to: `{name}.pdf`"
    },
    "hi": {
        "welcome": "🚀 **PDF Converter Bot mein aapka swagat hai!**\n\nPDF banane ke liye photos bhejein.\n\n📌 **Plan:** {plan}\n🔗 **Aapka Invite Link:** {link}\n👥 **Invites:** {invites}/3\n\n*VIP PRO Plan paane ke liye 3 doston ko invite karein!*",
        "set_lang": "🌐 Apni bhasha ki category chunein:",
        "lang_changed": "✅ Bhasha safalpurvak badal di gayi hai!",
        "photo_added": "📸 Photo mil gayi ({count}/{max_photos}). Aur bhejein ya **Make PDF** par click karein.",
        "limit_reached": "⚠️ {plan} plan ki limit poori ho gayi ({max_photos} photos max).\n\n3 doston ko invite karke **PRO** plan lein!",
        "no_photos": "❌ Abhi tak koi photo nahi bheji!",
        "pdf_creating": "⏳ Aapki PDF ban rahi hai...",
        "pdf_success": "✅ **Yeh rahi aapki PDF!**",
        "name_prompt": "✏️ Apni PDF file ka naam likh kar bhejein:",
        "name_saved": "✅ File name set ho gaya: `{name}.pdf`"
    },
    "bho": {
        "welcome": "🚀 **PDF Converter Bot me raua sabhe ke swagat ba!**\n\nPDF banave khatir photo bheji.\n\n📌 **Plan:** {plan}\n🔗 **Aapank Link:** {link}\n👥 **Invites:** {invites}/3",
        "set_lang": "🌐 Bhasha chuniye:", "lang_changed": "✅ Bhasha badal gail ba!", "photo_added": "📸 Photo mil gail ({count}/{max_photos}).", "limit_reached": "⚠️ Limit poora ho gail!", "no_photos": "❌ Ekko photo naikhe!", "pdf_creating": "⏳ PDF banta...", "pdf_success": "✅ Raur PDF aagail!", "name_prompt": "✏️ PDF ke naam likhi:", "name_saved": "✅ Naam set ho gail: `{name}.pdf`"
    },
    "ml": {
        "welcome": "🚀 **PDF Converter Bot-lekku swagatham!**\n\nPDF undakkan photos ayakkuka.\n\n📌 **Plan:** {plan}\n🔗 **Link:** {link}\n👥 **Invites:** {invites}/3",
        "set_lang": "🌐 Bhasha thiranjedukkuka:", "lang_changed": "✅ Bhasha maatti!", "photo_added": "📸 Photo kittiyittu ({count}/{max_photos}).", "limit_reached": "⚠️ Limit kazhinju!", "no_photos": "❌ Photos onnum illa!", "pdf_creating": "⏳ PDF undakkunnu...", "pdf_success": "✅ Ningalude PDF!", "name_prompt": "✏️ PDF peru ayakkuka:", "name_saved": "✅ Peru set aayi: `{name}.pdf`"
    },
    "bn": { "welcome": "🚀 **PDF Converter Bot-e apnake swagatam!**\n\nPDF toiri korte chhobi pathan." },
    "te": { "welcome": "🚀 **PDF Converter Bot ki swagatam!**\n\nPDF tayaru cheyadaniki photos pampandi." },
    "mr": { "welcome": "🚀 **PDF Converter Bot madhe swagat aahe!**\n\nPDF banavnyasathi photo pathva." },
    "ta": { "welcome": "🚀 **PDF Converter Bot-ku nalvaravu!**\n\nPDF thayaarikka photos anuppungal." },
    "gu": { "welcome": "🚀 **PDF Converter Bot ma swagat chhe!**\n\nPDF banava mate photos moklo." },
    "ur": { "welcome": "🚀 **PDF Converter Bot mein khush amdeed!**\n\nPDF banane ke liye tasaveer bhejein." },
    "kn": { "welcome": "🚀 **PDF Converter Bot ge swagatha!**\n\nPDF madalu photos kalsi." },
    "pa": { "welcome": "🚀 **PDF Converter Bot vich swagat hai!**\n\nPDF baman layi photos bhejo." },
    "es": { "welcome": "🚀 ¡Bienvenido a PDF Converter Bot!" },
    "fr": { "welcome": "🚀 Bienvenue sur PDF Converter Bot!" },
    "de": { "welcome": "🚀 Willkommen beim PDF Converter Bot!" },
    "pt": { "welcome": "🚀 Bem-vindo ao PDF Converter Bot!" },
    "ru": { "welcome": "🚀 Добро пожаловать в PDF Converter Bot!" },
    "ja": { "welcome": "🚀 PDF Converter Botへようこそ！" },
    "ko": { "welcome": "🚀 PDF Converter Bot에 오신 것을 환영합니다!" },
    "tr": { "welcome": "🚀 PDF Converter Bot'a hoş geldiniz!" },
    "vi": { "welcome": "🚀 Chào mừng đến với PDF Converter Bot!" },
    "ar": { "welcome": "🚀 أهلاً بك في بوت تحويل الصور إلى PDF!" }
}

USER_PDF_NAMES = {}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(chat_id):
    data = load_data()
    if chat_id not in data:
        data[chat_id] = json.loads(json.dumps(DEFAULT_USER))
        save_data(data)
    return data[chat_id], data

def get_text(chat_id, key):
    usr, _ = get_user(chat_id)
    lang = usr.get("lang", "en")
    if lang not in LANGS: lang = "en"
    return LANGS[lang].get(key, LANGS["en"].get(key, ""))

async def adminvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if update.effective_user.id != ADMIN_ID and chat_id != str(ADMIN_ID):
        await update.message.reply_text("⛔ Admin only command!")
        return

    data = load_data()
    if context.args:
        target_id = context.args[0].strip()
        if target_id not in data:
            data[target_id] = json.loads(json.dumps(DEFAULT_USER))
        data[target_id]["plan"] = "PRO"
        save_data(data)
        await update.message.reply_text(f"👑 **SUCCESS:** User `{target_id}` ko VIP PRO de diya gaya hai!", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=int(target_id), text="🎉 **Congratulations!** Admin ne aapka **VIP PRO** plan active kar diya hai! 🚀")
        except Exception:
            pass
    else:
        usr, _ = get_user(chat_id)
        usr["plan"] = "PRO"
        save_data(data)
        await update.message.reply_text("👑 **ADMIN PRIVILEGE:** Aapka apna VIP PRO Unlock ho gaya hai!")

async def vip_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    usr, _ = get_user(chat_id)
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{chat_id}"
    plan_status = "👑 VIP PRO Plan" if usr.get("plan") == "PRO" else "🆓 Free Plan"
    msg = f"📊 **Aapka Account Status:**\n\n📌 **Current Plan:** {plan_status}\n👥 **Total Invites:** {usr.get('invites', 0)}/3\n🔗 **Referral Link:** {link}"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    usr, data = get_user(chat_id)
    bot_username = (await context.bot.get_me()).username

    if update.effective_user.id == ADMIN_ID:
        usr["plan"] = "PRO"
        save_data(data)

    if context.args and context.args[0].startswith("ref_"):
        referrer_id = context.args[0].replace("ref_", "")
        if referrer_id in data and referrer_id != chat_id:
            ref_usr = data[referrer_id]
            if chat_id not in ref_usr.get("invited_users", []):
                ref_usr.setdefault("invited_users", []).append(chat_id)
                ref_usr["invites"] = len(ref_usr["invited_users"])
                if ref_usr["invites"] >= 3:
                    ref_usr["plan"] = "PRO"
                save_data(data)

    link = f"https://t.me/{bot_username}?start=ref_{chat_id}"
    msg = get_text(chat_id, "welcome").format(
        plan=usr["plan"], link=link, invites=usr.get("invites", 0)
    )
    
    keyboard = [
        [InlineKeyboardButton("📄 Make PDF", callback_data="make_pdf"),
         InlineKeyboardButton("🗑️ Clear Photos", callback_data="clear")],
        [InlineKeyboardButton("🌐 Change Language", callback_data="set_lang"),
         InlineKeyboardButton("✏️ Set File Name", callback_data="set_name")]
    ]
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    usr, data = get_user(chat_id)
    max_photos = 50 if usr["plan"] == "PRO" else 10
    photos = usr.get("photos", [])

    if len(photos) >= max_photos:
        await update.message.reply_text(get_text(chat_id, "limit_reached").format(plan=usr["plan"], max_photos=max_photos), parse_mode="Markdown")
        return

    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    usr.setdefault("photos", []).append(photo_bytes.hex())
    save_data(data)

    msg = get_text(chat_id, "photo_added").format(count=len(usr["photos"]), max_photos=max_photos)
    keyboard = [[InlineKeyboardButton("📄 Make PDF Now", callback_data="make_pdf")]]
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if doc.mime_type and doc.mime_type.startswith("image/"):
        chat_id = str(update.effective_chat.id)
        usr, data = get_user(chat_id)
        max_photos = 50 if usr["plan"] == "PRO" else 10
        photos = usr.get("photos", [])

        if len(photos) >= max_photos:
            await update.message.reply_text(get_text(chat_id, "limit_reached").format(plan=usr["plan"], max_photos=max_photos), parse_mode="Markdown")
            return

        doc_file = await doc.get_file()
        photo_bytes = await doc_file.download_as_bytearray()
        usr.setdefault("photos", []).append(photo_bytes.hex())
        save_data(data)

        msg = get_text(chat_id, "photo_added").format(count=len(usr["photos"]), max_photos=max_photos)
        keyboard = [[InlineKeyboardButton("📄 Make PDF Now", callback_data="make_pdf")]]
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = str(query.message.chat.id)
    usr, data = get_user(chat_id)

    if query.data == "clear":
        usr["photos"] = []
        save_data(data)
        await query.edit_message_text("🗑️ All photos cleared!")

    elif query.data == "set_lang":
        keyboard = [
            [InlineKeyboardButton("🇮🇳 Indian Languages", callback_data="cat_indian"),
             InlineKeyboardButton("🌍 International Languages", callback_data="cat_intl")]
        ]
        await query.edit_message_text("🌐 Choose a language category / भाषा श्रेणी चुनें:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "cat_indian":
        keyboard = [
            [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"), InlineKeyboardButton("हिन्दी 🇮🇳", callback_data="lang_hi")],
            [InlineKeyboardButton("भोजपुरी 🇮🇳", callback_data="lang_bho"), InlineKeyboardButton("മലയാളം 🇮🇳", callback_data="lang_ml")],
            [InlineKeyboardButton("বাংলা 🇧🇩", callback_data="lang_bn"), InlineKeyboardButton("తెలుగు 🇮🇳", callback_data="lang_te")],
            [InlineKeyboardButton("मराठी 🇮🇳", callback_data="lang_mr"), InlineKeyboardButton("தமிழ் 🇮🇳", callback_data="lang_ta")],
            [InlineKeyboardButton("ગુજરાતી 🇮🇳", callback_data="lang_gu"), InlineKeyboardButton("اردو 🇵🇰", callback_data="lang_ur")],
            [InlineKeyboardButton("ಕನ್ನಡ 🇮🇳", callback_data="lang_kn"), InlineKeyboardButton("ਪੰਜਾਬੀ 🇮🇳", callback_data="lang_pa")],
            [InlineKeyboardButton("⬅️ Back", callback_data="set_lang")]
        ]
        await query.edit_message_text("🇮🇳 Select Indian Language:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "cat_intl":
        keyboard = [
            [InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es"), InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr")],
            [InlineKeyboardButton("Deutsch 🇩🇪", callback_data="lang_de"), InlineKeyboardButton("Português 🇧🇷", callback_data="lang_pt")],
            [InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"), InlineKeyboardButton("日本語 🇯🇵", callback_data="lang_ja")],
            [InlineKeyboardButton("한국어 🇰🇷", callback_data="lang_ko"), InlineKeyboardButton("Türkçe 🇹🇷", callback_data="lang_tr")],
            [InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="lang_vi"), InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")],
            [InlineKeyboardButton("⬅️ Back", callback_data="set_lang")]
        ]
        await query.edit_message_text("🌍 Select International Language:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("lang_"):
        lang_code = query.data.split("_")[1]
        usr["lang"] = lang_code
        save_data(data)
        await query.edit_message_text("✅ Language updated successfully!")

    elif query.data == "set_name":
        await query.edit_message_text(get_text(chat_id, "name_prompt"))

    elif query.data == "make_pdf":
        photos = usr.get("photos", [])
        if not photos:
            await query.edit_message_text(get_text(chat_id, "no_photos"))
            return

        status_msg = await query.edit_message_text(get_text(chat_id, "pdf_creating"))
        images_list = []
        raw_buffers = [bytes.fromhex(p) for p in photos]
        filename = USER_PDF_NAMES.pop(chat_id, "Converted_Document")

        for buf in raw_buffers:
            img = Image.open(io.BytesIO(buf))
            if img.mode != 'RGB': img = img.convert('RGB')
            images_list.append(img)

        if images_list:
            pdf_bytes = io.BytesIO()
            images_list[0].save(pdf_bytes, format="PDF", save_all=True, append_images=images_list[1:])
            pdf_bytes.seek(0)
            try: await status_msg.delete()
            except: pass

            usr["photos"] = []
            save_data(data)

            await context.bot.send_document(
                chat_id=int(chat_id),
                document=InputFile(pdf_bytes, filename=f"{filename}.pdf"),
                caption=get_text(chat_id, "pdf_success"),
                parse_mode="Markdown"
            )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip()
    if not text.startswith("/"):
        USER_PDF_NAMES[chat_id] = text
        await update.message.reply_text(get_text(chat_id, "name_saved").format(name=text), parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adminvip", adminvip))
    app.add_handler(CommandHandler("vip", vip_status))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
