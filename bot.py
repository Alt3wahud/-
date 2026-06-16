import telebot
from telebot import types
import yt_dlp
import os
import requests

# توكن البوت
TOKEN = '8643672051:AAFd9dmgdYthxeKBgCuR6KZLgUwHpWoC-Io'
bot = telebot.TeleBot(TOKEN)

# معلوماتك
OWNER_USERNAME = "uillay"
BOT_USERNAME = "Dea6hbot"

# قاموس لحفظ لغة كل محادثة
chat_langs = {}

# نصوص البوت باللغتين
LANG_TEXTS = {
    'ar': {
        'start_msg': "= : Hi? <a href='tg://user?id={id}'>{name}</a> .\n= : Iam <a href='https://t.me/{bot_user}'>death</a> .\n= : version==4.0.0 .\n\n= : لتشغيل الموسيقى في المكالمات .\n= : لتحميل المقاطع الصوتية .",
        'group_welcome': "مرحبا <a href='tg://user?id={id}'>{name}</a>\nفي بوت الاغاني <a href='https://t.me/{bot_user}'>death</a>\nشكرا لاضافتي في {group}\nالان يمكنك تشغيل الاغاني والمقاطع في هذه الدردشة",
        'btn_add': "لإضافتي في مجموعتك",
        'btn_owner': "= : المالك : =",
        'btn_lang': "اللغة 🌐",
        'searching': "جاري البحث عن «{query}» والتحميل، انتظر ثواني...",
        'downloading': "جاري التحميل، انتظر ثواني...",
        'error': "عذراً، صار خطأ بالتحميل.",
        'duration_limit': "عذراً، المقطع طويل جداً! الحد الأقصى هو 20 دقيقة ⏱.",
        'size_limit': "عذراً، حجم المقطع يتجاوز 50 ميجابايت (حدود التليكرام) 📦.",
        'lang_changed': "تم تغيير لغة البوت إلى العربية 🇮🇶."
    },
    'en': {
        'start_msg': "= : Hi? <a href='tg://user?id={id}'>{name}</a> .\n= : Iam <a href='https://t.me/{bot_user}'>death</a> .\n= : version==4.0.0 .\n\n= : To play music in voice chats .\n= : To download audio and video clips .",
        'group_welcome': "Welcome <a href='tg://user?id={id}'>{name}</a>\nTo <a href='https://t.me/{bot_user}'>death</a> music bot\nThanks for adding me to {group}\nNow you can play songs and clips in this chat",
        'btn_add': "Add to your group",
        'btn_owner': "= : Owner : =",
        'btn_lang': "Language 🌐",
        'searching': "Searching for «{query}» and downloading, please wait...",
        'downloading': "Downloading, please wait...",
        'error': "Sorry, an error occurred during download.",
        'duration_limit': "Sorry, the audio is too long! The maximum limit is 20 minutes ⏱.",
        'size_limit': "Sorry, the audio size exceeds 50 MB (Telegram limit) 📦.",
        'lang_changed': "Bot language has been changed to English 🇺🇸."
    }
}

def get_lang(chat_id):
    return chat_langs.get(chat_id, 'ar')

def create_main_markup(lang_code):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_add = types.InlineKeyboardButton(LANG_TEXTS[lang_code]['btn_add'], url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
    btn_owner = types.InlineKeyboardButton(LANG_TEXTS[lang_code]['btn_owner'], url=f"https://t.me/{OWNER_USERNAME}")
    btn_lang = types.InlineKeyboardButton(LANG_TEXTS[lang_code]['btn_lang'], callback_data="change_lang")
    markup.add(btn_add, btn_owner, btn_lang)
    return markup

# 1. أمر /start بالخاص
@bot.message_handler(commands=['start'])
def send_welcome(message):
    lang_code = get_lang(message.chat.id)
    user_name = message.from_user.first_name
    text = LANG_TEXTS[lang_code]['start_msg'].format(id=message.from_user.id, name=user_name, bot_user=BOT_USERNAME)
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=create_main_markup(lang_code))

# 2. كود الترحيب للمجموعات
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for new_member in message.new_chat_members:
        if new_member.id == bot.get_me().id:
            lang_code = get_lang(message.chat.id)
            user_name = message.from_user.first_name
            group_name = message.chat.title
            text = LANG_TEXTS[lang_code]['group_welcome'].format(id=message.from_user.id, name=user_name, bot_user=BOT_USERNAME, group=group_name)
            bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=create_main_markup(lang_code))

