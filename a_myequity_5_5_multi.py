### LEGEND ###
# TS = Trade Started,
# TB = Trade Bought,
# TC = Trade Completed
import math
## Logic Add for - Search a script status in a_script_trade_history.txt file
# If script in file then check for status - if TC then add new trade for it, otherwise skip
# check latest script every 30 minutes.


# import time
from signal import SIGKILL
from os import getpid, kill, path, makedirs
# import json
import threading
from datetime import datetime  # , timedelta
# from time import sleep
from api_helper import NorenApiPy  # , get_time
from ft_token import FTToken
from a_trade_5_5 import Trade
import logging
from a_active_script_finder import get_active_scripts
from a_analyse_script import ScriptAnalysis

NEXT_ORDER_TIME = 300
EXCHG = 'NSE'
QTY = 1
PID = getpid()
TRADE_CYCLE = 1
trades_status = {}
ACC_ID = 'FT035389'
last_margin_available = 0.0

# Get the directory of the current script
script_directory = path.dirname(path.abspath(__file__))

# Set Script Trade History File to track trading history
# a_script_trade_history_file = path.join(script_directory, 'a_script_trade_history.txt')

# scripts_file is file containing a list of today's active script
scripts_file = path.join(path.dirname(path.abspath(__file__)), 'a_latest_scripts.txt')

# Log directory
log_dir = path.join(script_directory, '../log')
history_dir = path.join(script_directory, '../history')
# Ensure the log directory exists
if not path.exists(log_dir):
    makedirs(log_dir)

# Ensure the directory exists, create it if it doesn't
if not path.exists(history_dir):
    makedirs(history_dir)

# Create a log file name with the full path in the script directory
trade_log_file = path.join(log_dir, 'a_trade_' + datetime.now().strftime('%d-%m-%Y') + '.log')

# Set up the general logger
trades_logger = logging.getLogger('trades_logger')
trades_logger.setLevel(logging.INFO)

# Create handler for the general log file
trades_file_handler = logging.FileHandler(trade_log_file)
trades_file_handler.setLevel(logging.INFO)


# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
trades_file_handler.setFormatter(formatter)

# Add the handler to the general logger
trades_logger.addHandler(trades_file_handler)

# logging.basicConfig(
#     filename=log_file_name,              # Log file
#     level=trades_logger.info,                 # Log all levels (DEBUG and higher)
#     format='%(asctime)s - %(name)s - %(message)s'
# )


# Initialize the API session
api = NorenApiPy()
token = FTToken()
usersession = token.generate_token()
userid = token.user_id
userpasswd = token.passwd


# Function to set up per-script loggers
def setup_script_logger(script_name_):
    script_log_file = path.join(log_dir, 'a_trade_' + f'{script_name_}_' + datetime.now().strftime('%d-%m-%Y') + '.log')

    # Create a logger for the script
    script_logger = logging.getLogger(f'{script_name_}_logger')
    script_logger.setLevel(logging.INFO)

    # Create file handler for the script log
    script_file_handler = logging.FileHandler(script_log_file)
    script_file_handler.setLevel(logging.INFO)

    # Use the same formatter
    script_file_handler.setFormatter(formatter)

    # Add the file handler to the script logger
    script_logger.addHandler(script_file_handler)

    return script_logger

def get_available_margin():
    global last_margin_available
    _ = api.set_session(userid=userid, password=userpasswd, usertoken=usersession)
    limits = api.get_limits()
    try:
        margin_used = float(limits['marginused'])
    except KeyError:
        margin_used = 0.0
    available_margin_ = round(float(limits['cash']) - margin_used, 2)
    if last_margin_available != available_margin_:
        trades_logger.info(f"INFO : Available Margin Limit is Rs {available_margin_}")
        last_margin_available = available_margin_
    return available_margin_

def clear_file_content(f_path):
    today = datetime.today()
    # Check if the file exists and its last modification date
    if path.exists(f_path):
        last_modified_date = datetime.fromtimestamp(path.getmtime(f_path))
    else:
        last_modified_date = None
    # If the file was modified on a previous day or doesn't exist, clear it
    if last_modified_date != today:
        with open(f_path, 'w') as f:
            f.write("")  # Clear the file by writing an empty string
        trades_logger.info(f"File '{f_path}' has been cleared for the new day.")
    else:
        trades_logger.info(f"File '{f_path}' was already cleared today.")

