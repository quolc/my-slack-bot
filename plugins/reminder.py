from slackbot.bot import listen_to, respond_to
from slacker import Slacker
from slackbot_settings import API_TOKEN, username, general_channel

import threading
import time
import datetime
import sqlite3

###########################
# constants
###########################

units = {
    'second' : 1,
    'minute' : 60,
    'hour'   : 3600,
    'day'    : 3600 * 24,
    'week'   : 3600 * 24 * 7,
}
dbname = 'database.db'


###########################
# internal functions
###########################

# register new item
def _register_item(remind_at, body, channel):
    conn = sqlite3.connect(dbname)
    conn.text_factory = str
    c = conn.cursor()

    sql = 'insert into reminders(created_at, remind_at, message, channel) values (?,?,?,?)'
    c.execute(sql, [datetime.datetime.now(), remind_at, body, channel])

    conn.commit()
    conn.close()
    print('I\'ll post "{}" {} seconds later.'.format(body, remind_at, channel))


###########################
# slack reaction funcitons
###########################

# register new item
@listen_to('(.*) \(remind (.*) later\)')
def register_reminder(message, body, time):
    # calculate remaining time to remind
    try:
        number, unit = time.split()
        number = float(number)
        if unit[-1] == 's':
            unit = unit[0:-1]
        seconds = int(number * units[unit])
        d = datetime.datetime.now()
        d = d + datetime.timedelta(seconds=seconds)

        # register to reminder pool
        _register_item(d, body, message.channel._body['name'])

        # reaction
        message.react('+1')
    except Exception as e:
        message.react('question')
        print(e.message)

# list registered items
@respond_to('reminder list')
def list_reminder(message):
    conn = sqlite3.connect(dbname)
    conn.text_factory = str
    c = conn.cursor()

    c.execute( "select * from reminders" )
    l = c.fetchall()
    mes = "there are {} items in reminder list:".format(len(l))
    for (_, time, body, channel) in l:
        mes = mes + "\n- \"{}\" will be remided at {} (registered in #{})".format(
                body, time, channel)
    message.reply(mes)

    c.close()
    conn.close()


###########################
# start execution
###########################

class PollingThread(threading.Thread):
    def __init__(self, dbname):
        super(PollingThread, self).__init__()
        self.client = Slacker(API_TOKEN)

    def run(self):
        print('======== start polling thread for reminder ========')
        while True:
            time.sleep(5)

            # search item to remind
            conn = sqlite3.connect(dbname)
            conn.text_factory = str
            c = conn.cursor()
            c.execute( "select * from reminders" )
            l = c.fetchall()

            for (item_id, created_at, remind_at, body, channel) in l:
                dt = datetime.datetime.strptime(remind_at, '%Y-%m-%d %H:%M:%S.%f')
                if dt < datetime.datetime.now():
                    print('posting "{}"'.format(body))
                    self.client.chat.post_message(general_channel,
                            "{} {} (registered at {})".format(username, body, created_at),
                            as_user=True, link_names=[username])
                    # delete item
                    c.execute( 'delete from reminders where id=?', (item_id,) )
                    conn.commit()

            c.close()
            conn.close()

t = PollingThread(dbname)
t.start()

