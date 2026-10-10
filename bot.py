import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import threading
import time
import requests
from flask import Flask

# 1. Bot Token
TOKEN = '8681462655:AAE_NBd1uQcAdgXflA4WQlSNq0cZV2pYXz0'
bot = telebot.TeleBot(TOKEN)
user_links = {}

# 2. Render Web Server
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))

@app.route('/')
def home():
    return "Bot is 100% active and awake!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# 3. 2-Minute Anti-Sleep Loop
def keep_alive():
    time.sleep(20)
    while True:
        try:
            requests.get(f"http://127.0.0.1:{PORT}/")
            render_url = os.environ.get("RENDER_EXTERNAL_URL")
            if render_url:
                requests.get(render_url)
            print("⚡ 2-Min Ping Sent! Render is Wide Awake.")
        except Exception as e:
            print(f"Ping notice: {e}")
        time.sleep(120)

# Stable Options (YouTube Android Client Spoofing)
YDL_BASE_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    },
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web']
        }
    }
}

# 4. Bot Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 Downloader Bot Active 24/7!\nMujhe koi bhi video link bhejo, main available qualities fetch karunga.")

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def fetch_qualities(message):
    url = message.text.strip()
    chat_id = message.chat.id
    msg = bot.reply_to(message, "🔍 Scanning video qualities...")

    opts = dict(YDL_BASE_OPTS)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        formats = info.get('formats', [])
        resolutions = set()
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('height'):
                resolutions.add(f.get('height'))
        
        resolutions = sorted(list(resolutions), reverse=True)
        keyboard = InlineKeyboardMarkup(row_width=2)
        user_links[chat_id] = url
        
        buttons = [InlineKeyboardButton(text=f"🎥 {res}p", callback_data=f"dl_{res}") for res in resolutions]
        keyboard.add(*buttons)
        keyboard.add(InlineKeyboardButton(text="🎵 Audio Only (MP3)", callback_data="dl_audio"))

        title = info.get('title', 'Video')
        bot.edit_message_text(
            text=f"✅ *{title}*\n\nQuality select karein:",
            chat_id=chat_id,
            message_id=msg.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        err_msg = str(e) if str(e) else repr(e)
        bot.edit_message_text(f"❌ Error: {err_msg}", chat_id=chat_id, message_id=msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def handle_download(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if chat_id not in user_links:
        bot.answer_callback_query(call.id, "Session expire ho gaya. Link dobara bhejein.")
        return
        
    url = user_links[chat_id]
    choice = call.data.split('_')[1]
    
    bot.edit_message_text(f"⏳ Downloading ({choice}p)... Please wait.", chat_id=chat_id, message_id=msg_id)
    
    if choice == 'audio':
        format_str = 'bestaudio/best'
        ext = 'mp3'
    else:
        format_str = f'bestvideo[height<={choice}]+bestaudio/best[height<={choice}]'
        ext = 'mp4'
        
    out_file = f"{chat_id}_video.{ext}"
    opts = dict(YDL_BASE_OPTS)
    opts.update({
        'format': format_str,
        'outtmpl': out_file,
        'merge_output_format': 'mp4',
    })
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
            
        bot.edit_message_text("⬆️ Uploading to Telegram...", chat_id=chat_id, message_id=msg_id)
        
        with open(out_file, 'rb') as f:
            if choice == 'audio':
                bot.send_audio(chat_id, f)
            else:
                bot.send_video(chat_id, f)
                
        if os.path.exists(out_file):
            os.remove(out_file)
        bot.delete_message(chat_id, msg_id)
        
    except Exception as e:
        err_msg = str(e) if str(e) else repr(e)
        bot.edit_message_text(f"❌ Download fail: {err_msg}", chat_id=chat_id, message_id=msg_id)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    threading.Thread(target=keep_alive).start()
    print("Anti-Sleep 2-Min Bot is LIVE!")
    bot.infinity_polling()
