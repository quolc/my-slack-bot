from slackbot.bot import Bot

from slackbot_settings import API_TOKEN

def main():
    # RTM client for reaction
    bot = Bot()
    bot.run()

if __name__ == '__main__':
    main()

