import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import sqlite3
from datetime import datetime
from datetime import timedelta

# Введите токен своего бота
TOKEN = "6834425219:AAHXPrRlsnPXT29UXsgUgjTjQ1B5n9KyScg"

# Название базы данных
DB_NAME = "tattoo_bot_di.db"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Состояния разговора
NAME, TATTOO_CHOICE, TATTOO_PREFERENCES, TATTOO_PHOTO, APPOINTMENT_DATE, CONTACT_INFO, FINISH = range(7)
# Словарь для хранения информации о клиентах
clients_data = {}

# Обработка команды /start
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Доброго времени суток! Как Вас зовут?')
    return NAME

# Обработка имени
def get_name(update: Update, context: CallbackContext) -> int:
    user_name = update.message.text
    clients_data[update.message.chat_id] = {'name': user_name}
    update.message.reply_text(f'Приятно познакомиться, {user_name}! Хотите татуировку?', reply_markup=get_tattoo_choice_markup())
    return TATTOO_CHOICE

# Функция для создания клавиатуры с кнопками "Да" и "Нет"
def get_tattoo_choice_markup():
    keyboard = [['Да', 'Нет']]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

# Функция для обработки выбора по татуировке
def tattoo_choice(update: Update, context: CallbackContext) -> int:
    # Получаем ответ пользователя
    user_response = update.message.text.lower()

    # Проверяем ответ
    if user_response == 'да':
        update.message.reply_text('Отлично! Есть пожелания к эскизу? Вариант того, что хочется набить? '
                                  'Разработка эскиза бесплатная. Опишите, включая размер, стиль. Фото можно будет прикрепить на следующем этапе. Пишите все в 1 сообщении')

        return TATTOO_PREFERENCES
    elif user_response == 'нет':
        update.message.reply_text('Жаль, что вы передумали. Вот несколько вариантов для ознакомления:''https://t.me/dianabiot')
        # Вернем конечное состояние
        return NAME
    else:
        # Если ответ не "да" и не "нет", запросим повторный выбор
        update.message.reply_text('Пожалуйста, выберите "да" или "нет".')
        return TATTOO_CHOICE

# Обработка пожеланий по татуировке
def tattoo_preferences(update: Update, context: CallbackContext) -> int:
    preferences = update.message.text
    clients_data[update.message.chat_id]['tattoo_preferences'] = preferences
    update.message.reply_text('Отлично! Теперь пришлите фото с понравившимся вариантом татуировки или какого-то объекта/субъекта для разработки эскиза. Фото должно быть 1')
    return TATTOO_PHOTO

# Обработка фото
def tattoo_photo(update: Update, context: CallbackContext) -> int:
    file_id = update.message.photo[-1].file_id
    clients_data[update.message.chat_id]['tattoo_photo'] = file_id
    update.message.reply_text('Спасибо за фото! Теперь укажите свой номер телефона или ссылку на телеграмм для связи:')
    return CONTACT_INFO


# Обработка контактной информации
def contact_info(update: Update, context: CallbackContext) -> int:
    phone_number = update.message.text
    clients_data[update.message.chat_id]['phone_number'] = phone_number
    update.message.reply_text('Теперь выберите удобную дату сеанса:', reply_markup=get_available_dates_markup())
    return APPOINTMENT_DATE
# Обработка выбора даты
def get_appointment_date(update: Update, context: CallbackContext) -> int:
    context.user_data['appointment_date'] = update.message.text

    # Сохраняем дату в базе данных как занятую
    save_appointment_date(context.user_data['appointment_date'])

    # Сохраняем информацию в базе данных или отправляем ее куда-то еще
    save_data(update.message.chat_id)

    update.message.reply_text(f'До встречи на сеансе {context.user_data["appointment_date"]}! '
                              f'Обязательно хорошо поспите и вкусно покушайте :)')

    return ConversationHandler.END

# Функция для создания клавиатуры с доступными датами
def get_available_dates_markup():
    dates = get_available_dates()
    keyboard = [[date.strftime('%Y-%m-%d')] for date in dates]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

# Функция для получения свободных дат
def get_available_dates():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Создаем таблицу, если ее нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            date TEXT PRIMARY KEY
        )
    ''')

    # Получаем все занятые даты
    cursor.execute('SELECT date FROM appointments')
    occupied_dates = {datetime.strptime(row[0], '%Y-%m-%d').date() for row in cursor.fetchall()}

    # Получаем все даты за следующие 30 дней, которые не заняты
    all_dates = {datetime.now().date() + timedelta(days=i) for i in range(30)}
    available_dates = all_dates - occupied_dates

    conn.close()

    return sorted(available_dates)

# Завершение разговора
def finish(update: Update, context: CallbackContext) -> int:
    appointment_date = update.message.text
    clients_data[update.message.chat_id]['appointment_date'] = appointment_date

    # Сохраняем дату в базу данных как занятую
    save_appointment_date(appointment_date)

    # Сохраняем информацию в базе данных или отправляем ее куда-то еще
    save_data(update.message.chat_id)

    update.message.reply_text(f'До встречи на сеансе {appointment_date}!, обязательно хорошо поспите и вкусно покушайте :)')

    return ConversationHandler.END

# Сохранение данных в базе данных (в данном случае, просто логирование)
def save_data(chat_id):
    logger.info(f"New client data:\nChat ID: {chat_id}\nData: {clients_data[chat_id]}")

# Сохранение даты в базе данных
def save_appointment_date(date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('INSERT INTO appointments (date) VALUES (?)', (date,))
    conn.commit()

    conn.close()

# Главная функция
def main() -> None:
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            TATTOO_CHOICE: [MessageHandler(Filters.text & ~Filters.command, tattoo_choice)],
            TATTOO_PREFERENCES: [MessageHandler(Filters.text & ~Filters.command, tattoo_preferences)],
            TATTOO_PHOTO: [MessageHandler(Filters.photo & ~Filters.command, tattoo_photo)],
            CONTACT_INFO: [MessageHandler(Filters.text & ~Filters.command, contact_info)],
            APPOINTMENT_DATE: [MessageHandler(Filters.text & ~Filters.command, get_appointment_date)],
            FINISH: [MessageHandler(Filters.text & ~Filters.command, finish)]
        },
        fallbacks=[]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
