import logging, json, os, io, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from PIL import Image

TOKEN = os.getenv("TOKEN", "8822091309:AAErFSkNRoPPWfORXKK2o7Fas41_vml20fQ")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7476309567"))
DATA_FILE = "pdf_user_data.json"

DEFAULT_USER = {
    "referrals": 0,
    "referred_by": None,
    "plan": "FREE",
    "lang": "en"
}

USER_PHOTO_BUFFERS = {}
USER_PDF_NAMES = {}
USER_PENDING_DOCS = {}

LANGS = {
    "en": {
        "status_pro": "👑 VIP PRO UNLOCKED (Limit: 50 Photos)",
        "status_free": "🔓 FREE PLAN (Limit: 10 Photos)",
        "welcome": "📄 **PDF MASTER & EDITOR PRO**\n\n🏷️ Status: **{status}**\n👥 Invites: **{refs}/3 Friends**\n\n📸 **Photo to PDF:** Send photos to convert!\n🔄 **Rename PDF:** Send any PDF to rename!\n\n🔗 **Your Invite Link:**\n`{ref_link}`",
        "btn_share": "🎁 Share & Unlock VIP",
        "btn_tools": "🔒 Advanced Tools",
        "btn_lang": "🌐 Change Language",
        "added_photo": "📥 **Photo Added!** ({curr}/{max})\n📄 Name: `{name}.pdf`",
        "pdf_success": "✅ **PDF Created Successfully!**\n📄 Name: `{filename}`",
        "help_msg": "🛠️ **PDF BOT GUIDE:**\n1. Send Photos to convert into PDF.\n2. Use `/name MyFile` to set custom name.\n3. Send existing PDF file to rename it.\n4. Type `/vip` to check your status."
    },
    "hi": {
        "status_pro": "👑 VIP प्रो अनलॉक (सीमा: 50 फोटो)",
        "status_free": "🔓 फ्री प्लान (सीमा: 10 फोटो)",
        "welcome": "📄 **पीडीएफ मास्टर एंड एडिटर प्रो**\n\n🏷️ स्थिति: **{status}**\n👥 आमंत्रण: **{refs}/3 मित्र**\n\n📸 **फोटो से पीडीएफ:** फोटो भेजें और पीडीएफ पाएं!\n🔄 **नाम बदलें:** कोई भी पीडीएफ भेजकर नाम बदलें!\n\n🔗 **आपका लिंक:**\n`{ref_link}`",
        "btn_share": "🎁 शेयर और वीआईपी पाएं",
        "btn_tools": "🔒 एडवांस टूल",
        "btn_lang": "🌐 भाषा बदलें",
        "added_photo": "📥 **फोटो जोड़ी गई!** ({curr}/{max})\n📄 नाम: `{name}.pdf`",
        "pdf_success": "✅ **पीडीएफ सफलतापूर्वक बन गई!**",
        "help_msg": "🛠️ **पीडीएफ गाइड:**\n1. पीडीएफ बनाने के लिए फोटो भेजें।\n2. नया नाम देने के लिए `/name Naya_Naam` टाइप करें।\n3. नाम बदलने के लिए पुरानी पीडीएफ फाइल भेजें।"
    },
    "hinglish": {
        "status_pro": "👑 VIP PRO UNLOCKED (Limit: 50 Photos)",
        "status_free": "🔓 FREE PLAN (Limit: 10 Photos)",
        "welcome": "📄 **PDF MASTER & EDITOR PRO**\n\n🏷️ Status: **{status}**\n👥 Invites: **{refs}/3 Friends**\n\n📸 **Photo to PDF:** Photos bhejein, bot PDF bana dega!\n🔄 **Rename PDF:** PDF bhej kar naam badlein!\n\n🔗 **Aapka Link:**\n`{ref_link}`",
        "btn_share": "🎁 Share & Unlock VIP",
        "btn_tools": "🔒 Advanced Tools",
        "btn_lang": "🌐 Language Badlein",
        "added_photo": "📥 **Photo Add Ho Gayi!** ({curr}/{max})\n📄 Name: `{name}.pdf`",
        "pdf_success": "✅ **PDF Successfully Ban Gayi!**",
        "help_msg": "🛠️ **PDF BOT GUIDE:**\n1. Photo bhej kar PDF banayein.\n2. `/name MyFile` bhej kar naam set karein.\n3. Purani PDF bhej kar rename karein."
    },
    "mr": {"status_pro": "👑 VIP अनलॉक (50 फोटो)", "status_free": "🔓 मोफत प्लॅन (10 फोटो)", "welcome": "📄 **PDF MASTER PRO**\n\n🏷️ स्टेटस: **{status}**\n🔗 **लिंक:** `{ref_link}`", "btn_share": "🎁 शेअर करा", "btn_tools": "🔒 प्रगत साधने", "btn_lang": "🌐 भाषा बदला", "added_photo": "📥 फोटो जोडला!", "pdf_success": "✅ पीडीएफ तयार झाली!", "help_msg": "🛠️ **मार्गदर्शक:** फोटो पाठवा किंवा पीडीएफ पाठवून नाव बदला."},
    "bn": {"status_pro": "👑 ভিআইপি আনলক (৫০ ছবি)", "status_free": "🔓 ফ্রি প্ল্যান (১০ ছবি)", "welcome": "📄 **PDF MASTER PRO**\n\n🏷️ স্ট্যাটাস: **{status}**\n🔗 **লিঙ্ক:** `{ref_link}`", "btn_share": "🎁 শেয়ার করুন", "btn_tools": "🔒 অ্যাডভান্সড টুলস", "btn_lang": "🌐 ভাষা পরিবর্তন", "added_photo": "📥 ছবি যোগ করা হয়েছে!", "pdf_success": "✅ পিডিএফ তৈরি হয়েছে!", "help_msg": "🛠️ **গাইড:** ছবি পাঠান বা পিডিএফ রিনেম করুন।"},
    "te": {"status_pro": "👑 VIP అన్‌లాక్ (50 ఫోటోలు)", "status_free": "🔓 ఉచిత ప్లాన్ (10 ఫోటోలు)", "welcome": "📄 **PDF MASTER PRO**\n\n🏷️ స్థితి: **{status}**\n🔗 **లింక్:** `{ref_link}`", "btn_share": "🎁 షేర్ చేయండి", "btn_tools": "🔒 సాధనాలు", "btn_lang": "🌐 భాష మార్చండి", "added_photo": "📥 ఫోటో జోడించబడింది!", "pdf_success": "✅ PDF సృష్టించబడింది!", "help_msg": "🛠️ **మార్గదర్శకం:** ఫోటోలు పంపండి."},
    "ta": {"status_pro": "👑 VIP அலாக் (50)", "status_free": "🔓 இலவசம் (10)", "welcome": "📄 **PDF MASTER PRO**\n\n🏷️ நிலை: **{status}**\n🔗 **லிங்க்:** `{ref_link}`", "btn_share": "🎁 பகிர்ந்து", "btn_tools": "🔒 கருவிகள்", "btn_lang": "🌐 மொழி", "added_photo": "📥 சேர்க்கப்பட்டது!", "pdf_success": "✅ உருவாக்கப்பட்டது!", "help_msg": "🛠️ **வழிகாட்டி:** புகைப்படங்களை அனுப்புங்கள்."},
    "ar": {"status_pro": "👑 تم فتح VIP (50 صورة)", "status_free": "🔓 مجاني (10 صور)", "welcome": "📄 **PDF MASTER PRO**\n\n🏷️ الحالة: **{status}**\n🔗 **الرابط:** `{ref_link}`", "btn_share": "🎁 مشاركة", "btn_tools": "🔒 أدوات", "btn_lang": "🌐 تغيير اللغة", "added_photo": "📥 تم الإضافة!", "pdf_success": "✅ تم الإنشاء!", "help_msg": "🛠️ **دليل:** أرسل الصور لتحويلها."},
    "ru": {"status_pro": "👑 VIP РАЗБЛОКИРОВАН (50)", "status_free": "🔓 БЕСПЛАТНО (10)", "welcome": "📄 **PDF MASTER PRO**\n\n🏷️ Статус: **{status}**\n🔗 **Ссылка:** `{ref_link}`", "btn_share": "🎁 Поделиться", "btn_tools": "🔒 Инструменты", "btn_lang": "🌐 Язык", "added_photo": "📥 Добавлено!", "pdf_success": "✅ Создано!", "help_msg": "🛠️ **Справка:** Отправьте фото."},
    "fa": {"status_pro": "👑 وی‌آی‌پی فعال (۵۰)", "status_free": "🔓 رایگان (۱۰)", "welcome": "📄 **PDF MASTER PRO**\n\n🏷️ وضعیت: **{status}**\n🔗 **لینک:** `{ref_link}`", "btn_share": "🎁 اشتراک", "btn_tools": "🔒 ابزارها", "btn_lang": "🌐 زبان", "added_photo": "📥 اضافه شد!", "pdf_success": "✅ ساخته شد!", "help_msg": "🛠️ **راهنما:** عکس‌ها را ارسال کنید."}
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except: pass
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
    usr, data = get_user(chat_id)
    if update.effective_user.id == ADMIN_ID or chat_id == str(ADMIN_ID):
        usr["plan"] = "PRO"
        save_data(data)
        await update.message.reply_text("👑 **ADMIN PRIVILEGE:** VIP PRO Unlocked!")
    else:
        await update.message.reply_text("⛔ Admin only command!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    usr, data = get_user(chat_id)
    bot_username = (await context.bot.get_me()).username

    if update.effective_user.id == ADMIN_ID:
        usr["plan"] = "PRO"
        save_data(data)

    if context.args and not usr.get("referred_by"):
        inviter_id = context.args[0].replace("ref_", "")
        if inviter_id != chat_id and inviter_id in data:
            usr["referred_by"] = inviter_id
            inviter = data[inviter_id]
            inviter["referrals"] = inviter.get("referrals", 0) + 1
            if inviter["referrals"] >= 3 and inviter.get("plan") != "PRO":
                inviter["plan"] = "PRO"
                save_data(data)
                try: await context.bot.send_message(chat_id=int(inviter_id), text="🎉 **VIP PRO UNLOCKED!** 🚀")
                except: pass
            else: save_data(data)

    ref_link = f"https://t.me/{bot_username}?start=ref_{chat_id}"
    is_pro = usr.get("plan") == "PRO"
    status = get_text(chat_id, "status_pro" if is_pro else "status_free")
    
    msg_template = get_text(chat_id, "welcome")
    msg = msg_template.format(status=status, refs=usr.get('referrals', 0), ref_link=ref_link)

    tools_text = "🔓 Advanced Tools" if is_pro else get_text(chat_id, "btn_tools")
    kb = [
        [InlineKeyboardButton(get_text(chat_id, "btn_share"), callback_data="refer_info")],
        [InlineKeyboardButton(tools_text, callback_data="locked_tools"), InlineKeyboardButton(get_text(chat_id, "btn_lang"), callback_data="choose_lang")]
    ]
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    help_txt = get_text(chat_id, "help_msg")
    await update.message.reply_text(help_txt, parse_mode="Markdown")

async def vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    usr, _ = get_user(chat_id)
    status = "👑 VIP PRO UNLOCKED (50 Photos Limit)" if usr.get("plan") == "PRO" else "🔓 FREE PLAN (3 Referrals required for VIP)"
    await update.message.reply_text(f"📊 **Account Status:**\n{status}\n• Referrals Completed: **{usr.get('referrals', 0)} / 3**")

async def set_pdf_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not context.args:
        await update.message.reply_text("❌ Usage: `/name My_New_File_Name`", parse_mode="Markdown")
        return

    custom_name = "_".join(context.args)

    if chat_id in USER_PENDING_DOCS:
        status_msg = await update.message.reply_text("🔄 **Renaming PDF Document...**")
        try:
            doc_file = USER_PENDING_DOCS.pop(chat_id)
            pdf_bytes = await doc_file.download_as_bytearray()
            
            await status_msg.delete()
            await context.bot.send_document(
                chat_id=int(chat_id),
                document=io.BytesIO(pdf_bytes),
                filename=f"{custom_name}.pdf",
                caption=f"✅ **PDF Renamed Successfully!**\n📄 New Name: `{custom_name}.pdf`"
            )
        except Exception:
            await status_msg.edit_text("❌ Failed to rename PDF file!")
    else:
        USER_PDF_NAMES[chat_id] = custom_name
        await update.message.reply_text(f"✏️ **PDF Name Set To:** `{custom_name}.pdf`\nAb photos bhejien!", parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    doc = update.message.document

    if doc.mime_type == 'application/pdf' or doc.file_name.endswith('.pdf'):
        doc_file = await doc.get_file()
        USER_PENDING_DOCS[chat_id] = doc_file
        await update.message.reply_text(
            f"📥 **PDF Received:** `{doc.file_name}`\n\nIs PDF ka naya naam kya rakhna hai?\nType karein: `/name Aapka_Naya_Naam`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("⚠️ Kripya sirf **PDF File** bhejien!")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat_id)
    usr, data = get_user(chat_id)
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{chat_id}"

    if query.data == "choose_lang":
        await query.answer()
        lang_kb = [
            [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi"), InlineKeyboardButton("🗣️ Hinglish", callback_data="lang_hinglish")],
            [InlineKeyboardButton("🇮🇳 मराठी", callback_data="lang_mr"), InlineKeyboardButton("🇮🇳 বাংলা", callback_data="lang_bn")],
            [InlineKeyboardButton("🇮🇳 తెలుగు", callback_data="lang_te"), InlineKeyboardButton("🇮🇳 தமிழ்", callback_data="lang_ta")],
            [InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"), InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"), InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
        ]
        await query.message.edit_text("🌐 **Select Language:**", reply_markup=InlineKeyboardMarkup(lang_kb))
    
    elif query.data.startswith("lang_"):
        selected_lang = query.data.replace("lang_", "")
        usr["lang"] = selected_lang
        save_data(data)
        await query.answer("Language Changed!")
        
        is_pro = usr.get("plan") == "PRO"
        status = get_text(chat_id, "status_pro" if is_pro else "status_free")
        msg = get_text(chat_id, "welcome").format(status=status, refs=usr.get('referrals', 0), ref_link=ref_link)
        kb = [
            [InlineKeyboardButton(get_text(chat_id, "btn_share"), callback_data="refer_info")],
            [InlineKeyboardButton(get_text(chat_id, "btn_lang"), callback_data="choose_lang")]
        ]
        await query.message.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "refer_info":
        await query.answer()
        await query.message.reply_text(f"📢 **Share Link:**\n`{ref_link}`\n\n• Referrals: {usr.get('referrals', 0)}/3", parse_mode="Markdown")
    elif query.data == "locked_tools":
        await query.answer()
        if usr.get("plan") == "PRO":
            await query.message.reply_text("🔓 **VIP Tools Unlocked!**\n• Multi-Photo Combine (50 Limit)\n• Instant PDF Rename")
        else:
            await query.message.reply_text("🔒 **Locked!** Invite 3 friends to unlock.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    usr, _ = get_user(chat_id)
    max_limit = 50 if usr.get("plan") == "PRO" else 10

    if chat_id not in USER_PHOTO_BUFFERS: USER_PHOTO_BUFFERS[chat_id] = []
    if len(USER_PHOTO_BUFFERS[chat_id]) >= max_limit:
        await update.message.reply_text(f"⚠️ Limit: {max_limit} photos.")
        return

    if update.message.caption: USER_PDF_NAMES[chat_id] = update.message.caption.strip().replace(" ", "_")

    photo_file = await update.message.photo[-1].get_file()
    img_bytes = await photo_file.download_as_bytearray()
    USER_PHOTO_BUFFERS[chat_id].append(img_bytes)
    
    total_imgs = len(USER_PHOTO_BUFFERS[chat_id])
    file_name = USER_PDF_NAMES.get(chat_id, "Document")
    
    text_msg = get_text(chat_id, "added_photo").format(curr=total_imgs, max=max_limit, name=file_name)
    msg = await update.message.reply_text(text_msg)
    asyncio.create_task(auto_process_buffer(chat_id, total_imgs, update, context, msg))

async def auto_process_buffer(chat_id, expected_count, update, context, status_msg):
    await asyncio.sleep(4)
    if chat_id in USER_PHOTO_BUFFERS and len(USER_PHOTO_BUFFERS[chat_id]) == expected_count:
        await generate_combined_pdf(chat_id, update, context, status_msg)

async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in USER_PHOTO_BUFFERS and USER_PHOTO_BUFFERS[chat_id]:
        status_msg = await update.message.reply_text("🔄 Processing...")
        await generate_combined_pdf(chat_id, update, context, status_msg)

async def generate_combined_pdf(chat_id, update, context, status_msg):
    if chat_id not in USER_PHOTO_BUFFERS or not USER_PHOTO_BUFFERS[chat_id]: return
    images_list = []
    try:
        raw_buffers = USER_PHOTO_BUFFERS.pop(chat_id, [])
        filename = USER_PDF_NAMES.pop(chat_id, "Document") + ".pdf"

        for buf in raw_buffers:
            img = Image.open(io.BytesIO(buf))
            if img.mode != 'RGB': img = img.convert('RGB')
            images_list.append(img)

        if images_list:
            pdf_bytes = io.BytesIO()
            images_list[0].save(pdf_bytes, format='PDF', save_all=True, append_images=images_list[1:])
            pdf_bytes.seek(0)
            try: await status_msg.delete()
            except: pass

            success_text = get_text(chat_id, "pdf_success").format(filename=filename)
            await context.bot.send_document(chat_id=int(chat_id), document=pdf_bytes, filename=filename, caption=success_text)
    except Exception: pass

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adminvip", adminvip))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("vip", vip_command))
    app.add_handler(CommandHandler("name", set_pdf_name))
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
