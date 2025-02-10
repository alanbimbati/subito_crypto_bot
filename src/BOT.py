import telebot
from model import Utente, Feedback,Group
from config import *

# Configurazione del bot
app_config = ProdConfig()
TOKEN_DEL_BOT = "1722321202:AAH0ejhh_A5kLePfD9bt9CGYBXZbE9iA6AU"
bot = telebot.TeleBot(TOKEN_DEL_BOT)

@bot.message_handler(func=lambda message: True)
def gestione_messaggi(message):
    chat_id = message.chat.id  # chat di provenienza del messaggio
    chat_title = message.chat.title

    username = message.from_user.username  # autore del messaggio
    user_id  = message.from_user.id

    Utente().checkUtente(message)
    user = Utente().getUtente(user_id)

    if message.text.startswith('/status'):
        try:
            parts = message.text.split()
            target_user = parts[1] if len(parts) > 1 else f"@{username}"
            answer = Utente().infoUser(Utente().getUtente(target_user))        
            bot.reply_to(message, answer, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"Utente non trovato")

if __name__ == '__main__':
    bot.infinity_polling()
