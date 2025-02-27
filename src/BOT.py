import telebot
import re
from model import Utente, Feedback, Group
from config import TOKEN_DEL_BOT


bot = telebot.TeleBot(TOKEN_DEL_BOT)

def register_user(message):
    try:
        if Utente().getUtente(message.from_user.id) is not None:
            bot.reply_to(message, messages["errors"]["registration"], parse_mode="Markdown")
            return
        Utente().registerUser(message)
        bot.reply_to(message, messages["successes"]["registration"], parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, messages["errors"]["registration"].format(e), parse_mode="Markdown")

def delete_user(message):
    user_id = message.from_user.id
    try:
        if Utente().getUtente(user_id) is not None:
            Utente().deleteUser(user_id)
            bot.reply_to(message, messages["successes"]["deletion"], parse_mode="Markdown")
        else:
            bot.reply_to(message, messages["errors"]["deletion"], parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, messages["errors"]["deletion"].format(e), parse_mode="Markdown")


def get_user_status(message):
    username = message.from_user.username
    try:
        parts = message.text.split()
        target_identifier = parts[1] if len(parts) > 1 else f"@{username}"
        target = Utente().getUtente(target_identifier)
        if target is None:
            raise Exception("User not found")
        answer = target.infoUser(target)
        bot.reply_to(message, answer, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, messages["errors"]["user_not_found"], parse_mode="Markdown")


def officialize_group(message):
    try:
        Group.officialize(message.chat.id, message.from_user.id)
        bot.reply_to(message, messages["successes"]["officialize"])
    except Exception as e:
        bot.reply_to(message, messages["errors"]["officialize"].format(e))


def set_pgp_key(message, edit_mode=False):
    user_id = message.from_user.id
    text_message = message.text.replace("/setpgpkey" if not edit_mode else "/editpgpkey", "")
    pgp_key = re.sub(r'\s+', '', text_message)

    if not pgp_key:
        bot.reply_to(message, messages["errors"]["empty_pgp_key"])
        return

    if not is_valid_pgp_key(pgp_key):
        bot.reply_to(message, messages["errors"]["invalid_pgp_key"])
        return

    try:
        user = Utente()
        if user.set_pgp_key(user_id, pgp_key):
            bot.reply_to(message, messages["successes"]["pgp_key_edited"] if edit_mode else messages["successes"]["pgp_key_set"])
        else:
            bot.reply_to(message, messages["errors"]["user_not_found"])
    except Exception as e:
        bot.reply_to(message, messages["errors"]["pgp_key"].format(e))


def is_valid_pgp_key(pgp_key):
    return pgp_key.startswith("-----BEGINPGP")

def help_command(message):
    help_text = "Available commands:\n\n"
    for command, data in commands.items():
        help_text += f"*{command}*: {data['description']}\n"

    max_length = 4096  # Telegram's message character limit

    # Improved debugging: Print the length and the message itself
    print(f"Help message length: {len(help_text)}")
    print("Help message content:\n", help_text)

    if len(help_text) > max_length:
        chunks = [help_text[i:i + max_length] for i in range(0, len(help_text), max_length)]
        for i, chunk in enumerate(chunks):
            try:
                bot.reply_to(message, chunk, parse_mode="Markdown")
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Error sending chunk {i+1}: {e}")
                # Handle the error appropriately (e.g., log it, send a different message)
    else:
        try:
            bot.reply_to(message, help_text, parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error sending help message: {e}")




# --- Command Dictionary ---
commands = {
    "/start": {"handler": register_user, "description": "Registers you with the bot."},
    "/delete": {"handler": delete_user, "description": "Deletes your registration."},
    "/status": {"handler": get_user_status, "description": "Shows your current status (optional: `/status @username` for another user)."},
    "/officialize": {"handler": officialize_group, "description": "Officializes the group (only for admins)."},
    "/setpgpkey": {"handler": lambda m: set_pgp_key(m, edit_mode=False), "description": "Sets your PGP key."},
    "/editpgpkey": {"handler": lambda m: set_pgp_key(m, edit_mode=True), "description": "Edits your PGP key."},
    "/help": {"handler": help_command, "description": "Shows this help message."},
}

# --- Messages Dictionary (Combined Error and Success) ---
messages = {
    "errors": {
        "registration": "Errore durante la registrazione: {}",
        "deletion": "Errore durante la cancellazione: {}",
        "user_not_found": "Utente non trovato",
        "officialize": "Errore: {}",
        "pgp_key": "Errore nella gestione della chiave PGP: {}",
        "invalid_pgp_key": "Chiave PGP non valida. Assicurati di averla incollata correttamente.",
        "empty_pgp_key": "Devi inserire la chiave PGP dopo il comando. Esempio: /setpgpkey -----BEGIN PGP...",
        "command_not_found": "Command not found"
    },
    "successes": {
        "registration": "Registrazione effettuata con successo!",
        "deletion": "La tua registrazione è stata eliminata",
        "officialize": "Il gruppo è stato ufficializzato!",
        "pgp_key_set": "Chiave PGP impostata con successo!",
        "pgp_key_edited": "Chiave PGP modificata con successo!",
    },
}




@bot.message_handler(func=lambda message: True)
def gestione_messaggi(message):
    for command, data in commands.items():
        if message.text.startswith(command):
            data["handler"](message)
            return

    bot.reply_to(message, messages["errors"]["command_not_found"])


if __name__ == "__main__":
    bot.infinity_polling()
