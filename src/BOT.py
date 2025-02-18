import telebot
from model import Utente, Feedback,Group
from config import TOKEN_DEL_BOT

# Configurazione del bot
bot = telebot.TeleBot(TOKEN_DEL_BOT)

@bot.message_handler(func=lambda message: True)
def gestione_messaggi(message):
    chat_id = message.chat.id              # Chat di provenienza del messaggio
    chat_title = message.chat.title         # Titolo della chat (per i gruppi)

    username = message.from_user.username   # Username dell'utente
    user_id  = message.from_user.id         # ID dell'utente

    # Gestione comando /start: registrazione utente
    if message.text.startswith('/start'):
        try:
            # Registra l'utente; il metodo registerUser deve essere implementato nel modello
            Utente().registerUser(message)
            bot.reply_to(message, "Registrazione effettuata con successo!", parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"Errore durante la registrazione: {e}", parse_mode="Markdown")
        return

    # Se l'utente non è registrato, gli viene richiesto di registrarsi prima di procedere
    user = Utente().getUtente(user_id)
    if user is None:
        bot.reply_to(message, "Devi prima registrarti usando il comando /start", parse_mode="Markdown")
        return

    # Gestione comando /delete: l'utente si cancella dal sistema
    if message.text.startswith('/delete'):
        try:
            Utente().deleteUser(user_id)
            bot.reply_to(message, "La tua registrazione è stata eliminata", parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"Errore durante la cancellazione: {e}", parse_mode="Markdown")
        return

    # Esempio di comando /status
    if message.text.startswith('/status'):
        try:
            parts = message.text.split()
            # Se viene specificato un username, lo usiamo, altrimenti usiamo quello del richiedente
            target_identifier = parts[1] if len(parts) > 1 else f"@{username}"
            target = Utente().getUtente(target_identifier)
            if target is None:
                raise Exception("User not found")
            answer = Utente().infoUser(target)
            bot.reply_to(message, answer, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, "Utente non trovato", parse_mode="Markdown")


if __name__ == '__main__':
    bot.infinity_polling()
