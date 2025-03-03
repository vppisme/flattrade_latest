# from api_helper import NorenApiPy
# from time import sleep
from datetime import datetime
from a_set_margin import get_margin
import logging
from os import path, makedirs


# logger = logging.getLogger(__name__)
# print(logger)
SLMM = 10
BUY_REJECT_RESET = 23


class Trade:
    def __init__(self, api, tradingsymbol, script_token, account_id, password, sell_margin=0.5, exchg='NSE', qty=1,
                 buy_margin=0.5, new_buy_value_margin=0.5):
        self.api = api
        self.userid = account_id
        self.password = password
        # self.token = script_token

        self.script_data = {'exchange': exchg, 'trading_symbol': tradingsymbol, 'script_token': script_token,
                            'sell_margin': sell_margin, 'buy_margin': buy_margin,
                            'new_buy_value_margin': new_buy_value_margin, 'to_order': True, 'qty': qty,
                            'sell_value': 0.0, 'buy_value': 0.0, 'no_of_order': 0, 'buy_value_0': 0.0,
                            'buy_order_no': None, 'buy_order_status': None, 'buy_order_time': None,
                            'no_buy_order': 0, 'sell_order_no': None, 'sell_order_status': None,
                            'sell_order_time': None, 'no_sell_order': 0, 'ltp': 0.0, 'ltt': None, 'ltd': None,
                            'last_sell_value': 0.0, 'today_high': 0.0, 'today_low': 0.0,
                            'previous_tick_open_value': 0.0, 'previous_tick_close_value': 0.0,
                            'start_time': None, 'last_order_age': 0, 'too_high_diff': 0.0,
                            'max_buy_order_update_margin': 5.0, 'stop_loss_margin': 5.0,
                            'is_sell_order_placed': 0, 'act_id': account_id, 'trade_cycle': 0,
                            'buy_order_reject_reset_counter': 0}

        # Set Script Trade History File to track trading history
        # Ensure the directory exists, create it if it doesn't
        # Get the directory of the current script
        script_directory = path.dirname(path.abspath(__file__))
        history_dir = path.join(script_directory, '../history')

        # Log directory
        log_dir = path.join(script_directory, '../log')

        # Ensure the directory exists
        if not path.exists(log_dir):
            makedirs(log_dir)
        if not path.exists(history_dir):
            makedirs(history_dir)

        self.history_file = path.join(history_dir,
                                  f'a_{self.script_data["trading_symbol"]}_trade_history_{datetime.now().strftime("%d-%m-%Y")}.txt')

        # Function to set up per-script loggers
        def setup_script_logger():
            script_log_file = path.join(log_dir,
                                        'a_trade_' + f'_{self.script_data["trading_symbol"]}_' + datetime.now().strftime('%d-%m-%Y') + '.log')

            # Create a logger for the script
            script_logger_ = logging.getLogger(f"{self.script_data['trading_symbol']}_logger")
            script_logger_.setLevel(logging.INFO)

            # Create file handler for the script log
            script_file_handler = logging.FileHandler(script_log_file)
            script_file_handler.setLevel(logging.INFO)

            # Use the same formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            script_file_handler.setFormatter(formatter)

            # Add the file handler to the script logger
            script_logger_.addHandler(script_file_handler)

            return script_logger_

        # Set up the logger for the trade instance
        self.logger = setup_script_logger()

    def get_buy_order_no(self):
        return self.script_data['buy_order_no']

    def get_buy_order_time(self):
        return self.script_data['buy_order_time']

    def get_buy_value(self):
        return self.script_data['buy_value']

    def get_sell_order_no(self):
        return self.script_data['sell_order_no']

    def get_sell_order_time(self):
        return self.script_data['sell_order_time']

    def set_buy_sell_margin(self):
        ltp = self.get_ltp()
        self.script_data['buy_margin'] = get_margin(ltp)['buy_margin']
        min_sell_margin = get_margin(ltp)['sell_margin']
        if self.script_data['sell_margin'] < min_sell_margin:
            self.script_data['sell_margin'] = min_sell_margin
        self.script_data['new_buy_value_margin'] = get_margin(ltp)['new_buy_value_margin']
        self.script_data['max_buy_order_update_margin'] = get_margin(ltp)['max_buy_order_update_margin']
        self.script_data['too_high_diff'] = get_margin(ltp)['too_high_diff']
        self.script_data['stop_loss_margin'] = self.script_data['sell_margin'] * SLMM

    def get_script_token(self):
        return self.script_data['script_token']


    def get_quote(self):
        is_get_quote = False
        quote = None
        while not is_get_quote:
            quote = self.api.get_quotes(exchange=self.script_data['exchange'], token=self.script_data['script_token'])
            if quote is not None:
                is_get_quote = True
        return quote


    def get_ltp(self):
        # quote = self.get_quote()
        # self.logger.info(self.script_data['ltp'])
        return self.script_data['ltp']

    def get_ltd(self):
        # quote = self.get_quote()
        return self.script_data['ltd']

    def get_ltt(self):
        # quote = self.get_quote()
        return self.script_data['ltt']


    def get_buyvalue_ltp_diff(self):
        return  round(self.script_data['buy_value'] - self.script_data['ltp'], 2)


    def get_sell_margin(self):
        return self.script_data['sell_margin']


    def get_stop_loss_margin(self):
        return self.script_data['stop_loss_margin']

    def get_available_margin(self):
        # _ = self.api.set_session(userid=self.userid, password=self.password, usertoken=self.script_data['script_token'])
        limits = self.api.get_limits()
        try:
            margin_used = float(limits['marginused'])
        except KeyError:
            margin_used = 0.0
        # print(f"----------------------->>>>> {limits}")
        available_margin_ = round(float(limits['cash']) - margin_used, 2)
        self.logger.info(f"INFO : Available Margin Limit is Rs {available_margin_}")
        return available_margin_


    def set_ltp(self):
        quote = self.get_quote()
        # self.logger.info(quote)
        self.script_data['ltp']  = float(quote['lp'])
        self.script_data['ltt'] = quote['ltt']
        self.script_data['ltd'] = quote['ltd']


    def set_previous_min_data(self, start_time, end_time):
        is_get_previous_data = False
        previous_min_data = None
        while not is_get_previous_data:
            previous_min_data = self.api.get_time_price_series(exchange=self.script_data['exchange'],
                                                               token=self.script_data['script_token'],
                                                               starttime=start_time, endtime=end_time)
            # self.logger.info(previous_min_data)
            if previous_min_data is not None:
                is_get_previous_data = True
        # self.logger.info(previous_min_data)

        self.script_data['previous_tick_open_value'] = float(previous_min_data[0]['into'])
        self.script_data['previous_tick_close_value'] = float(previous_min_data[0]['intc'])
        return

    def set_today_hl(self):
        # script_data = self.api.get_quotes(exchange=self.script_data['exchange'],
        #                                   token=self.script_data['script_token'])
        script_data = self.get_quote()
        self.script_data['today_high'] = float(script_data['h'])
        self.script_data['today_low'] = float(script_data['l'])
        return

    def print_ltp(self):
        self.logger.info(f"INFO : {self.script_data['trading_symbol']} - LTP is self.script_data['ltp']")
        return

    def get_script_name(self):
        # self.logger.info(self.script_data)
        return self.script_data['trading_symbol']

    def print_script(self):
        self.logger.info(f"INFO : Script Name - {self.get_script_name()}")
        return

    def get_trade_cycle(self):
        return self.script_data['trade_cycle']

    def is_update_buy_order_further(self):
        if self.script_data['ltp'] - self.script_data['buy_value_0'] > self.script_data['max_buy_order_update_margin']:
            self.logger.info(f"WARN : {self.script_data['trading_symbol']} - Script Value has been raised too high to update Buy Value further. ")
            return False
        return True

    def buy_order_value_update(self):
        if self.script_data['ltp'] - self.script_data['buy_value'] > self.script_data['new_buy_value_margin']:
            new_buy_value = round(self.script_data['ltp'] - self.script_data['buy_margin'], 2)
            if self.is_update_buy_order_further():
                try:
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Modifying Buy Order to new buy value {new_buy_value}")
                    _ = self.api.modify_order(exchange=self.script_data['exchange'],
                                              tradingsymbol=self.script_data['trading_symbol'],
                                              orderno=self.script_data['buy_order_no'],
                                              newquantity=self.script_data['qty'],
                                              newprice_type='LMT',
                                              newprice=new_buy_value)
                    self.script_data['buy_value'] = new_buy_value
                    self.script_data['sell_value'] = round(new_buy_value + self.script_data['sell_margin'], 2)
                except Exception:
                    raise Exception("ERROR : An error occurred in updating a new value to Buy Order")


    def check_buy_order_status(self):
        if self.script_data['buy_order_no'] is not None:
            try:
                is_buy_order_status = False
                buy_order_status = None
                self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Checking buy order status - check_buy_order_status()")
                while not is_buy_order_status:
                    buy_order_status = self.api.single_order_history(orderno=self.script_data['buy_order_no'])
                    if buy_order_status is not None:
                        is_buy_order_status = True

                self.logger.info(f"INFO : {self.script_data['trading_symbol']} -  check_buy_order_status() - script_data - {self.script_data} ")
                self.script_data['buy_order_status'] = buy_order_status[0]['status']

                if self.script_data['buy_order_status'] == 'OPEN':
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_buy_order_status() - buy order - OPEN")
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Buy order with ID {self.script_data['buy_order_no']}"
                          f" is pending - check_buy_order_status()")
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Checking buy_order_value_update - check_buy_order_status() -> buy_order_value_update()")
                    self.buy_order_value_update()
                    return self.script_data['buy_order_status']

                elif self.script_data['buy_order_status'] == 'COMPLETE':
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_buy_order_status() - buy order - COMPLETE")
                    self.script_data['buy_order_time'] = buy_order_status[0]['exch_tm']
                    self.script_data['no_of_order'] = self.script_data['qty']
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Buy order with ID {self.script_data['buy_order_no']} is COMPLETE")
                    # # Read the file and modify the specified line
                    # with open(self.history_file, 'r') as file:
                    #     lines = file.readlines()
                    # # Modify lines as needed
                    # # TS = Trade Start, TB = Trade Bought, TC = Trade Complete
                    # is_line_found = False
                    # for i, line in enumerate(lines):
                    #     if line.startswith(self.script_data['trading_symbol']) and line.strip().endswith("TS"):
                    #         lines[i] = line.replace("-TS", "-TB")
                    #         is_line_found = True
                    #         break
                    # if is_line_found:
                    #     # Write the modified lines back to the file
                    #     with open(self.history_file, 'w') as file:
                    #         file.writelines(lines)

                    # Read and modify the last line of the file
                    with open(self.history_file, 'r+') as file:
                        lines = file.readlines()  # Read all lines to find the last line
                        if lines:  # Ensure the file is not empty
                            last_line = lines[-1].strip()  # Get the last line
                            if last_line.startswith(self.script_data['trading_symbol']) and last_line.endswith("TS"):
                                # Modify the last line
                                lines[-1] = last_line.replace("-TS", "-TB") + '\n'
                                file.seek(0)  # Move to the beginning of the file
                                file.writelines(lines)  # Rewrite the modified content

                    if self.script_data['sell_order_status'] is None and self.script_data['to_order'] == 0:
                        self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Placing a sell order against a buy order {self.script_data['buy_order_no']}")
                        self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_buy_order_status() -> do_sell()")
                        self.do_sell()
                    return self.script_data['buy_order_status']
                elif self.script_data['buy_order_status'] == 'REJECTED':
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_buy_order_status() - buy order - REJECTED")
                    self.logger.info(f"WARNING : {self.script_data['trading_symbol']} - Buy order with ID {self.script_data['buy_order_no']} is REJECTED")
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - ACTION_TODO : Please check reason for buy order rejection.")
                    self.logger.info(f"INFO :  {self.script_data['trading_symbol']} - INFO : Reject_Reset_Count is {self.script_data['buy_order_reject_reset_counter']}")
                    self.script_data['buy_order_reject_reset_counter'] += 1
                    if self.script_data['buy_order_reject_reset_counter'] > BUY_REJECT_RESET:
                        self.logger.info(f"INFO : {self.script_data['trading_symbol']} - INFO : Resetting Buy Order Status to None")
                        self.script_data['buy_order_status'] = None
                        self.script_data['buy_order_reject_reset_counter'] = 0
                        # self.reset_value()
                    return self.script_data['buy_order_status']
                else:
                    return self.script_data['buy_order_status']

            except Exception:
                raise Exception(f"ERROR : {self.script_data['trading_symbol']} - An error occurred in getting status of a new Buy Order")
        else:
            self.logger.info(f"INFO : {self.script_data['trading_symbol']} - There is no Buy order placed.")
            return None

    def  update_sell_order(self, new_sell_value):
        self.logger.info(f"WARN : {self.script_data['trading_symbol']} - Script value is moving downwards."
                   " So lowering sell value to execute sell order.")
        try:
            _ = self.api.modify_order(exchange=self.script_data['exchange'],
                                      tradingsymbol=self.script_data['trading_symbol'],
                                      orderno=self.script_data['sell_order_no'],
                                      newquantity=self.script_data['qty'],
                                      newprice_type='LMT',
                                      newprice=new_sell_value)

        except Exception:
            raise Exception(f"ERROR : {self.script_data['trading_symbol']} - an error occurred in updating sell order")

    def sell_order_value_update(self):
        if (self.script_data['buy_value'] - self.script_data['ltp'] > self.script_data['stop_loss_margin'] and
                self.script_data['is_sell_order_placed'] == 1):
            self.logger.info(f"WARN : {self.script_data['trading_symbol']} - Script value is moving too low to make profit."
                  " So sell script at Market Price to control loss.")
            try:
                _ = self.api.modify_order(exchange=self.script_data['exchange'],
                                          tradingsymbol=self.script_data['trading_symbol'],
                                          orderno=self.script_data['sell_order_no'],
                                          newquantity=self.script_data['qty'],
                                          newprice_type='MKT')

            except Exception:
                raise Exception(f"ERROR : {self.script_data['trading_symbol']} - an error occurred in updating sell order")
            # finally:
            #     self.script_data['is_sell_order_placed'] = 1

    def reset_value(self):
        self.script_data['buy_order_time'] = None
        self.script_data['buy_order_no'] = None
        self.script_data['buy_order_status'] = None
        self.script_data['no_buy_order'] = 0
        self.script_data['sell_order_no'] = None
        self.script_data['sell_order_status'] = None
        self.script_data['sell_order_time'] = None
        self.script_data['no_sell_order'] = 0
        self.script_data['no_of_order'] = 0
        self.script_data['to_order'] = 1
        self.script_data['is_sell_order_placed'] = 0

    def check_sell_order_status(self):
        if self.script_data['sell_order_no'] is not None:
            try:
                is_sell_order_status = False
                sell_order_status = None
                while not is_sell_order_status:
                    sell_order_status = self.api.single_order_history(orderno=self.script_data['sell_order_no'])
                    if sell_order_status is not None:
                        is_sell_order_status = True
                self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_sell_order_status() - sell_order_status - {sell_order_status}")
                self.script_data['sell_order_status'] = sell_order_status[0]['status']
                if self.script_data['sell_order_status'] == 'COMPLETE':
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_sell_order_status() - COMPLETE")
                    # self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_sell_order_status() - COMPLETE -> reset_value()")
                    # self.script_data['is_sell_order_placed'] = 0
                    self.script_data['trade_cycle'] += 1
                    # with open(self.history_file, 'r') as file:
                    #     lines = file.readlines()
                    # # Modify lines as needed
                    # # TS = Trade Start, TB = Trade Bought, TC = Trade Complete
                    # is_line_found = False
                    # for i, line in enumerate(lines):
                    #     if line.startswith(self.script_data['trading_symbol']) and line.strip().endswith("TB"):
                    #         lines[i] = line.replace("-TB", "-TC")
                    #         is_line_found = True
                    #         break
                    # if is_line_found:
                    #     # Write the modified lines back to the file
                    #     with open(self.history_file, 'w') as file:
                    #         file.writelines(lines)
                    # Read and modify the last line of the file
                    with open(self.history_file, 'r') as file:
                        lines = file.readlines()  # Read all lines

                    if lines:  # Check if the file is not empty
                        last_line = lines[-1].strip()  # Get the last line
                        if last_line.startswith(self.script_data['trading_symbol']) and last_line.endswith("TB"):
                            # Modify the last line
                            # # TS = Trade Start, TB = Trade Bought, TC = Trade Complete
                            lines[-1] = last_line.replace("-TB", "-TC") + '\n'

                            # Write the modified lines back to the file
                            with open(self.history_file, 'w') as file:
                                file.writelines(lines)
                    # self.reset_value()
                    return self.script_data['sell_order_status']
                elif self.script_data['sell_order_status'] == 'OPEN':
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_sell_order_status() - OPEN")
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Sell order with ID {self.script_data['sell_order_no']} is pending")
                    self.script_data['is_sell_order_placed'] = 1
                    self.sell_order_value_update()
                    return self.script_data['sell_order_status']
                elif self.script_data['sell_order_status'] == 'REJECTED':
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_sell_order_status() - REJECTED")
                    self.logger.info(f"WARN : {self.script_data['trading_symbol']} - Sell order with ID {self.script_data['sell_order_no']} is REJECTED")
                    self.logger.info(f"ACTION_TODO {self.script_data['trading_symbol']} - Please check reason for sell order rejection.")
                    self.logger.info(f"INFO : {self.script_data['trading_symbol']} - check_sell_order_status() - REJECTED -> reset_value()")
                    # self.script_data['is_sell_order_placed'] = 0
                    self.script_data['trade_cycle'] += 1
                    # self.reset_value()
                    return self.script_data['sell_order_status']
            except Exception:
                raise Exception(f"ERROR : {self.script_data['trading_symbol']} - An error occurred in getting status of a new Sell Order")
        else:
            self.logger.info(f"INFO : {self.script_data['trading_symbol']} - There is no sell order placed.")
            self.script_data['is_sell_order_placed'] = 0
            return None


    def do_buy(self):
        # place_order(self, act_id, buy_or_sell, product_type,
        #                     exchange, tradingsymbol, quantity, discloseqty,
        #                     price_type, price=0.0, trigger_price=None,
        #                     algo_id=None,naic_code=None,
        #                     retention='DAY', amo=None, remarks=None, bookloss_price = 0.0, bookprofit_price = 0.0, trail_price = 0.0)
        available_margin = self.get_available_margin()
        if available_margin >= round(self.script_data['buy_value'] * self.script_data['qty'], 2) and self.script_data['trade_cycle'] == 0:
            try:
                is_buy_order_res = False
                buy_order_res = None
                while not is_buy_order_res:

                    try:
                        buy_order_res = self.api.place_order(buy_or_sell='B',
                                                             product_type='C',
                                                             exchange=self.script_data['exchange'],
                                                             tradingsymbol=self.script_data['trading_symbol'],
                                                             quantity=self.script_data['qty'],
                                                             discloseqty=0,
                                                             price_type='LMT',
                                                             price=self.script_data['buy_value'],
                                                             trigger_price=None,
                                                             retention='DAY',
                                                             remarks='my_order_001') #,
                                                             # act_id=self.script_data['act_id'])
                    except TypeError:
                        buy_order_res = self.api.place_order(buy_or_sell='B',
                                                             product_type='C',
                                                             exchange=self.script_data['exchange'],
                                                             tradingsymbol=self.script_data['trading_symbol'],
                                                             quantity=self.script_data['qty'],
                                                             discloseqty=0,
                                                             price_type='LMT',
                                                             price=self.script_data['buy_value'],
                                                             trigger_price=None,
                                                             retention='DAY',
                                                             remarks='my_order_001',
                                                             act_id=self.script_data['act_id'])
                    if buy_order_res is not None:
                        is_buy_order_res = True
                # self.logger.info(f"BuyOrderResponse - {buy_order_res}")
                # sleep(0.5)
                # self.logger.info(f"Buy order --- {buy_order_res}")
                self.script_data['buy_order_no'] = buy_order_res['norenordno']
                tmp_date = datetime.strptime(buy_order_res['request_time'], "%H:%M:%S %d-%m-%Y")
                self.script_data['buy_order_time'] = datetime.strftime(tmp_date, "%d-%m-%Y %H:%M:%S")
                self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Buy_Order_Time - {self.script_data['buy_order_time']}")
                self.script_data['to_order'] = 0
                # self.script_data['no_of_order'] = self.script_data['qty']
                # self.script_data['buy_order_time'] = buy_order_res['exch_tm']
                # self.logger.info(
                #     f"INFO : {self.script_data['trading_symbol']} - Script Set Parameters - {self.script_data}")
                self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Checking buy order status - do_buy() -> check_buy_order_status()")
                self.check_buy_order_status()


            except Exception:
                raise Exception(f"ERROR : {self.script_data['trading_symbol']} - An error occurred in placing Buy Order")


    def is_sell_order_completed(self):
        return self.check_sell_order_status()


    def do_sell(self):

        sell_value = round(self.script_data['buy_value'] + self.script_data['sell_margin'], 2)

            # if self.script_data['ltp'] - self.script_data['buy_value'] < self.script_data['sell_margin']
        if sell_value != 0.0:
            try:
                is_sell_order_res = False
                sell_order_res = None
                while not is_sell_order_res:
                    try:
                        sell_order_res = self.api.place_order(buy_or_sell='S',
                                                          product_type='C',
                                                          exchange=self.script_data['exchange'],
                                                          tradingsymbol=self.script_data['trading_symbol'],
                                                          quantity=self.script_data['qty'],
                                                          discloseqty=0,
                                                          price_type='LMT',
                                                          price=sell_value,
                                                          trigger_price=None,
                                                          retention='DAY',
                                                          remarks='my_order_001')
                                                          # act_id=self.script_data['act_id'])
                    except TypeError:
                        sell_order_res = self.api.place_order(buy_or_sell='S',
                                                              product_type='C',
                                                              exchange=self.script_data['exchange'],
                                                              tradingsymbol=self.script_data['trading_symbol'],
                                                              quantity=self.script_data['qty'],
                                                              discloseqty=0,
                                                              price_type='LMT',
                                                              price=sell_value,
                                                              trigger_price=None,
                                                              retention='DAY',
                                                              remarks='my_order_001',
                                                              act_id=self.script_data['act_id'])
                    # sleep(0.5)
                    if sell_order_res is not None:
                        is_sell_order_res = True
                self.logger.info(f"INFO : {self.script_data['trading_symbol']} - do_sell - sell_order_res - {sell_order_res}")
                self.script_data['sell_order_no'] = sell_order_res['norenordno']
                # self.script_data['sell_order_time'] = sell_order_res['exch_tm']
                self.logger.info(f"INFO : {self.script_data['trading_symbol']} - do_Sell() -> check_sell_order_status()")
                self.check_sell_order_status()

            except Exception:
                raise Exception(f"ERROR : {self.script_data['trading_symbol']} - An error occurred in placing Sell Order")
            finally:
                self.script_data['is_sell_order_placed'] = 1


    def do_trade(self):
        # if (self.script_data['no_of_order'] == 0 and
        #         self.script_data['to_order'] == 1 and
        #         self.script_data['is_sell_order_placed'] == 0):
        if self.script_data['buy_order_no'] is None and self.script_data['sell_order_no'] is None:
            self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Placing a Buy Order - do_buy()")
            self.do_buy()


    def check_open_order_status(self):
        self.check_buy_order_status()
        self.check_sell_order_status()


    def set_buy_value(self):
        return round(self.script_data['ltp'] - self.script_data['buy_margin'], 2)


    def start_trade(self):
        # if self.script_data['buy_order_status'] is None and self.script_data['sell_order_status'] is None:
        self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Setting for buying")
        self.set_buy_sell_margin()
        # self.logger.info(self.script_data)
        if (float(self.script_data['today_high']) - float(self.script_data['ltp']) <
                float(self.script_data['too_high_diff'])):
            self.logger.info(f"WARN : {self.script_data['trading_symbol']} - Wait - Script Value is near today's High Value -"
                  " Script value is moved\33[1;31m too high\033[0m")
        else:
            if self.script_data['no_of_order'] == 0:
                self.script_data['buy_value'] = self.set_buy_value()
                self.script_data['buy_value_0'] = self.script_data['buy_value']
                self.script_data['sell_value'] = round(self.script_data['buy_value'] +
                                                       self.script_data['sell_margin'], 2)
                # self.do_trade()
                self.logger.info(f"INFO : {self.script_data['trading_symbol']} - Script Trading Settings....")
                self.logger.info(self.script_data)
                self.do_trade()
