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
    "photos": [],
    "custom_name": ""
}

LANGS = {
    "en": {
        "welcome": "🚀 **Welcome to PDF Converter Bot!**\n\nSend me photos to create a PDF.\n\n📌 **Plan:** {plan}\n🔗 **Your Invite Link:** {link}\n👥 **Invites:** {invites}/3\n\n*Invite 3 friends to get VIP PRO Plan (Up to 50 photos per PDF)!*",
        "set_lang": "🌐 Choose your language:",
        "lang_changed": "✅ Language updated to English!",
        "photo_added": "📸 Photo received ({count}/{max_photos}). Send more photos or click **Make PDF**.",
        "limit_reached": "⚠️ Limit reached for {plan} plan ({max_photos} photos max).\n\nUpgrade to **PRO** by inviting 3 friends!",
        "no_photos": "❌ No photos uploaded yet! Please send photos first.",
        "pdf_creating": "⏳ Creating your PDF, please wait...",
        "pdf_success": "✅ **Here is your PDF document!**",
        "name_prompt": "✏️ Send me the name for your PDF or type `/rename MyFileName`:",
        "name_saved": "✅ PDF File Name set to: `{name}.pdf`",
        "photos_cleared": "🗑️ All uploaded photos have been cleared!",
        "help_text": "❓ **How to Use this Bot:**\n\n1️⃣ Send photos one by one or all together.\n2️⃣ Use `/rename MyDocument` to set custom PDF file name.\n3️⃣ Click **Make PDF** button to download your document.\n4️⃣ Click **Clear Photos** to delete uploaded images.\n\n📌 **Available Commands:**\n/start - Show Main Menu\n/help - Show Detailed Usage Instructions\n/languages - Change Bot Language\n/rename <name> - Rename Your PDF File\n/vip - Check Plan & Referral Status",
        "btn_make": "📄 Make PDF", "btn_clear": "🗑️ Clear Photos", "btn_lang": "🌐 Change Language", "btn_name": "✏️ Rename PDF"
    },
    "hi": {
        "welcome": "🚀 **PDF Converter Bot mein aapka swagat hai!**\n\nPDF banane ke liye photos bhejein.\n\n📌 **Plan:** {plan}\n🔗 **Aapka Invite Link:** {link}\n👥 **Invites:** {invites}/3\n\n*VIP PRO Plan paane ke liye 3 doston ko invite karein!*",
        "set_lang": "🌐 Apni bhasha chunein:",
        "lang_changed": "✅ Bhasha Hindi set ho gayi hai!",
        "photo_added": "📸 Photo mil gayi ({count}/{max_photos}). Aur bhejein ya **Make PDF** par click karein.",
        "limit_reached": "⚠️ {plan} plan ki limit poori ho gayi ({max_photos} photos max).\n\n3 doston ko invite karke **PRO** plan lein!",
        "no_photos": "❌ Abhi tak koi photo nahi bheji!",
        "pdf_creating": "⏳ Aapki PDF ban rahi hai...",
        "pdf_success": "✅ **Yeh rahi aapki PDF document!**",
        "name_prompt": "✏️ Apni PDF file ka naam likh kar bhejein ya `/rename NayaNaam` command dein:",
        "name_saved": "✅ File name set ho gaya: `{name}.pdf`",
        "photos_cleared": "🗑️ Saari photos delete kar di gayi hain!",
        "help_text": "❓ **Bot ko istemaal karne ka tareeka:**\n\n1️⃣ Bot ko ek ya ek se zyada photos bhejein.\n2️⃣ PDF ka naam badalne ke liye `/rename NayaNaam` likhein ya **Rename PDF** button par tap karein.\n3️⃣ **Make PDF** button par click karke PDF download karein.\n4️⃣ Purani photos hatane ke liye **Clear Photos** par tap karein.\n\n📌 **Mukhya Commands:**\n/start - Main Menu kholne ke liye\n/help - Bot chalane ki poori jankari\n/languages - Bhasha badalne ke liye\n/rename <naam> - PDF File Name change karne ke liye\n/vip - VIP Status aur Invites check karne ke liye",
        "btn_make": "📄 PDF Banayein", "btn_clear": "🗑️ Photos Hataayein", "btn_lang": "🌐 Bhasha Badaleyn", "btn_name": "✏️ Rename PDF"
    },
    "hinglish": {
        "welcome": "🚀 **PDF Converter Bot mein welcome hai!**\n\nPDF banane ke liye photos bhejo.\n\n📌 **Plan:** {plan}\n🔗 **Invite Link:** {link}\n👥 **Invites:** {invites}/3",
        "set_lang": "🌐 Apni language select karo:",
        "lang_changed": "✅ Language Hinglish set ho gayi hai!",
        "photo_added": "📸 Photo mil gayi ({count}/{max_photos}). Aur bhejo ya **Make PDF** dabao.",
        "limit_reached": "⚠️ {plan} plan ki limit khatam ho gayi ({max_photos} photos max).",
        "no_photos": "❌ Koi photo nahi bheji abhi tak!",
        "pdf_creating": "⏳ PDF ban rahi hai, thoda wait karo...",
        "pdf_success": "✅ **Yeh rahi aapki PDF!**",
        "name_prompt": "✏️ PDF ka naam bhejo ya `/rename MyName` likho:",
        "name_saved": "✅ File name set ho gaya: `{name}.pdf`",
        "photos_cleared": "🗑️ Saari photos clear ho gayi hain!",
        "help_text": "❓ **Bot use karne ka tarika:**\n\n1️⃣ Pehle photos send karo.\n2️⃣ Rename karne ke liye `/rename MyFileName` command use karo.\n3️⃣ **Make PDF** dabakar PDF download karo.\n4️⃣ Photos clear karne ke liye **Clear Photos** dabao.\n\n📌 **Commands:**\n/start - Main Menu\n/help - Usage Guide\n/languages - Change Language\n/rename <name> - Rename PDF File\n/vip - Check VIP Status",
        "btn_make": "📄 Make PDF", "btn_clear": "🗑️ Clear Photos", "btn_lang": "🌐 Change Language", "btn_name": "✏️ Rename PDF"
    },
    "ta": {
        "welcome": "🚀 **PDF Converter Bot-ku nalvaravu!**", "set_lang": "🌐 Mozhiyai therndhedungal:",
        "lang_changed": "✅ Mozhi maatram seyyappattathu!", "photo_added": "📸 Photo vanthathu ({count}/{max_photos}).",
        "limit_reached": "⚠️ Limit mudinthathu!", "no_photos": "❌ Photos illai!", "pdf_creating": "⏳ PDF thayaarakirathu...",
        "pdf_success": "✅ Ungal PDF!", "name_prompt": "✏️ PDF peyarai `/rename Peyar` anuppungal:",
        "name_saved": "✅ Peyar set: `{name}.pdf`", "photos_cleared": "🗑️ Photos neekkappattana!",
        "help_text": "❓ **Payanpaduthuvathu:**\n1️⃣ Photos anuppungal.\n2️⃣ `/rename Peyar` use seyyungal.\n3️⃣ **Make PDF** click seyyungal.",
        "btn_make": "📄 Make PDF", "btn_clear": "🗑️ Clear Photos", "btn_lang": "🌐 Language", "btn_name": "✏️ Rename PDF"
    },
    "te": {
        "welcome": "🚀 **PDF Converter Bot ki swagatam!**", "set_lang": "🌐 Bhasha enchukondi:",
        "lang_changed": "✅ Bhasha marpabadindi!", "photo_added": "📸 Photo andindi ({count}/{max_photos}).",
        "limit_reached": "⚠️ Limit mugisindi!", "no_photos": "❌ Photos levu!", "pdf_creating": "⏳ PDF tayaravtundi...",
        "pdf_success": "✅ Idi mee PDF!", "name_prompt": "✏️ PDF peru `/rename Peru` pampandi:",
        "name_saved": "✅ Peru set: `{name}.pdf`", "photos_cleared": "🗑️ Photos tholaginchabaddayi!",
        "help_text": "❓ **Upayoginchali:**\n1️⃣ Photos pampandi.\n2️⃣ `/rename Peru` upayoginchandi.\n3️⃣ **Make PDF** click cheyandi.",
        "btn_make": "📄 Make PDF", "btn_clear": "🗑️ Clear Photos", "btn_lang": "🌐 Language", "btn_name": "✏️ Rename PDF"
    },
    "bho": {
        "welcome": "🚀 **PDF Converter Bot me raua sabhe ke swagat ba!**", "set_lang": "🌐 Bhasha chuniye:",
        "lang_changed": "✅ Bhasha badal gail ba!", "photo_added": "📸 Photo mil gail ({count}/{max_photos}).",
        "limit_reached": "⚠️ Limit poora ho gail!", "no_photos": "❌ Ekko photo naikhe!", "pdf_creating": "⏳ Raur PDF banta...",
        "pdf_success": "✅ **Yeh raur PDF ba!**", "name_prompt": "✏️ PDF ke naam `/rename Naam` likhi:",
        "name_saved": "✅ Naam set: `{name}.pdf`", "photos_cleared": "🗑️ Sab photo hata dihal gail!",
        "help_text": "❓ **Kaise use kare ke ba:**\n1️⃣ Photo bheji.\n2️⃣ `/rename Naam` se naam badli.\n3️⃣ **Make PDF** dabai.",
        "btn_make": "📄 PDF Banai", "btn_clear": "🗑️ Photo Hatai", "btn_lang": "🌐 Bhasha Badli", "btn_name": "✏️ Rename PDF"
    },
    "ur": {
        "welcome": "🚀 **PDF Converter Bot mein khush amdeed!**", "set_lang": "🌐 Zaban muntakhib karein:",
        "lang_changed": "✅ Zaban tabdeel ho gayi hai!", "photo_added": "📸 Tasaveer mil gayi hai.",
        "limit_reached": "⚠️ Limit poori ho chuki hai!", "no_photos": "❌ Koi tasveer nahi mili!", "pdf_creating": "⏳ PDF ban rahi hai...",
        "pdf_success": "✅ Yeh rahi aapki PDF!", "name_prompt": "✏️ PDF ka naam `/rename Naam` likhein:",
        "name_saved": "✅ Naam set ho gaya.", "photos_cleared": "🗑️ Tasaveer khatam kar di gayi hain!",
        "help_text": "❓ **Istemal ka tarika:**\n1️⃣ Tasaveer bhejein.\n2️⃣ `/rename Naam` istemal karein.\n3️⃣ **Make PDF** dabayein.",
        "btn_make": "📄 PDF Banayein", "btn_clear": "🗑️ Photos Hataayein", "btn_lang": "🌐 Zaban Badlein", "btn_name": "✏️ Rename PDF"
    },
    "es": {
        "welcome": "🚀 ¡Bienvenido a PDF Converter Bot!", "set_lang": "🌐 Elige tu idioma:",
        "lang_changed": "✅ ¡Idioma actualizado!", "photo_added": "📸 Foto recibida.",
        "limit_reached": "⚠️ ¡Límite alcanzado!", "no_photos": "❌ ¡No hay fotos!", "pdf_creating": "⏳ Creando PDF...",
        "pdf_success": "✅ ¡Aquí está tu PDF!", "name_prompt": "✏️ Envía `/rename Nombre`:",
        "name_saved": "✅ Nombre guardado.", "photos_cleared": "🗑️ ¡Fotos borradas!",
        "help_text": "❓ **Cómo usar:**\n1️⃣ Envía fotos.\n2️⃣ Usa `/rename Nombre`.\n3️⃣ Toca **Make PDF**.",
        "btn_make": "📄 Crear PDF", "btn_clear": "🗑️ Borrar Fotos", "btn_lang": "🌐 Idioma", "btn_name": "✏️ Cambiar Nombre"
    },
    "ru": {
        "welcome": "🚀 Добро пожаловать в PDF Converter Bot!", "set_lang": "🌐 Выберите язык:",
        "lang_changed": "✅ Язык изменен!", "photo_added": "📸 Фото получено.",
        "limit_reached": "⚠️ Лимит исчерпан!", "no_photos": "❌ Нет фото!", "pdf_creating": "⏳ Создание PDF...",
        "pdf_success": "✅ Ваш PDF готов!", "name_prompt": "✏️ Введите `/rename Имя`:",
        "name_saved": "✅ Имя сохранено.", "photos_cleared": "🗑️ Все фото удалены!",
        "help_text": "❓ **Как использовать:**\n1️⃣ Отправьте фото.\n2️⃣ Используйте `/rename Имя`.\n3️⃣ Нажмите **Make PDF**.",
        "btn_make": "📄 Создать PDF", "btn_clear": "🗑️ Очистить", "btn_lang": "🌐 Язык", "btn_name": "✏️ Переименовать"
    },
    "ar": {
        "welcome": "🚀 أهلاً بك في بوت تحويل الصور إلى PDF!", "set_lang": "🌐 اختر لغتك:",
        "lang_changed": "✅ تم تحديث اللغة!", "photo_added": "📸 تم استلام الصورة.",
        "limit_reached": "⚠️ تم الوصول للحد الأقصى!", "no_photos": "❌ لا توجد صور!", "pdf_creating": "⏳ جاري إنشاء الـ PDF...",
        "pdf_success": "✅ إليك ملف الـ PDF الخاص بك!", "name_prompt": "✏️ أرسل `/rename الاسم`:",
        "name_saved": "✅ تم حفظ الاسم.", "photos_cleared": "🗑️ تم مسح جميع الصور!",
        "help_text": "❓ **طريقة الاستخدام:**\n1️⃣ أرسل الصور.\n2️⃣ استخدم `/rename الاسم`.\n3️⃣ اضغط **Make PDF**.",
        "btn_make": "📄 إنشاء PDF", "btn_clear": "🗑️ مسح الصور", "btn_lang": "🌐 اللغة", "btn_name": "✏️ إعادة تسمية"
    }
}

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

