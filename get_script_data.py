from api_helper import NorenApiPy, get_time
import logging
import time
import pandas as pd
from ft_token import FTToken
from datetime import datetime, timedelta



# sample
logging.basicConfig(level=logging.INFO)

# flag to tell us if the websocket is open
socket_opened = False


# application callbacks
# def event_handler_order_update(message):
#     print("order event: " + str(message))
#
#
# def event_handler_quote_update(message):
#     # e   Exchange
#     # tk  Token
#     # lp  LTP
#     # pc  Percentage change
#     # v   volume
#     # o   Open price
#     # h   High price
#     # l   Low price
#     # c   Close price
#     # ap  Average trade price
#
#     print("quote event: {0}".format(time.strftime('%d-%m-%Y %H:%M:%S')) + str(message))


# def open_callback():
#     global socket_opened
#     socket_opened = True
#     print('app is connected')
#
#     # api.subscribe('NSE|11630')
#     # api.subscribe(['NSE|22', 'BSE|522032'])
#     api.subscribe('NSE|1363')


# end of callbacks

# def get_time(time_string):
#     data = time.strptime(time_string, '%d-%m-%Y %H:%M:%S')
#
#     return time.mktime(data)


# start of our program
api = NorenApiPy()

# set token and user id
# paste the token generated using the login flow described
# in LOGIN FLOW of https://pi.flattrade.in/docs

token = FTToken()
usersession = token.generate_token()
userid = token.user_id
userpasswd = token.passwd

# usersession = '3428f5f5c5d60057b64a3548612dd3517f59a681aa6f931c585d76cd854e3b6d'
# userid = 'FT035389'

ret = api.set_session(userid=userid, password=userpasswd, usertoken=usersession)

count = 100
exch = 'NSE'
token = '1997'

while count > 0:
    ret = api.get_quotes(exchange=exch, token=token)
    print(ret)
    count -= 1

# if ret != None:
#     while True:
#         print('f => find symbol')
#         print('m => get quotes')
#         print('p => contract info n properties')
#         print('v => get 1 min market data')
#         print('t => get today 1 min market data')
#         print('d => get daily data')
#         print('o => get option chain')
#         print('s => start_websocket')
#
#         print('q => quit')
#
#         prompt1 = input('what shall we do? ').lower()
#
#         if prompt1 == 'v':
#             csec = datetime.now() - timedelta(hours=0, minutes=0)
#             print(csec.strftime('%d-%m-%Y %H:%M') + ":00")
#             start_time1 = csec.strftime('%d-%m-%Y %H:%M') + ":00"
#             # start_time = "05-06-2024 15:27:00"
#             # if start_time1 == start_time:
#             #     print("OK")
#             # print(type(start_time))
#             # end_time = time.time()
#             # start_time = csec.strftime('%d-%m-%y %H:%M:%S')
#
#             start_secs = get_time(start_time1)
#             # start_secs1 = get_time(start_time1)
#             print(start_secs)
#             # print(start_secs1)
#
#             end_time = get_time(start_time1)
#             # end_time = csec.strftime('%d-%m-%Y %H:%M:00')
#             # print(type(end_time))
#             ret = api.get_time_price_series(exchange='NSE', token='9552', starttime=start_secs, endtime=end_time)
#
#
#             df = pd.DataFrame.from_dict(ret)
#             # print(df)
#             # print(f'{start_secs} to {end_time}')
#
#         elif prompt1 == 't':
#             ret = api.get_time_price_series(exchange='NSE', token='9552')
#
#             df = pd.DataFrame.from_dict(ret)
#             # print(df)
#             print(f"Pervious Opening: {ret[0]['into']}")
#             print(f"Pervious Closing: {ret[0]['intc']}")
#
#
#         elif prompt1 == 'f':
#             exch = 'NFO'
#             query = 'NIFTY 30MAY24 23600 CE'
#             ret = api.searchscrip(exchange=exch, searchtext=query)
#             print(ret)
#
#             if ret != None:
#                 symbols = ret['values']
#                 for symbol in symbols:
#                     print('{0} token is {1}'.format(symbol['tsym'], symbol['token']))
#
#         elif prompt1 == 'd':
#             exch = 'NSE'
#             tsym = 'HINDALCO-EQ'
#             ret = api.get_daily_price_series(exchange=exch, tradingsymbol=tsym, startdate=0)
#             print(ret)
#
#         elif prompt1 == 'p':
#             exch = 'NSE'
#             token = '9552'
#             ret = api.get_security_info(exchange=exch, token=token)
#             print(ret)
#
#         elif prompt1 == 'm':
#             exch = 'NSE'
#             token = '1997'
#             ret = api.get_quotes(exchange=exch, token=token)
#             print(ret)
#         elif prompt1 == 'o':
#             exch = 'NSE'
#             tsym = 'HINDALCO-EQ'
#             chain = api.get_option_chain(exchange=exch, tradingsymbol=tsym, strikeprice=23600, count=1)
#             print(chain)
#             chainscrips = []
#             for scrip in chain['values']:
#                 scripdata = api.get_quotes(exchange=scrip['exch'], token=scrip['token'])
#                 chainscrips.append(scripdata)
#
#             print(chainscrips)
#
#         elif prompt1 == 's':
#             if socket_opened == True:
#                 print('websocket already opened')
#                 continue
#             ret = api.start_websocket(order_update_callback=event_handler_order_update,
#                                       subscribe_callback=event_handler_quote_update, socket_open_callback=open_callback)
#             print(ret)
#
#         else:
#             ret = api.logout()
#             print(ret)
#             print('Fin')  # an answer that wouldn't be yes or no
#             break
