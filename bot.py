import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os

TOKEN = '8681462655:AAE_NBd1uQcAdgXflA4WQlSNq0cZV2pYXz0'
bot = telebot.TeleBot(TOKEN)
user_links = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 Downloader Bot Active!\nMujhe koi bhi video link bhejo, main available qualities fetch karunga.")

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def fetch_qualities(message):
    url = message.text
    chat_id = message.chat.id
    msg = bot.reply_to(message, "🔍 Scanning video qualities...")

    ydl_opts = {'quiet': True, 'noplaylist': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
            text=f"✅ **{title}**\n\nQuality select karein:",
            chat_id=chat_id,
            message_id=msg.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {e}", chat_id=chat_id, message_id=msg.message_id)

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
    ydl_opts = {
        'format': format_str,
        'outtmpl': out_file,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
        bot.edit_message_text(f"❌ Download fail: {e}", chat_id=chat_id, message_id=msg_id)

print("Bot is LIVE!")
bot.infinity_polling()
