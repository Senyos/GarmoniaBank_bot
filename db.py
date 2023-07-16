import sqlite3
import datetime as DT

class BotDB:

    def __init__(self, db_file):
        """Инициализация соединения с БД"""
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def serial_exists(self, serial):
        """Проверяем, есть ли серийник в БД"""
        result = self.cursor.execute(f"SELECT serial FROM 'serials' WHERE trim(serial) LIKE '{serial}';")
        return bool(len(result.fetchall()))

    def name_exists(self, name):
        """Проверяем, есть ли имя в БД"""
        result = self.cursor.execute(f"SELECT name FROM 'serials' WHERE trim(name) LIKE '{name}';")
        return bool(len(result.fetchall()))

    def get_name_by_serial(self, serial):
        """Получаем имя по серийнику"""
        result = self.cursor.execute(f"SELECT name FROM 'serials' WHERE trim(serial) LIKE '{serial}';")
        return result.fetchone()[0]

    def get_serial_by_name(self, name):
        """Получаем серийник по имени"""
        result = self.cursor.execute(f"SELECT serial FROM 'serials' WHERE trim(name) LIKE '{name}';")
        return result.fetchone()[0]

    def add_serial(self, serial, name):
        """Добавляем серийник в БД"""
        self.cursor.execute("INSERT INTO 'serials' ('serial', 'name') VALUES (?,?)", (serial, name))
        return self.conn.commit()


    def bank_number_exists(self, bank_number):
        """Проверяем, есть ли банк. номер в БД"""
        result = self.cursor.execute(f"SELECT bank_number FROM 'accounts' WHERE trim(bank_number) LIKE '{bank_number}';")
        return bool(len(result.fetchall()))

    def get_bank_number_by_id(self, user_id):
        """Получаем банк. номер по айди"""
        result = self.cursor.execute(f"SELECT bank_number FROM 'accounts' WHERE trim(user_id) LIKE '{user_id}';")
        return result.fetchone()[0]

    def get_date_by_id(self, user_id):
        """Получаем дату по айди"""
        result = self.cursor.execute(f"SELECT date FROM 'accounts' WHERE trim(user_id) LIKE '{user_id}';")
        return result.fetchone()[0]

    def get_balance_by_id(self, user_id):
        """Получаем баланс по айди"""
        result = self.cursor.execute(f"SELECT balance FROM 'accounts' WHERE trim(user_id) LIKE '{user_id}';")
        return result.fetchone()[0]

    def get_name_by_bank_number(self, bank_number):
        result = self.cursor.execute(f"SELECT user_name FROM 'accounts' WHERE trim(bank_number) LIKE '{bank_number}';")
        return result.fetchone()[0]

    def get_id_by_bank_number(self, bank_number):
        """Получаем айди по банк номеру"""
        result = self.cursor.execute(f"SELECT user_id FROM 'accounts' WHERE trim(bank_number) LIKE '{bank_number}';")
        return result.fetchone()[0]

    def add_account(self, userinfo_list):
        self.cursor.execute("INSERT or IGNORE INTO accounts VALUES (?,?,?,?,?,?)", userinfo_list)
        return self.conn.commit()

    def transfer_money(self, user_id_sender, user_id_receiving, amount, balance_if_sender, balance_of_receiving):
        """Переводим деньги"""
        new_balance_s = balance_if_sender - amount
        new_balance_r = balance_of_receiving + amount

        self.cursor.execute("UPDATE 'accounts' SET balance=? WHERE user_id LIKE ?",
                            (new_balance_s, user_id_sender))
        self.cursor.execute("UPDATE 'accounts' SET balance=? WHERE user_id LIKE ?",
                            (new_balance_r, user_id_receiving))
        return self.conn.commit()

    def get_bank_balance(self):
        result = self.cursor.execute(f"SELECT balance FROM 'bank' WHERE trim(id) LIKE '1';")
        return result.fetchone()[0]

    def add_bank_money(self, amount, balance):
        new_balance = amount + balance
        self.cursor.execute("UPDATE 'bank' SET balance=?, date=? WHERE id LIKE ?",
                            (new_balance, DT.datetime.date(DT.datetime.now()), 1))
        return self.conn.commit()

    def burn_bank_money(self, amount, balance):
        new_balance = balance - amount
        self.cursor.execute("UPDATE 'bank' SET balance=?, date=? WHERE id LIKE ?",
                            (new_balance, DT.datetime.date(DT.datetime.now()), 1))
        return self.conn.commit()

    def give_bank_money(self, amount, bank_balance, user_id, user_balance):
        new_bank_balance = bank_balance - amount
        new_user_balance = user_balance + amount
        self.cursor.execute("UPDATE 'bank' SET balance=?, date=? WHERE id LIKE ?",
                            (new_bank_balance, DT.datetime.date(DT.datetime.now()), 1))
        self.cursor.execute("UPDATE 'accounts' SET balance=?, date=? WHERE user_id LIKE ?",
                            (new_user_balance, DT.datetime.date(DT.datetime.now()), user_id))
        return self.conn.commit()

    def give_back_money(self, amount, bank_balance, user_id, user_balance):
        new_bank_balance = bank_balance + amount
        new_user_balance = user_balance - amount
        self.cursor.execute("UPDATE 'bank' SET balance=?, date=? WHERE id LIKE ?",
                            (new_bank_balance, DT.datetime.date(DT.datetime.now()), 1))
        self.cursor.execute("UPDATE 'accounts' SET balance=?, date=? WHERE user_id LIKE ?",
                            (new_user_balance, DT.datetime.date(DT.datetime.now()), user_id))
        return self.conn.commit()

    def close(self):
        """Закрытие соединения с БД"""
        self.conn.close