# 3. إعدادات اللغة
@bot.callback_query_handler(func=lambda call: call.data in ["change_lang", "set_ar", "set_en"])
def language_callback(call):
    if call.data == "change_lang":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("عربي 🇮🇶", callback_data="set_ar"),
            types.InlineKeyboardButton("English 🇺🇸", callback_data="set_en")
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == "set_ar":
        chat_langs[call.message.chat.id] = 'ar'
        bot.answer_callback_query(call.id, "تم اختيار اللغة العربية.")
        bot.edit_message_text(LANG_TEXTS['ar']['lang_changed'], call.message.chat.id, call.message.message_id)
    elif call.data == "set_en":
        chat_langs[call.message.chat.id] = 'en'
        bot.answer_callback_query(call.id, "English selected.")
        bot.edit_message_text(LANG_TEXTS['en']['lang_changed'], call.message.chat.id, call.message.message_id)

def check_limits(video_info, lang_code, message, msg_id):
    duration = video_info.get('duration', 0)
    if duration and duration > 1200: # 20 دقيقة
        bot.edit_message_text(LANG_TEXTS[lang_code]['duration_limit'], message.chat.id, msg_id)
        return False
    filesize = video_info.get('filesize') or video_info.get('filesize_approx') or 0
    if filesize and filesize > 50000000: # 50 ميجا
        bot.edit_message_text(LANG_TEXTS[lang_code]['size_limit'], message.chat.id, msg_id)
        return False
    return True

# دالة لتحميل وإرسال الصوتية
def process_and_send_audio(ydl_opts, query, message, msg_id, lang_code):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            video_info = info['entries'][0] if 'entries' in info and len(info['entries']) > 0 else info
            
            if not check_limits(video_info, lang_code, message, msg_id):
                return
            
            info_download = ydl.extract_info(query, download=True)
            video_dl_info = info_download['entries'][0] if 'entries' in info_download and len(info_download['entries']) > 0 else info_download
            filename = ydl.prepare_filename(video_dl_info)
            
            title = video_dl_info.get('title', 'Audio Track')
            thumb_url = video_dl_info.get('thumbnail')
            thumb_filename = f"thumb_{video_dl_info['id']}.jpg"
            
            if thumb_url:
                try:
                    r = requests.get(thumb_url)
                    with open(thumb_filename, 'wb') as f:
                        f.write(r.content)
                except:
                    thumb_filename = None
            else:
                thumb_filename = None
        
        # إنشاء زر death اللي يودي ليوزرك
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("death", url=f"https://t.me/{OWNER_USERNAME}"))
        
        # الوصف المحدث
        audio_caption = "𝘾𝙍𝙀𝘿𝙄𝙏 ➤ @Dea6hbot"
        
        # إرسال الملف الصوتي
        with open(filename, 'rb') as audio:
            thumb_file = open(thumb_filename, 'rb') if thumb_filename and os.path.exists(thumb_filename) else None
            
            bot.send_audio(
                message.chat.id, 
                audio, 
                caption=audio_caption,
                reply_to_message_id=message.message_id, 
                reply_markup=markup, 
                title=title, 
                performer=title, # اسم الفنان صار هو اسم المقطع
                thumb=thumb_file 
            )
            
            if thumb_file:
                thumb_file.close()
        
        os.remove(filename)
        if thumb_filename and os.path.exists(thumb_filename):
            os.remove(thumb_filename)
        bot.delete_message(message.chat.id, msg_id)
        
    except Exception as e:
        bot.edit_message_text(LANG_TEXTS[lang_code]['error'], message.chat.id, msg_id)
        print(f"Error: {e}")

@bot.message_handler(func=lambda message: message.text and (message.text.lower().startswith("yt ") or message.text.startswith("يوت ")))
def search_and_download(message):
    lang_code = get_lang(message.chat.id)
    query = message.text[3:].strip() if message.text.lower().startswith("yt ") else message.text[4:].strip()
    if not query: return
    
    msg = bot.reply_to(message, LANG_TEXTS[lang_code]['searching'].format(query=query))
    ydl_opts = {'format': 'bestaudio[ext=m4a]/bestaudio', 'outtmpl': 'audio_%(id)s.%(ext)s', 'quiet': True, 'noplaylist': True}
    search_query = f"ytsearch1:{query}"
    process_and_send_audio(ydl_opts, search_query, message, msg.message_id, lang_code)

@bot.message_handler(func=lambda message: message.text and ("youtube.com" in message.text or "youtu.be" in message.text or "tiktok.com" in message.text))
def download_link(message):
    lang_code = get_lang(message.chat.id)
    msg = bot.reply_to(message, LANG_TEXTS[lang_code]['downloading'])
    ydl_opts = {'format': 'bestaudio[ext=m4a]/bestaudio', 'outtmpl': 'audio_%(id)s.%(ext)s', 'quiet': True, 'noplaylist': True}
    process_and_send_audio(ydl_opts, message.text, message, msg.message_id, lang_code)

print("البوت شغال هسه...")
bot.infinity_polling()
