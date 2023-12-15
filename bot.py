import sqlite3

# Название базы данных
DB_NAME = "tattoo_bot_di.db"

def view_appointments():
    conn = sqlite3.connect("tattoo_bot_di.db")
    cursor = conn.cursor()

    # Получаем все записи из таблицы appointments
    cursor.execute('SELECT * FROM appointments')
    rows = cursor.fetchall()

    # Выводим результат
    for row in rows:
        print(row)

    conn.close()

# Вызываем функцию
view_appointments()
