import telebot
from pycoingecko import CoinGeckoAPI
from app.utils import load_dicts
from app.globals import cg, coins, bot, dicts, fiat


def init_bot(token):
    global bot, coins, dicts, cg
    cg = CoinGeckoAPI()
    with open('proxy', 'r') as proxy_file:
        proxies = proxy_file.read().splitlines()
        telebot.apihelper.proxy = {'https': 'http://' + x for x in proxies}
    for x in cg.get_coins_list():
        coins[x['symbol']] = x['id']
        coins[x['id']] = x['id']
    load_dicts()
    bot = telebot.TeleBot(token)
    from app import handlers