def get_main_keyboard(chat_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(chat_id, "btn_make"), callback_data="make_pdf"),
         InlineKeyboardButton(get_text(chat_id, "btn_clear"), callback_data="clear")],
        [InlineKeyboardButton(get_text(chat_id, "btn_lang"), callback_data="set_lang"),
         InlineKeyboardButton(get_text(chat_id, "btn_name"), callback_data="set_name")]
    ])

def get_language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"), InlineKeyboardButton("Hindi 🇮🇳", callback_data="lang_hi")],
        [InlineKeyboardButton("Hinglish 💬", callback_data="lang_hinglish"), InlineKeyboardButton("Tamil 🇮🇳", callback_data="lang_ta")],
        [InlineKeyboardButton("Telugu 🇮🇳", callback_data="lang_te"), InlineKeyboardButton("Bhojpuri 🇮🇳", callback_data="lang_bho")],
        [InlineKeyboardButton("Urdu 💬", callback_data="lang_ur"), InlineKeyboardButton("Spanish 🇪🇸", callback_data="lang_es")],
        [InlineKeyboardButton("Russian 🇷🇺", callback_data="lang_ru"), InlineKeyboardButton("Arabic 🇸🇦", callback_data="lang_ar")]
    ])

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
    msg = f"📊 **Account Status:**\n\n📌 **Plan:** {plan_status}\n👥 **Invites:** {usr.get('invites', 0)}/3\n🔗 **Referral Link:** {link}"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await update.message.reply_text(get_text(chat_id, "help_text"), parse_mode="Markdown")