def file_age_in_minutes(file_path):
    # Get the current time
    now = datetime.now()
    # Get the last modification time of the file
    modified_time = datetime.fromtimestamp(path.getmtime(file_path))
    # Check if the file was modified today
    if modified_time.date() == now.date():
        # Calculate the age in minutes
        age_in_minutes = (now - modified_time).total_seconds() / 60
        return age_in_minutes
    else:
        return None  # File was not modified today

def get_scripts_data():
    # clear content of previous day

    clear_file_content(scripts_file)
    # if path.exists(a_script_trade_history_file):
    #     clear_file_content(a_script_trade_history_file)

    # Get today's active script list from NSE
    get_active_scripts()
    scripts_ = {}
    ret = None

    available_margin_ = get_available_margin()
    # Reading the today_scripts.txt file and processing the data
    with open(scripts_file, 'r') as sf:
        today_scripts = list(map(str.strip, sf.readlines()))
    _ = api.set_session(userid=userid, password=userpasswd, usertoken=usersession)
    for s in today_scripts:
        # # initialise trades_status for script
        # trades_status[s] = {}
        # Splitting the name and quantity
        # A list of scripts - {'INDUSTOWER-EQ': ['29135', '1'], 'IIFL-EQ': ['11809', '1'], 'RELINFRA-EQ': ['553', '1'], 'VEDL-EQ': ['3063', '1'], 'INDIASHLTR-EQ': ['20556', '1'], 'ZOMATO-EQ': ['5097', '1'], 'KALYANKJIL-EQ': ['2955', '1'], 'ICICIBANK-EQ': ['4963', '1'], 'ADANIPOWER-EQ': ['17388', '1'], 'JUBLPHARMA-EQ': ['3637', '1'], 'HEG-EQ': ['1336', '1'], 'PPLPHARMA-EQ': ['11571', '1'], 'POWERGRID-EQ': ['14977', '1'], 'GRAPHITE-EQ': ['592', '1'], 'NATIONALUM-EQ': ['6364', '1'], 'TATAMOTORS-EQ': ['3456', '1'], 'IEX-EQ': ['220', '1']}
        if s.find("#", 0, 1) != 0:
            script_name_, s_ltp = s.split('-')
            query = script_name_ + "-EQ"
            if float(s_ltp) > round(available_margin_/2, 2):
                quantity = 1
            else:
                quantity = int(available_margin_/(2 * float(s_ltp)))
            # print(quantity)

            is_ret = False

            while not is_ret:
                ret = api.searchscrip(exchange=EXCHG, searchtext=query)
                if ret is not None:
                    is_ret = True
            # ret = {'stat': 'Ok', 'values': [{'exch': 'NSE', 'token': '25049', 'tsym': 'PREMIERENE-EQ', 'cname': 'PREMIER ENERGIES LIMITED', 'instname': 'EQ', 'pp': '2', 'ls': '1', 'ti': '0.05'}]}
            # script_token = ret['values'][0]['token']
            scripts_[query] = list((ret['values'][0]['token'], quantity))

    print(scripts_)
    return scripts_

def can_trade():
    curnt_time = int(f"{datetime.now().hour}{datetime.now().minute:02d}")
    if curnt_time > 1445:
        trades_logger.info("ALERT : Time Over...")
        return False
    else:
        return True


# Generating a list of Active Scripts
scripts = get_scripts_data()
# scripts = {'SWANENERGY-EQ': ['27095', 1]}
trades_logger.info(f"INFO : A list of scripts - {scripts}")


