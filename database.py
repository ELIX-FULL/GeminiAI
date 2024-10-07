import logging
import sqlite3
from datetime import datetime, timedelta

logging.basicConfig(filename='Errors.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

connection = sqlite3.connect('database.db')
cursor = connection.cursor()

# USERS
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER, balance INTEGER, USER_STATUS TEXT);')

# CHANNELS INFO
cursor.execute('CREATE TABLE IF NOT EXISTS channels (channel_id INTEGER, name TEXT, url TEXT);')

# ADMINS
cursor.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER);')

# BANNED_USERS
cursor.execute('CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER);')

# Создание таблицы для хранения активности пользователей день
cursor.execute('''CREATE TABLE IF NOT EXISTS user_actions
             (user_id INTEGER, action TEXT, timestamp DATETIME)''')

# Создание таблицы для хранения активности пользователей месяц
cursor.execute('''CREATE TABLE IF NOT EXISTS user_actions_month
             (user_id INTEGER, action TEXT, timestamp DATETIME)''')

connection.commit()


def check_daily_activity(user_id):
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM user_actions WHERE user_id=? AND DATE(timestamp)=?", (user_id, today))
        count = cursor.fetchone()[0]
        return count > 0


def be_active(user_id, action):
    with sqlite3.connect('database.db') as connection:
        if not check_daily_activity(user_id):
            cursor = connection.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO user_actions (user_id, action, timestamp) VALUES (?, ?, ?)",
                           (user_id, action, timestamp))
            cursor.execute("INSERT INTO user_actions_month (user_id, action, timestamp) VALUES (?, ?, ?)",
                           (user_id, action, timestamp))
            connection.commit()
            return True
        else:
            return False


# Функция для получения статистики за вчерашний день
def get_yesterday_stats():
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_actions WHERE DATE(timestamp)=?",
                       (yesterday,))
        yesterday_count = cursor.fetchone()[0]
        return yesterday_count


# Функция для получения статистики за день
def get_daily_stats():
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM user_actions WHERE DATE(timestamp)=?", (today,))
        daily_count = cursor.fetchone()[0]
        return daily_count


# Функция для получения статистики за месяц
def check_monthly_activity(user_id):
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()
        current_month = datetime.now().strftime("%Y-%m")
        cursor.execute("SELECT COUNT(*) FROM user_actions_month WHERE user_id=? AND strftime('%Y-%m', timestamp)=?",
                       (user_id, current_month))
        count = cursor.fetchone()[0]
        return count > 0


def get_monthly_stats():
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()
        current_month = datetime.now().strftime("%Y-%m")
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_actions_month WHERE strftime('%Y-%m', timestamp)=?",
                       (current_month,))
        monthly_count = cursor.fetchone()[0]
        return monthly_count


def check_user(user_id):
    try:
        with sqlite3.connect('database.db') as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        logging.error(f"Error checking user: {e}")
        return False


def get_all_user_ids():
    user_ids = []
    try:
        with sqlite3.connect('database.db') as db:
            cursor = db.cursor()
            # Извлекаем все user_id из таблицы пользователей
            cursor.execute('SELECT user_id FROM users;')
            data = cursor.fetchall()
            # Проверяем, что данные действительно получены
            if data:
                user_ids = [user[0] for user in data]
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении всех идентификаторов пользователей: {e}")
    return user_ids


def get_users_count():
    try:
        with sqlite3.connect('database.db') as db:
            cursor = db.cursor()
            return cursor.execute('SELECT COUNT(*) FROM users;').fetchone()[0]
    except sqlite3.Error as e:
        logging.error(f"Error getting user count: {e}")
        return None


def get_user_profile(user_id):
    try:
        with sqlite3.connect('database.db') as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT user_id, balance, USER_STATUS FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                user_ids = result[0]
                balance = result[1]
                user_status = result[2]
                return user_ids, balance, user_status

            return None, None, None
    except Exception as e:
        logging.error(f"Error retrieving user profile: {e}")
        return None


def get_user_balance():
    try:
        with sqlite3.connect('database.db') as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT balance FROM users")
            result = cursor.fetchall()
            if result:
                balance = result[0]
                return balance
            return None
    except Exception as e:
        logging.error(f"Error retrieving user balance: {e}")
        return "Ошибка при получении баланса пользователя."


# STARTER PRO PREMIUM ULTRA MYTHIC
# SR PRO PM UA MC
def add_user(user_id):
    try:
        with sqlite3.connect("database.db") as db:
            cursor = db.cursor()
            # Проверяем, существует ли пользователь с таким user_id
            if check_user(user_id):
                return f"✅Пользователь с ID {user_id} уже является пользователем."
            else:
                b = 1
                status = 'SR'
                cursor.execute("INSERT INTO users (user_id, balance, USER_STATUS) "
                               "VALUES (?, ?, ?)", (user_id, b, status))
                db.commit()
                return f"✅Пользователь с ID {user_id} успешно добавлен в список пользователей."
    except sqlite3.IntegrityError:
        logging.info(f"User with ID {user_id} already exists.")
        return f"✅Пользователь с ID {user_id} уже является пользователем."
    except Exception as e:
        logging.error(f"Error adding user with ID {user_id}: {e}")
        return f"❌Ошибка при добавлении пользователя: {e}"


def add_admin(user_id):
    with sqlite3.connect("database.db") as db:
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO admins (user_id) VALUES (?)", (user_id,))
            db.commit()
            logging.info(f"User with ID {user_id} added to admins.")
            return f"✅Пользователь с ID {user_id} успешно добавлен в список администраторов."
        except sqlite3.IntegrityError:
            logging.warning(f"User with ID {user_id} already an admin.")
            return f"✅Пользователь с ID {user_id} уже является администратором."
        except Exception as e:
            logging.error(f"Error adding admin: {e}")
            return f"❌Ошибка при добавлении пользователя: {e}"


def is_admin(user_id):
    try:
        with sqlite3.connect('database.db') as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        logging.error(f"Error checking admin: {e}")
        return False


def remove_admin(user_id):
    try:
        with sqlite3.connect('database.db') as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            connection.commit()
            connection.close()
            logging.info(f"User with ID {user_id} removed from admins.")
            return f"✅Пользователь с ID {user_id} успешно удален из списка администраторов."
    except Exception as e:
        logging.error(f"Error removing user: {e}")
        return f"❌Ошибка при удалении пользователя: {e}"


def add_channel(channel_id, name, url):
    try:
        with sqlite3.connect('database.db') as connection:
            cursor = connection.cursor()

            success = cursor.execute('INSERT INTO channels (channel_id, name, url) VALUES (?, ?, ?)',
                                     (channel_id, name, url))

            if success:
                connection.commit()
                return f"CHANNEL ID {channel_id} успешно добавлен."
            else:
                return f"CHANNEL ID {channel_id} уже существует."
    except Exception as e:
        logging.error(f"Error adding channel: {e}")
    connection.close()


#add_channel(-1002148431155, '№1', 'https://t.me/dvbinsed')


def get_channel_ids():
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()

        cursor.execute('SELECT channel_id FROM channels')
        channel_ids = cursor.fetchall()
        return [channel_id[0] for channel_id in channel_ids]


def get_channel_info():
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()

        # Select the name and URL of all channels
        cursor.execute('SELECT name, url FROM channels')
        channels = cursor.fetchall()

    return channels