async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await update.message.reply_text(get_text(chat_id, "set_lang"), reply_markup=get_language_keyboard())

async def rename_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    usr, data = get_user(chat_id)
    if context.args:
        new_name = " ".join(context.args).strip()
        usr["custom_name"] = new_name
        save_data(data)
        await update.message.reply_text(get_text(chat_id, "name_saved").format(name=new_name), parse_mode="Markdown", reply_markup=get_main_keyboard(chat_id))
    else:
        await update.message.reply_text("⚠️ Usage: `/rename MyFileName`", parse_mode="Markdown")

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
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(chat_id))

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
    keyboard = [[InlineKeyboardButton(get_text(chat_id, "btn_make"), callback_data="make_pdf")]]
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
        keyboard = [[InlineKeyboardButton(get_text(chat_id, "btn_make"), callback_data="make_pdf")]]
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat.id)
    usr, data = get_user(chat_id)

    if query.data == "clear":
        usr["photos"] = []
        save_data(data)
        await query.answer(get_text(chat_id, "photos_cleared"), show_alert=True)
        try:
            await query.edit_message_text(get_text(chat_id, "photos_cleared"), reply_markup=get_main_keyboard(chat_id))
        except Exception:
            pass

    elif query.data == "set_lang":
        await query.answer()
        await query.edit_message_text(get_text(chat_id, "set_lang"), reply_markup=get_language_keyboard())

    elif query.data.startswith("lang_"):
        lang_code = query.data.split("_")[1]
        usr["lang"] = lang_code
        save_data(data)
        await query.answer(get_text(chat_id, "lang_changed"), show_alert=True)
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=ref_{chat_id}"
        msg = get_text(chat_id, "welcome").format(plan=usr["plan"], link=link, invites=usr.get("invites", 0))
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(chat_id))

    elif query.data == "set_name":
        await query.answer()
        await query.edit_message_text(get_text(chat_id, "name_prompt"), parse_mode="Markdown")

    elif query.data == "make_pdf":
        await query.answer()
        photos = usr.get("photos", [])
        if not photos:
            await query.edit_message_text(get_text(chat_id, "no_photos"), reply_markup=get_main_keyboard(chat_id))
            return

        status_msg = await query.edit_message_text(get_text(chat_id, "pdf_creating"))
        images_list = []
        raw_buffers = [bytes.fromhex(p) for p in photos]
        
        filename = usr.get("custom_name") or "Converted_Document"

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
            usr["custom_name"] = ""
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
        usr, data = get_user(chat_id)
        usr["custom_name"] = text
        save_data(data)
        await update.message.reply_text(get_text(chat_id, "name_saved").format(name=text), parse_mode="Markdown", reply_markup=get_main_keyboard(chat_id))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("languages", languages_command))
    app.add_handler(CommandHandler("rename", rename_command))
    app.add_handler(CommandHandler("adminvip", adminvip))
    app.add_handler(CommandHandler("vip", vip_status))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