def trade_start(script, session_token, quantity, analysed_sell_margin):
    # Get the logger for this specific script
    script_logger = setup_script_logger(script)

    # Log information to both general and script loggers
    trades_logger.info(f"INFO : Initiating trade for script: {script}")
    trades_logger.info(f"INFO: Thread name is {threading.current_thread().name}")

    # Setting sessions
    _ = api.set_session(userid=userid, password=userpasswd, usertoken=usersession)

    # Create a Trade Object
    # trade1 = Trade(api=api, tradingsymbol=script, script_token=scripts[script][0], account_id=userid, qty=scripts[script][0])
    trade1 = Trade(api=api, tradingsymbol=script, password=userpasswd,
                   script_token=session_token, account_id=userid,
                   qty=quantity, sell_margin=analysed_sell_margin)

    trades_logger.info(trade1.script_data)

    current_second = 1
    while trade1.get_trade_cycle() < TRADE_CYCLE and can_trade():
        trade1.set_today_hl()
        trade1.set_ltp()
        traded_script = trade1.get_script_name()
        script_logger.info(f"INFO : {traded_script} - LTP is Rs. {trade1.get_ltp()}")

        available_margin_ = get_available_margin()
        script_logger.info(f"INFO : Available Margin is : {available_margin_}")

        trade1.check_open_order_status()
        buy_value_ltp_diff = trade1.get_buyvalue_ltp_diff()
        sell_margin = trade1.get_sell_margin()
        stop_loss_margin = trade1.get_stop_loss_margin()

        if available_margin_ >= trade1.get_ltp() and trade1.check_buy_order_status() is None:
            script_logger.info(f"INFO: Starting trade for script {traded_script}")
            trades_logger.info(f"INFO : {traded_script} while -> start_trade()")
            trade1.start_trade()

        elif trade1.check_buy_order_status() is not None and trade1.check_sell_order_status() is None:
            script_logger.info(f"INFO : {traded_script} - Buy Order: {trade1.check_buy_order_status()}")
            if trade1.check_buy_order_status() == "REJECTED":
                script_logger.info(f"INFO : {traded_script} - Buy Order is REJECTED.!!! KILLING the trade for {traded_script}")
                break
            script_logger.info(f"INFO : {traded_script} - Sell Order: {trade1.check_sell_order_status()}")
            if trade1.check_sell_order_status() == "REJECTED":
                script_logger.info(f"INFO : {traded_script} - Sell Order is REJECTED.!!! KILLING the trade for {traded_script}")
                break
            script_logger.info(f"INFO : {traded_script} - Sell Order status: {trade1.check_sell_order_status()}...")

        elif trade1.check_buy_order_status() is not None and trade1.check_sell_order_status() is not None:
            # script_logger.info(f"INFO : {traded_script} - Buy Order: {trade1.check_buy_order_status()}")
            if trade1.check_buy_order_status() == "REJECTED":
                script_logger.info(
                    f"INFO : {traded_script} - Buy Order is REJECTED.!!! KILLING the trade for {traded_script}")
                break
            script_logger.info(f"INFO : {traded_script} - Sell Order: {trade1.check_sell_order_status()}")
            if trade1.check_sell_order_status() == "REJECTED":
                script_logger.info(
                    f"INFO : {traded_script} - Sell Order is REJECTED.!!! KILLING the trade for {traded_script}")
                break

            if trade1.check_sell_order_status() == "COMPLETE":
                script_logger.info(
                    f"INFO : {traded_script} - Sell Order is COMPLETE... KILLING the trade for {traded_script}")
                break

            if current_second % 15 == 0:
                script_logger.info(
                    f"INFO : {traded_script} - Difference between Buy Value and LTP : {buy_value_ltp_diff}")
                script_logger.info(f"INFO : {traded_script} - Sell Margin : {sell_margin}")
                script_logger.info(f"INFO : {traded_script} - Stop Loss Margin: {stop_loss_margin}")
                trade_cycle = trade1.get_trade_cycle()
                script_logger.info(f"INFO : {traded_script} - No of Trade Cycle: {trade_cycle}")
                try:
                    trades_status[traded_script]['buy_ord_no'] = trade1.get_buy_order_no()
                    trades_status[traded_script]['buy_ord_time'] = trade1.get_buy_order_time()
                    trades_status[traded_script]['buy_value'] = trade1.get_buy_value()
                    trades_status[traded_script]['sell_margin'] = trade1.get_sell_margin()
                    trades_status[traded_script]['sell_ord_no'] = trade1.get_sell_order_no()
                    trades_status[traded_script]['sell_ord_time'] = trade1.get_sell_order_time()
                    trades_status[traded_script]['ltp'] = trade1.get_ltp()
                    trades_logger.info(f"Info : {traded_script} status - {trades_status[traded_script]}")
                except KeyError:
                    script_logger.info(f"INFO : {traded_script} - Trade has been completed")

        # if available_margin_ >= trade1.get_ltp() :
        #     if trade1.check_buy_order_status() is None:
        #         script_logger.info(f"INFO: Starting trade for script {traded_script}")
        #         trades_logger.info(f"INFO : {traded_script} while -> start_trade()")
        #         trade1.start_trade()
        #
        #     elif trade1.check_buy_order_status() is not None and trade1.check_sell_order_status() is None:
        #         script_logger.info(f"INFO : {traded_script} - Buy Order: {trade1.check_buy_order_status()}")
        #         script_logger.info(f"INFO : {traded_script} - Sell Order: {trade1.check_sell_order_status()}")
        #         script_logger.info(f"INFO : {traded_script} - Sell Order: NOT PLACED...")
        #
        #     elif trade1.check_buy_order_status() is not None and trade1.check_sell_order_status() is not None:
        #
        #         if current_second % 15 == 0:
        #             script_logger.info(f"INFO : {traded_script} - Difference between Buy Value and LTP : {buy_value_ltp_diff}")
        #             script_logger.info(f"INFO : {traded_script} - Sell Margin : {sell_margin}")
        #             script_logger.info(f"INFO : {traded_script} - Stop Loss Margin: {stop_loss_margin}")
        #             trade_cycle = trade1.get_trade_cycle()
        #             script_logger.info(f"INFO : {traded_script} - No of Trade Cycle: {trade_cycle}")
        #             try:
        #                 trades_status[traded_script]['buy_ord_no'] = trade1.get_buy_order_no()
        #                 trades_status[traded_script]['buy_ord_time'] = trade1.get_buy_order_time()
        #                 trades_status[traded_script]['buy_value'] = trade1.get_buy_value()
        #                 trades_status[traded_script]['sell_margin'] = trade1.get_sell_margin()
        #                 trades_status[traded_script]['sell_ord_no'] = trade1.get_sell_order_no()
        #                 trades_status[traded_script]['sell_ord_time'] = trade1.get_sell_order_time()
        #                 trades_status[traded_script]['ltp'] = trade1.get_ltp()
        #                 trades_logger.info(f"Info : {traded_script} status - {trades_status[traded_script]}")
        #             except KeyError:
        #                 script_logger.info(f"INFO : {traded_script} - Trade has been completed")

        else:
            trades_logger.info(f"ALERT : Low Available Margin !! KILLING the trade for {traded_script}")
            break
            # if script_analysis(api, EXCHG, script_token, script, trade1.get_ltp(),
            #                    trade1.get_ltd(), trade1.get_ltt(), sell_margin, "buy") and current_second == 1:
            #     if (trade1.check_sell_order_status() is not None and is_reference_value_changed and
            #             reference_value > trade1.get_buy_value() and trade1.get_ltp() <= reference_value):
            #         script_logger.info(f"INFO : {script} - updating sell order as script value moved downwards")
            #         trade1.update_sell_order(reference_value)
            #         script_logger.info(
            #             f"INFO : {script} - Sell Order: {trade1.check_sell_order_status()} -> expected None as it may be completed")
            # if current_second % 15 == 0:
            #     script_logger.info(f"INFO : {traded_script} - Difference between Buy Value and LTP : {buy_value_ltp_diff}")
            #     script_logger.info(f"INFO : {traded_script} - Sell Margin : {sell_margin}")
            #     script_logger.info(f"INFO : {traded_script} - Stop Loss Margin: {stop_loss_margin}")
            #     trade_cycle = trade1.get_trade_cycle()
            #     script_logger.info(f"INFO : {traded_script} - No of Trade Cycle: {trade_cycle}")
            #     trades_status[traded_script]['buy_ord_no'] = trade1.get_buy_order_no()
            #     trades_status[traded_script]['buy_ord_time'] = trade1.get_buy_order_time()
            #     trades_status[traded_script]['buy_value'] = trade1.get_buy_value()
            #     trades_status[traded_script]['sell_margin'] = trade1.get_sell_margin()
            #     trades_status[traded_script]['sell_ord_no'] = trade1.get_sell_order_no()
            #     trades_status[traded_script]['sell_ord_time'] = trade1.get_sell_order_time()
            #     trades_status[traded_script]['ltp'] = trade1.get_ltp()
            #     trades_logger.info(f"Info : {traded_script} status - {trades_status}")

        # Checking Buy Order Status
        trade1.check_buy_order_status()

        # Checking Sell Order Status
        trade1.check_sell_order_status()

        if trade1.get_trade_cycle() > 0:
            break
        #     # Read the file and modify the specified line
        #     history_file_ = path.join(history_dir,
        #                              f'a_{traded_script}_trade_history_{datetime.now().strftime("%d-%m-%Y")}.txt')
        #     with open(history_file_, 'r') as sth_f:
        #         lns = sth_f.readlines()
        #
        #     # Modify lines as needed
        #     # TS = Trade Started, TB = Trade Bought, TC = Trade Completed
        #     is_line_found = False
        #     for i, line_ in enumerate(lns):
        #         if line_.startswith(traded_script) and line_.strip().endswith("TB"):
        #             lns[i] = line_.replace("-TB", "-TC")
        #             is_line_found = True
        #             break
        #
        #     if is_line_found:
        #         # Write the modified lines back to the file
        #         with open(history_file_, 'w') as sth_f:
        #             sth_f.writelines(lns)


