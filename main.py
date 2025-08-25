import telebot
import datetime
from logic import DB_Manager
from config import API_TOKEN

TOKEN = API_TOKEN
bot = telebot.TeleBot(TOKEN)
manager = DB_Manager()

# Команда для старта и приветствия
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    manager.add_user(user_id, message.from_user.username)
    bot.reply_to(message, "👋 Привет! Я - *Бот-ежедневник!*\n\n"
                          "✏️ Используй команды:\n"
                          "/add - добавить задачу\n"
                          "/list - показать задачи\n"
                          "/done - отметить задачу выполненной\n"
                          "/delete - удалить задачу\n\n"
                          "📃 Для большей информации о командах введи: /help")
    
# Команда для помощи и инструкций
@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = (
        "📚 *Инструкции по использованию бота:*\n\n"
        "1. /add Заголовок; Описание; ГГГГ-ММ-ДД; ЧЧ:ММ; Приоритет\n"
        "   - Добавить новую задачу.\n"
        "   - Пример: /add Купить продукты; Молоко, хлеб; 2025-08-24; 18:30; Высокий\n\n"
        "2. /list\n"
        "   - Показать все текущие задачи.\n\n"
        "3. /done ID_задачи [ID_задачи ...]\n"
        "   - Отметить задачу(-и) как выполненную(-ые).\n"
        "   - Пример: /done 1 или /done 1 2\n\n"
        "4. /delete ID_задачи [ID_задачи ...]\n"
        "   - Удалить задачу(-и).\n"
        "   - Пример: /delete 1 или /delete 1 2\n\n"
        "⚠️ *Формат даты и времени:* ГГГГ-ММ-ДД для даты и ЧЧ:ММ для времени.\n"
        "⚠️ *Приоритеты:* 🟢 Низкий, 🟡 Средний, 🔴 Высокий.\n\n"
        "⁉️ Если у тебя возникнут вопросы, не стесняйся обращаться!"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

# Команда для добавления задачи
@bot.message_handler(commands=['add'])
def handle_add(message):
    try:
        text = message.text[len("/add"):].strip()
        parts = text.split(";")

        if len(parts) != 5:
            bot.reply_to(
                message,
                "⚠️ Ошибка!\n\n"
                "💿 Формат: /add Заголовок; Описание; ГГГГ-ММ-ДД; ЧЧ:ММ; Приоритет\n"
                "📀 Пример: /add Купить продукты; Молоко, хлеб; 2025-08-24; 18:30; Высокий\n\n"
                "📃 Для большей информации о командах введи: /help"
            )
            return

        title, desc, date_str, time_str, priority = [p.strip() for p in parts]

        # Проверка даты
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            bot.reply_to(message, "⚠️ Ошибка!\n"
                                  "📅 Дата должна быть в формате ГГГГ-ММ-ДД (например, 2025-08-24).\n\n"
                                  "📃 Для большей информации о командах введи: /help")
            return

        # Проверка времени
        try:
            datetime.datetime.strptime(time_str, "%H:%M")
        except ValueError:
            bot.reply_to(message, "⚠️ Ошибка!\n"
                                  "⌚ Время должно быть в формате ЧЧ:ММ (например, 18:30).\n\n"
                                  "📃 Для большей информации о командах введи: /help")
            return

        # Словарь для конвертации
        priority_map = {
            "низкий": "low",
            "🟢 низкий": "low",
            "средний": "medium",
            "🟡 средний": "medium",
            "высокий": "high",
            "🔴 высокий": "high"
        }

        # Проверка приоритета
        priority_key = priority.lower()
        if priority_key not in priority_map:
            bot.reply_to(
                message,
                "⚠️ Ошибка!\n"
                "⭐ Приоритет должен быть один из: 🟢 Низкий / 🟡 Средний / 🔴 Высокий\n\n"
                "📃 Для большей информации о командах введи: /help"
            )
            return

        priority_db = priority_map[priority_key]

        # Добавляем задачу
        manager.add_task(message.chat.id, title, desc, date_str, time_str, priority_db)

        # Красивый вывод пользователю
        priority_display = {
            "low": "🟢 Низкий",
            "medium": "🟡 Средний",
            "high": "🔴 Высокий"
        }[priority_db]

        bot.reply_to(message, f"✅ Задача '{title}' добавлена с приоритетом {priority_display}!")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Непредвиденная ошибка: ```{e}```\n", parse_mode="Markdown"
                               "📃 Для большей информации о командах введи: /help")

# Команда для отображения списка задач
@bot.message_handler(commands=['list'])
def handle_list(message):
    tasks = manager.list_tasks(message.chat.id)
    if not tasks:
        bot.reply_to(message, "📭 У тебя пока нет задач")
        return

    text = "📌 Твои задачи:\n\n"
    for t in tasks:
        task_id, title, due_date, due_time, status = t
        status_icon = "✅" if status == "done" else "⌛"
        text += f"{status_icon} #{task_id} {title} ⏰ {due_date} {due_time}\n"
    bot.reply_to(message, text)

# Команда для отметки задачи как выполненной
@bot.message_handler(commands=['done'])
def handle_done(message):
    try:
        args = message.text.split()[1:]
        if not args:
            bot.reply_to(message, "❌ Укажи ID задач(-и), которые(-ую) нужно завершить. Пример: /done 1 или /done 1 2\n", parse_mode="Markdown"
                                  "📃 Для большей информации о командах введи: /help")
            return

        task_ids = [int(x) for x in args]
        updated = manager.mark_done(message.chat.id, task_ids)

        if updated > 0:
            bot.reply_to(message, f"✅ Завершено(-а) задач(-а): {updated}")
        else:
            bot.reply_to(message, "⚠️ Не найдено таких(-ой) задач(-и).\n"
                                  "📃 Для большей информации о командах введи: /help")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Непредвиденная ошибка: ```{e}```\n", parse_mode="Markdown"
                               "📃 Для большей информации о командах введи: /help")

@bot.message_handler(commands=['delete'])
def handle_delete(message):
    try:
        args = message.text.split()[1:]
        if not args:
            bot.reply_to(message, "❌ Укажи ID задач(-и) для удаления. Пример: /delete 1 или /delete 1 2\n", parse_mode="Markdown"
                                  "📃 Для большей информации о командах введи: /help")
            return

        task_ids = [int(x) for x in args]
        deleted = manager.delete_task(message.chat.id, task_ids)

        if deleted > 0:
            bot.reply_to(message, f"🗑️ Удалено(-а) задач(-а): {deleted}")
        else:
            bot.reply_to(message, "⚠️ Не найдено таких(-ой) задач(-и).\n"
                                  "📃 Для большей информации о командах введи: /help")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Непредвиденная ошибка: ```{e}```\n", parse_mode="Markdown"
                               "📃 Для большей информации о командах введи: /help")

# Запуск бота
bot.infinity_polling()