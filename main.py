import telebot
import psycopg2
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

API_TOKEN = ''
bot = telebot.TeleBot(API_TOKEN)

# Добавить кодировку
conn = psycopg2.connect(database="NetEng", user="postgres",
                        password="YourPassword", host="localhost",
                        port="5432", options='-c client_encoding=UTF8')
cursor = conn.cursor()


def init_db():
    with open("init_db.sql", "r", encoding='utf-8') as f:
        cursor.execute(f.read())
    conn.commit()


@bot.message_handler(commands=['start'])
def start_command(message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    cursor.execute("INSERT INTO users (telegram_id, username) VALUES (%s, %s)"
                   " ON CONFLICT (telegram_id) DO NOTHING",
                   (telegram_id, username))
    conn.commit()
    bot.send_message(message.chat.id, f"Hello, {username}, let study "
                                      f"English...")


@bot.message_handler(commands=['addword'])
def add_word(message):
    msg = bot.send_message(message.chat.id,
                           "Введите слово и его перевод "
                           "через запятую (например: apple, яблоко):")
    bot.register_next_step_handler(msg, save_word)


def save_word(message):
    user_id = message.from_user.id
    text = message.text.strip().split(',')
    if len(text) == 2:
        word, translation = text[0].strip(), text[1].strip()
        cursor.execute(
            "INSERT INTO user_words (user_id, word, translation) "
            "VALUES ((SELECT id FROM users WHERE telegram_id=%s), %s, %s)",
            (user_id, word, translation))
        conn.commit()
        cursor.execute(
            "SELECT COUNT(*) FROM user_words "
            "WHERE user_id=(SELECT id FROM users WHERE telegram_id=%s)",
            (user_id,))
        word_count = cursor.fetchone()[0]
        bot.send_message(message.chat.id,
                         f"Слово '{word}' с переводом '{translation}' "
                         f"добавлено. Вы изучаете {word_count} слов(а).")
    else:
        bot.send_message(message.chat.id,
                         "Некорректный формат ввода. Попробуйте снова.")


@bot.message_handler(commands=['deleteword'])
def delete_word(message):
    msg = bot.send_message(message.chat.id,
                           "Введите слово, которое хотите удалить:")
    bot.register_next_step_handler(msg, remove_word)


def remove_word(message):
    user_id = message.from_user.id
    word = message.text.strip()
    cursor.execute(
        "DELETE FROM user_words WHERE"
        " user_id=(SELECT id FROM users WHERE telegram_id=%s) AND word=%s",
        (user_id, word))
    conn.commit()
    cursor.execute(
        "SELECT COUNT(*) FROM user_words WHERE"
        " user_id=(SELECT id FROM users WHERE telegram_id=%s)",
        (user_id,))
    word_count = cursor.fetchone()[0]
    bot.send_message(message.chat.id,
                     f"Слово '{word}' удалено. Вы изучаете {word_count} слов(а).")


@bot.message_handler(commands=['allwords'])
def all_words(message):
    user_id = message.from_user.id
    cursor.execute("SELECT id FROM users WHERE telegram_id=%s", (user_id,))
    user_db_id = cursor.fetchone()[0]
    cursor.execute("SELECT word, translation FROM user_words WHERE user_id=%s",
                   (user_db_id,))
    words = cursor.fetchall()
    if words:
        response = "Ваши слова:\n" + "\n".join(
            [f"{word} - {translation}" for word, translation in words])
    else:
        response = "Вы не изучаете ни одного слова."
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['quiz'])
def quiz(message):
    cursor.execute(
        "SELECT word, translation FROM words ORDER BY RANDOM() LIMIT 1")
    word, correct_translation = cursor.fetchone()
    cursor.execute(
        "SELECT translation FROM words WHERE word != "
        "%s ORDER BY RANDOM() LIMIT 3",
        (word,))
    incorrect_translations = [row[0] for row in cursor.fetchall()]
    options = incorrect_translations + [correct_translation]
    random.shuffle(options)

    markup = InlineKeyboardMarkup()
    for option in options:
        markup.add(
            InlineKeyboardButton(option, callback_data=f"{word}:{option}"))

    bot.send_message(message.chat.id, f"Какой перевод слова '{word}'?",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_quiz_answer(call):
    word, selected_translation = call.data.split(':')
    cursor.execute("SELECT translation FROM words WHERE word=%s", (word,))
    correct_translation = cursor.fetchone()[0]

    if selected_translation == correct_translation:
        bot.answer_callback_query(call.id, "Правильно!")
    else:
        bot.answer_callback_query(call.id, "Неправильно, попробуйте снова.")


if __name__ == '__main__':
    init_db()
    bot.polling()