trades_logger.info("---------------------------------------------------------------------")

if not can_trade():
    kill(PID, SIGKILL)

do_trade = input("Shall we start? [y/n]: ").strip().lower() == 'y'
threads = {}
count = 0

# while can_trade() and do_trade and count < 1:
while can_trade() and do_trade:
    list_script_tradable = []
    if len(scripts) > 0:
        # for script_info in scripts.items():
        #     # script_info = ('CDSL-EQ', ['21174', 1])
        #     script_name = script_info[0]
        #     script_token = script_info[1][0]
        #     script_qty =  script_info[1][1]
        for script_name, (script_token, script_qty) in scripts.items():

            is_script_trade_started = False

            history_file = path.join(history_dir,
                                     f'a_{script_name}_trade_history_{datetime.now().strftime("%d-%m-%Y")}.txt')
            # Open the file in 'a' (append) mode, which will create it if it doesn't exist
            with open(history_file, 'a'):
                pass

            # Read the last line of the file and check if script trade started or not
            with open(history_file, 'r') as asth_f:
                lines = asth_f.readlines()  # Read all lines

            if lines:  # Check if the file is not blank
                last_line = lines[-1].strip()  # Get the last line and strip whitespace
                # Check if the last line starts with script_name and ends with "EQ" or "TC"
                if last_line.startswith(script_name):
                    if last_line.endswith("TC"):
                        is_script_trade_started = False
                    else:
                        is_script_trade_started = True
                else:
                    is_script_trade_started = False
            else:
                # File is blank
                is_script_trade_started = False

            # if trade for script not started than analyse the script and start trade if tradable.
            if not is_script_trade_started:
                # api, script_name, script_token, account_id, usersession, userpasswd, userid, exchange='NSE'
                s_analysis = ScriptAnalysis(api, script_name=script_name, script_token=script_token, account_id=ACC_ID,
                                            userid=userid, userpasswd=userpasswd, usersession=usersession, exchange=EXCHG)

                is_tradable = s_analysis.script_analysis()

                if is_tradable:
                    available_margin = get_available_margin()
                    if available_margin >= round(s_analysis.ltp * script_qty, 2):
                        list_script_tradable.append(script_name)
                        trades_logger.info(f"INFO : Available Margin is : {available_margin}")
                        trades_logger.info(f"INFO : {script_name} is buyable and initiate trading.")
                        # analysed_sell_margin_ = s_analysis.sell_margin
                        # reformatting analysed_sell_margin i.e. if sell margin is 100.14, then it is reformatted to 100.10
                        analysed_sell_margin_ = math.floor((s_analysis.sell_margin * 10) / 10)
                        # analysed_ltp_ = s_analysis.ltp
                        trades_logger.info(f"INFO :  {script_name} - Analysed Sell Margin is {analysed_sell_margin_}")
                        trades_logger.info(f"INFO :  {script_name} - Analysed at LTP {s_analysis.ltp}")
                        scrpt = script_name.split("-")[0]
                        # initialise trades_status for script
                        trades_status[script_name] = {}
                        # print(scrpt)
                        name = f"Thread-{scrpt}"
                        trades_logger.info(script_name)
                        # token_ = script_token
                        # qty_ = script_qty
                        threads[scrpt] = threading.Thread(
                            target=trade_start,
                            args=(script_name, script_token, script_qty, analysed_sell_margin_),
                            name=name
                        )

                        threads[scrpt].start()
                        history_file = path.join(history_dir, f'a_{script_name}_trade_history_{datetime.now().strftime("%d-%m-%Y")}.txt')
                        with open(history_file, 'a') as asth_f:
                            # TS = Trade Started, TB = Trade Bought, TC = Trade Completed
                            asth_f.write(f"{script_name}-{s_analysis.ltp}-{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}-TS\n")
                    else:
                        trades_logger.info(f"INFO :  {script_name} is tradable, but available margin is low.")


    # Removing tradable scripts trading has been started for these scripts
    for t_script in list_script_tradable:
        scripts.pop(t_script)

    # Generating List of Active Scripts again
    if len(scripts) == 0 or file_age_in_minutes(scripts_file) >= 30:
        # clear content of previous day
        clear_file_content(scripts_file)
        # Generating a list of Active Scripts
        scripts = get_scripts_data()
        # scripts = {'SWANENERGY-EQ': ['27095', 1]}
        trades_logger.info(f"INFO : A list of scripts - {scripts}")
        available_margin = get_available_margin()
        trades_logger.info(f"INFO : Available Margin is : {available_margin}")





    # for scrpt in scripts:
    #     threads[scrpt].join()

    # count += 1
