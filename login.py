import datetime

from api_helper import NorenApiPy
import logging
from ft_token import FTToken
# enable dbug to see request and responses
logging.basicConfig(level=logging.INFO)


# start of our program
api = NorenApiPy()

# set token and user id
# paste the token generated using the login flow described
# in LOGIN FLOW of https://pi.flattrade.in/docs
# usersession = 'api token'
token = FTToken()
usersession = token.generate_token()
userid = token.user_id
userpasswd = token.passwd

_ = api.set_session(userid=userid, password=userpasswd, usertoken=usersession)

ret = api.get_limits()
print(ret)
# cash = float(api.get_limits()['cash'])
# exch = 'NSE'
# token = '9552'
# price = float(api.get_quotes(exchange=exch, token=token)['lp'])
# # print(ret['lp'])
# # print(int(cash))
# print(type(cash))
# print(type(price))
# max_order = int(cash/price)
# print(max_order)
# # print(ret1)

# order_data = api.single_order_history(orderno='24061000200731')
# print(order_data)
# # print(type(order_data[1]['exch_tm']))
# order_time = order_data[1]['exch_tm']
# order_age = datetime.datetime.now() - datetime.datetime.strptime(order_time, '%d-%m-%Y %H:%M:%S')
# print(order_age.seconds)