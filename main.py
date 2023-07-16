import sqlite3
import telebot
from config import settings
import datetime as DT

from db import BotDB
BotDB_serials = BotDB('D:\.Working\Programming\SerialListener_bot\Databases\serials.db')
BotDB_bank = BotDB('Databases\\bank.db')
banker = settings['banker']

bot = telebot.TeleBot(settings['token'])

conn = sqlite3.connect('Databases\\bank.db')
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS accounts(
    user_id INTEGER PRIMARY KEY,
    user_name TEXT, 
    serial_number TEXT UNIQUE,
    bank_number TEXT UNIQUE,
    balance INTEGER,
    date DATETIME
    )""")
conn.commit()

cursor.execute("""CREATE TABLE IF NOT EXISTS bank(
	id INTEGER PRIMARY KEY,
	balance INTEGER,
	credit INTEGER,
    date DATETIME DEFAULT((DATETIME('now')))
    )""")
cursor.execute("INSERT or IGNORE INTO 'bank' ('id', 'balance', 'credit', 'date') VALUES (?,?,?,?)", (1, 0, 0, DT.datetime.date(DT.datetime.now())))
conn.commit()

@bot.message_handler(commands=['start'])
def start_message(message):
	bot.send_message(message.chat.id, 'Добро пожаловать, чтобы подключиться к банковской системе,'
									  ' введите команду:\n'
									  ' • /подключиться [серийный номер паспорта]\n'
									  ' • /п [серийный номер паспорта]')

@bot.message_handler(commands=['подключиться', 'Подключиться', 'п'])
def connect(message):
	get_user = message.from_user
	user_id = str(get_user.id)
	user_name = str(get_user.first_name)
	msg = message.text
	try:
		serial_number = str(msg.split()[1])
	except:
		bot.send_message(message.chat.id, 'Введите аргумент для команды через пробел\n'
										  'Например: /подключиться МР0КА252325')
	bank_number = user_id[:2] + user_name[:2] + 'b'
	if BotDB_bank.bank_number_exists(bank_number):
		bank_number = user_id[8:] + user_name[:2] + 'b'
	balance = 0
	date = DT.datetime.date(DT.datetime.now())

	if BotDB_serials.serial_exists(serial_number):
		userinfo_list = [user_id, user_name, serial_number, bank_number, balance, date]
		BotDB_bank.add_account(userinfo_list)
		bot.send_message(message.chat.id, 'Поздравляю, вы были подключены к системе банка! Ваш банковский номер: '
										  f'{bank_number}\n'
										  'Чтобы узнать подробности, введите команду:\n • /инфо'
										  '\n • /и')
	else:
		bot.send_message(message.chat.id, 'Такого серийного номера не существует')

@bot.message_handler(commands=['инфо', 'Инфо', 'и'])
def bank_info(message):
	get_user = message.from_user
	user_id = str(get_user.id)
	user_name = str(get_user.first_name)
	try:
		bank_number = BotDB_bank.get_bank_number_by_id(user_id)
		date = BotDB_bank.get_date_by_id(user_id)
		balance = BotDB_bank.get_balance_by_id(user_id)

		bot.send_message(message.chat.id, f'Привет, *{user_name}*!\n'
										f'Ваш банк. номер: *{bank_number}*\n'
										f'Ваш баланс:*{balance}* гарм. марок\n'
										f'Последнее изменение: *{date}*\n',
										parse_mode="Markdown")
	except:
		bot.send_message(message.chat.id, 'Вы не зарегистрированы, напишите /start')

@bot.message_handler(commands=['перевести', 'Перевести', 'пер'])
def transfer_money(message):
	msg = message.text
	get_user = message.from_user
	user_id = str(get_user.id)
	user_name = str(get_user.first_name)
	amount = int(msg.split()[1])

	balance_of_sender = BotDB_bank.get_balance_by_id(user_id)
	balance_of_receiving = BotDB_bank.get_balance_by_id(user_id)

	bank_number_of_receiving = str(msg.split()[2])
	bank_number_of_sender = BotDB_bank.get_bank_number_by_id(user_id)
	user_name_of_receiving = BotDB_bank.get_name_by_bank_number(bank_number_of_receiving)

	user_id_of_receiving = BotDB_bank.get_id_by_bank_number(bank_number_of_receiving)
	if user_id != user_id_of_receiving and amount <= balance_of_sender and balance_of_sender > 0:
		BotDB_bank.transfer_money(user_id, user_id_of_receiving, amount, balance_of_sender, balance_of_receiving)
		bot.send_message(message.chat.id, f'Успешно переведено {amount} марок!\n'
										  f'Итого: {balance_of_sender - amount}\n'
										  f'Получатель: {user_name_of_receiving}, {bank_number_of_receiving}')
		bot.send_message(user_id_of_receiving, f'Вам перевели {amount} марок!\n'
											   f'Итого: {amount + balance_of_receiving}\n'
											   f'Отправитель: {user_name}, {bank_number_of_sender}')
	else:
		bot.send_message(message.chat.id, 'Не удалось. Возможные причины:\n'
										  ' • Вы отправили деньги сами себе'
										  ' • Кол-во отправленных денег больше имеющихся'
										  ' • У вас нет денег на счету')

@bot.message_handler(commands=['вернуть', 'Вернуть', 'в'])
def return_money(message):
	get_user = message.from_user
	user_id = str(get_user.id)
	user_name = str(get_user.first_name)
	user_bank_number = BotDB_bank.get_bank_number_by_id(user_id)
	bank_id = banker
	msg = message.text
	amount = int(msg.split()[1])
	bank_balance = BotDB_bank.get_bank_balance()
	user_balance = BotDB_bank.get_balance_by_id(user_id)
	if amount <= user_balance and user_balance > 0:
		BotDB_bank.give_back_money(amount, bank_balance, user_id, user_balance)
		bot.send_message(message.chat.id, f'Успешно вернулись в банк {amount} марок!\n'
										  f'Было: {user_balance}\n'
										  f'Стало: {user_balance - amount} гарм. марок')
		bot.send_message(bank_id, f'Успешно вернулись в банк {amount} марок!\n'
								  f'Было в банке: {bank_balance}\n'
								  f'Стало в банке: {bank_balance + amount} гарм. марок\n'
								  f'Вернувший: {user_name}, {user_bank_number}')
	else:
		bot.send_message(message.chat.id, 'Не удалось. Возможные причины:\n'
										  ' • Кол-во отправленных денег больше имеющихся'
										  ' • У вас нет денег на счету')

@bot.message_handler(commands=['печатать', 'Печатать', 'печ'])
def print_money(message):
	get_user = message.from_user
	user_id = str(get_user.id)
	msg = message.text
	if user_id == banker:
		amount = int(msg.split()[1])
		balance = BotDB_bank.get_bank_balance()
		BotDB_bank.add_bank_money(amount, balance)
		bot.send_message(message.chat.id, f'Успешно напечатано {amount} марок!\n'
										  f'Было: {balance}\n'
										  f'Итого: {balance + amount} гарм. марок')
	else: pass

@bot.message_handler(commands=['сжечь', 'Сжечь', 'с'])
def burn_money(message):
	get_user = message.from_user
	user_id = str(get_user.id)
	msg = message.text
	if user_id == banker:
		amount = int(msg.split()[1])
		balance = BotDB_bank.get_bank_balance()
		BotDB_bank.burn_bank_money(amount, balance)
		bot.send_message(message.chat.id, f'Успешно сожжено {amount} марок!\n'
										  f'Было: {balance}\n'
										  f'Итого: {balance - amount} гарм. марок')
	else: pass

@bot.message_handler(commands=['банк', 'Банк', 'б'])
def bank_balance(message):
	get_user = message.from_user
	user_id = str(get_user.id)
	msg = message.text
	if user_id == banker:
		balance = BotDB_bank.get_bank_balance()
		bot.send_message(message.chat.id, f'Баланс банка: {balance} гарм. марок')
	else: pass

@bot.message_handler(commands=['дать', 'Дать', 'д'])
def give_money(message):
	get_user = message.from_user
	user_id = str(get_user.id)
	msg = message.text
	if user_id == banker:
		amount = int(msg.split()[1])
		bank_number = msg.split()[2]
		user_id = BotDB_bank.get_id_by_bank_number(bank_number)
		bank_balance = BotDB_bank.get_bank_balance()
		user_balance = BotDB_bank.get_balance_by_id(user_id)
		user_name = BotDB_bank.get_name_by_bank_number(bank_number)

		if bank_balance > 0 and amount <= bank_balance:
			BotDB_bank.give_bank_money(amount, bank_balance, user_id, user_balance)
			bot.send_message(message.chat.id, f'Успешно передано {amount} марок!\n'
											  f'Было в банке: {bank_balance}\n'
											  f'Стало в банке: {bank_balance - amount}\n'
											  f'Было у {user_name}, {bank_number}: {user_balance}\n'
											  f'Стало у {user_name}, {bank_number}: {user_balance + amount} гарм. марок')

			bot.send_message(user_id, f'Банк: спешно получено {amount} марок!\n'
									  f'Ваш баланс: {user_balance + amount}\n')
		else:
			bot.send_message(message.chat.id, 'На счету банка недостаточно денег. Для перевода - напечатайте ещё.')
	else: pass

@bot.message_handler(commands=['помощьб', 'Помощьб', 'пб'])
def help_list(message):
	get_user = message.from_user
	user_id = str(get_user.id)
	msg = message.text
	if user_id == banker:
		bot.send_message(message.chat.id, 'Помощь для банкира:\n'
										  ' • /банк, /б - посмотреть счёт банка\n'
										  ' • /печатать, /п [кол-во денег] - напечатать деньги\n'
										  ' • /сжечь, /с [кол-во денег] - сжечь деньги\n'
										  ' • /помощьб, /пб - помощь для банкира\n'
										  ' • /дать, /д - дать деньги участнику')
	else: pass

@bot.message_handler(commands=['помощь', 'Помощь'])
def help_list(message):
	bot.send_message(message.chat.id, "Помощь:\n"
									  ' • /подключиться, /п [серийный номер паспорта]\n'
									  ' • /инфо, /и\n'
									  ' • /перевести, /пер [количество] [банковский номер получателя]\n'
									  ' • /вернуть, /в [количество] - вернуть деньги банку')

bot.infinity_polling()