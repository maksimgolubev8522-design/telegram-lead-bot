import telebot
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("❌ Токен не найден! Создайте файл .env и добавьте туда BOT_TOKEN=ваш_токен")

bot = telebot.TeleBot(BOT_TOKEN)

# Файл, куда будем сохранять заявки
EXCEL_FILE = 'leads.xlsx'

# Словарь для временного хранения данных пользователя
user_data = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение при команде /start"""
    user_id = message.from_user.id
    user_data[user_id] = {}  # Очищаем старые данные

    welcome_text = (
        "👋 Здравствуйте! Я бот для записи на услуги.\n\n"
        "Пожалуйста, введите ваше **Имя**:"
    )
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")
    bot.register_next_step_handler(message, process_name_step)


def process_name_step(message):
    """Шаг 1: Получаем имя"""
    user_id = message.from_user.id
    name = message.text.strip()

    if not name:
        bot.send_message(user_id, "⚠️ Имя не может быть пустым. Введите имя еще раз:")
        bot.register_next_step_handler(message, process_name_step)
        return

    user_data[user_id]['name'] = name

    bot.send_message(user_id, f"Отлично, {name}! Теперь введите ваш **номер телефона** (например, +79991234567):")
    bot.register_next_step_handler(message, process_phone_step)


def process_phone_step(message):
    """Шаг 2: Получаем телефон"""
    user_id = message.from_user.id
    phone = message.text.strip()

    # Простая проверка на наличие цифр
    if not any(char.isdigit() for char in phone):
        bot.send_message(user_id, "⚠️ Номер телефона должен содержать цифры. Попробуйте еще раз:")
        bot.register_next_step_handler(message, process_phone_step)
        return

    user_data[user_id]['phone'] = phone

    bot.send_message(user_id, "Какую услугу вас интересует? (например: Консультация, Стрижка, Ремонт)")
    bot.register_next_step_handler(message, process_service_step)


def process_service_step(message):
    """Шаг 3: Получаем услугу и сохраняем в Excel"""
    user_id = message.from_user.id
    service = message.text.strip()

    if not service:
        bot.send_message(user_id, "⚠️ Укажите услугу:")
        bot.register_next_step_handler(message, process_service_step)
        return

    user_data[user_id]['service'] = service
    user_data[user_id]['date'] = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Сохраняем данные в Excel
    save_to_excel(user_data[user_id])

    # Отправляем подтверждение клиенту
    bot.send_message(
        user_id,
        "✅ Спасибо! Ваша заявка принята.\nМы свяжемся с вами в ближайшее время!",
        parse_mode="Markdown"
    )

    # Очищаем данные после успешной отправки
    del user_data[user_id]


def save_to_excel(data):
    """Функция для записи данных в Excel-файл"""
    # Преобразуем словарь в DataFrame
    df_new = pd.DataFrame([data])

    # Если файл уже существует, читаем его и добавляем новую строку
    if os.path.exists(EXCEL_FILE):
        df_existing = pd.read_excel(EXCEL_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    # Сохраняем обратно в Excel
    df_combined.to_excel(EXCEL_FILE, index=False)
    print(f"✅ Новая заявка сохранена: {data['name']}, {data['phone']}, {data['service']}")


# Запуск бота
print("🤖 Бот запущен и ожидает сообщения...")
bot.polling(none_stop=True)