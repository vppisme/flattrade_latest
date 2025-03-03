# reference_value : it is a reference value to determine peak or trough occurred or not.
# if a script value is going down after peak is formed, the peak is set as reference value to determine trough
# if a script value is going up after trough is formed, the trough is set as reference value to determine peak
# reference_value_time : time when a reference_value occurred
#### Logic #####
# High fall, high rise (~=0.9%) -> Tradable
# High fall, low rise, high/moderate fall -> don't buy
# Last sudden high fall -> Tradable
# High slow fall with low rise -> don't buy
# peak trend is downward with reducing diff (low) between trough to peak -> don't buy after 12:45
# peak trend is zigzag with comparatively good diff between trough to peak -> Tradable
# peak trend is downward with reducing diff (comparatively good) between trough to peak -> Tradable
# W.r.t to Last peak, LTP is very low and trough after this peak is not determined -> Tradable
# peak and trough near day high/low should be avoided

# Q.1 - Who is last ? peak or trough ? if trough, is_tradable = True,  if peak, check Q.2
# Q.2 - is ltp near last trough or last peak ?  if near trough or peak_to_ltp difference is gt 0.95% , is_tradable = True. If near peak, is_tradable = False
# Q.3 - Trend of peaks. if Zigzag, check Q.1, if Downwards, check Q.2
# Q.4 - Trend

# condition -> peak = 0 and first trough is forming means if ltp < last trough value - don't buy
# condition -> trough = 0 and first peak is either forming or formed means if ltp > last peak value- don't buy
#
# condition -> peak = 0 and first trough is formed, if ltp > last trough value - analyse for buying zpzz13up value from last trough
# condition -> trough = 1 and peak =0, -  analyse for buying using zpzz13up value
#
# condition -> peak = 1 and trough = 0, - analyse for buying using onep2down value from last peak
#
# condition -> peak > 0 and trough > 0 and peak formed first, analyse for buying zpzz13up value
# condition -> peak > 0 and trough > 0 and trough formed first, analyse for buying zpzz59down  value
#
#
#
# peak = 0 and trough = 0 -> don't buy
# peak = 0 and trough = 1 -> analyse for buying zpzz13up value from last trough -> if (Opening_value - ltp > 1.2%*Opening_value) and (ltp - last_trough < 0.0013*last_trough):buy
# peak = 1 and trough = 0, - analyse for buying using onep2down value from last peak -> if (last_peak - ltp > 1.2%*last_peak):buy
# peak > 1 and trough >1 and peak formed first, analyse for buying zpzz13up value from last trough -> if ( ltp - last_trough < 0.0013*last_trough):buy
# peak > 1 and trough >1 and trough formed first, analyse for buying zpzz59down  value -> if (last_peak - ltp > 0.0059*last_peak):buy


from datetime import datetime
import logging
from api_helper import NorenApiPy  # , get_time
from ft_token import FTToken

# import logging
# from api_helper import NorenApiPy

# from ft_token import FTToken
# from a_set_margin import get_margin

# logger = logging.getLogger(__name__)
# token = FTToken()
# usersession = token.generate_token()
# userid = token.user_id
# userpasswd = token.passwd


UP_LE_MP = 0.0013  # multiplier to determine LTP change from last trough
DOWN_GE_MP_0 = 0.012  # multiplier to determine fall of value from market opening to place buy order
# DOWN_GE_MP_1 = 0.0059  # multiplier to determine fall of value from last peak to place buy order
DOWN_GE_MP_1 = 0.0059  # multiplier to determine fall of value from last peak to place buy order
SELL_MARGIN_MP = 0.40  # multiplier to calculate sell margin

logger = logging.getLogger(__name__)


def time_duration(s_time, e_time):
    start_time = datetime.strptime(s_time, '%d-%m-%Y %H:%M:%S')
    end_time = datetime.strptime(e_time, '%d-%m-%Y %H:%M:%S')

    # Calculate the time difference in minutes
    return int((end_time - start_time).total_seconds() / 60)


def summerise(t_data, op):
    # print(t_data)
    if op == 'gt':
        max_value = 0.0
        max_value_time = None
        for data in t_data:
            if data[1] > max_value:
                max_value = data[1]
                max_value_time = data
        return max_value_time
    else:
        min_value = 0.0
        min_value_time = None
        for data in t_data:
            if min_value == 0.0:
                min_value = data[1]
            if data[1] <= min_value:
                min_value = data[1]
                min_value_time = data
        return min_value_time


def is_down_ge(val1, val2, val3):
    if val1 - val2 >= round(val1 * val3, 2):
        return True
    return False


def is_up_le(val1, val2, val3):
    # print(val1, val2, val3)
    if val1 - val2 > round(val1 * val3, 2):
        return False
    return True


def calculate_sell_margin(large_val, small_value, sell_margin_mp=SELL_MARGIN_MP):
    return round((large_val - small_value) * sell_margin_mp, 2)


class ScriptAnalysis:
    def __init__(self, api, script_name, script_token, account_id, usersession, userpasswd, userid, exchange='NSE'):
        self.min_avg_max_trough_peak_diff = None
        self.min_avg_max_peak_trough_diff = None
        self.usersession = usersession
        self.userpasswd = userpasswd
        self.userid = userid
        self.opening_price = None
        self.what_last = None
        self.value_at_zp59_down = None
        # self.min_avg_max_summerised_troughs = None
        self.min_avg_max_summerised_peaks = None
        self.last_trough_ltp_diff = None
        self.ltd = None
        self.ltt = None
        self.ltp = None
        self.last_peak_ltp_diff = None
        self.last_trough_peak_price_diff = None
        self.api = api
        self.exchange = exchange
        self.script_name = script_name
        self.script_token = script_token
        self.act_id = account_id
        self.summerised_peaks = []
        self.summerised_troughs = []
        self.peak_trough_diff = []
        self.trough_peak_diff = []
        self.action = 'buy'
        self.peaks = []
        self.troughs = []
        self.last_peak_trough_price_diff = 0.0
        self.is_reference_value_changed = False
        self.reference_value = 0.0
        self.reference_time_duration = 2
        self.what_first = None
        self.reference_value_time = None
        self.sell_margin = 0.0

    def what_is_last(self):
        if time_duration(self.peaks[-1][0], self.troughs[-1][0]) > 0:
            self.what_last = 'trough'
            # print("INFO : who_last is trough")
        else:
            self.what_last = 'peak'
            # print("INFO : who_last is peak")

    def duration_ltp_last_peak_trough(self):
        ltp_time = self.ltd + " " + self.ltt
        if self.what_last == 'peak':
            print(f"INFO : {self.script_name} : duration_ltp_last_peak_trough() - Peak : {time_duration(self.summerised_peaks[-1][0], ltp_time)} ")
            return time_duration(self.summerised_peaks[-1][0], ltp_time)
        else:
            print(f"INFO : {self.script_name} : duration_ltp_last_peak_trough() - Trough: {time_duration(self.summerised_troughs[-1][0], ltp_time)} ")
            return time_duration(self.summerised_troughs[-1][0], ltp_time)


    def what_is_first(self):
        if time_duration(self.peaks[0][0], self.troughs[0][0]) > 0:
            self.what_first = 'trough'
            # print("INFO : what_first is trough")
        else:
            self.what_first = 'peak'
            # print("INFO : what_first is peak")

    def summarize_peaks_troughs(self, peaks, troughs):
        max_peak = 0.0
        min_trough = 0.0

        if len(peaks) > 0 and len(troughs) > 0:
            if time_duration(peaks[0][0], troughs[0][0]) > 0:
                # print("----> Peak first")
                self.what_first = 'p'
                ref_trough = troughs[0]
                tmp_peaks = []
                # sum_peak.append(peaks[0])
                for peak in peaks:
                    # print(tmp_peaks)
                    if time_duration(peak[0], ref_trough[0]) > 0:
                        if peak[1] > max_peak:
                            tmp_peaks.append(peak)
                    else:
                        break
                # summerise(tmp_peaks)
                self.summerised_peaks.append(summerise(tmp_peaks, "gt"))
                return self.what_first, len(tmp_peaks)
            else:
                # print("----> Trough first")
                self.what_first = 't'
                ref_peak = peaks[0]
                tmp_troughs = []
                # sum_peak.append(peaks[0])
                for trough in troughs:
                    # print(tmp_troughs)

                    if time_duration(trough[0], ref_peak[0]) > 0:
                        if min_trough == 0.0:
                            min_trough = trough[1]
                        if trough[1] <= min_trough:
                            tmp_troughs.append(trough)
                    else:
                        break
                # summerise(tmp_troughs)
                self.summerised_troughs.append(summerise(tmp_troughs, "lt"))
                return self.what_first, len(tmp_troughs)

    def do_summerise_peaks_troughs(self, peaks_, troughs_):
        is_done = False
        peaks = peaks_
        troughs = troughs_
        lenth = 0
        is_no_peak_zero = False
        is_no_trough_zero = False
        while not is_done:
            self.what_first = None
            if len(peaks) > 0 and len(troughs) > 0:
                self.what_first, lenth = self.summarize_peaks_troughs(peaks=peaks, troughs=troughs)
            elif len(peaks) > 0 and len(troughs) == 0:
                self.what_first = 'p'
                lenth = len(peaks)
                self.summerised_peaks.append(summerise(peaks, "gt"))
                is_no_trough_zero = True
                is_no_peak_zero = True
                # peaks = []
            elif len(peaks) == 0 and len(troughs) > 0:
                self.what_first = 't'
                lenth = len(troughs)
                self.summerised_troughs.append(summerise(troughs, "lt"))
                is_no_trough_zero = True
                is_no_peak_zero = True
                # troughs = []
            else:
                is_no_peak_zero = True
                is_no_trough_zero = True

            # if i != 0 :
            if self.what_first == 'p':
                peaks = peaks[lenth:]
                if len(peaks) == 0:
                    # sleep(5)
                    # peaks.append(last_peak)
                    if len(troughs) > 0:
                        self.summerised_troughs.append(summerise(troughs, "lt"))
                    # if len(troughs) == 0:
                    #     is_no_trough_zero = True
                    is_no_peak_zero = True
                # elif len(peaks) > 0 and len(troughs) == 0:
                #     self.summerised_peaks.append(summerise(peaks, "gt"))
                #     is_no_trough_zero = True

                # troughs
            else:
                troughs = troughs[lenth:]
                if len(troughs) == 0:
                    # sleep(5)
                    # troughs.append(last_trough)
                    if len(peaks) > 0:
                        self.summerised_peaks.append(summerise(peaks, "gt"))
                    # if len(peaks) == 0:
                    #     is_no_peak_zero = True
                    is_no_trough_zero = True
                # elif len(troughs) > 0 and len(peaks) == 0:
                #     self.summerised_peaks.append(summerise(troughs, "lt"))
                #     is_no_peak_zero = True
            # print(peaks)
            # print(troughs)
            #
            # print(f"sum_peaks: {sum_peaks}")
            # print(f"sum_troughs: {sum_troughs}")

            if is_no_peak_zero and is_no_trough_zero:
                is_done = True
        self.summerised_peaks = list(dict.fromkeys(self.summerised_peaks))
        self.summerised_troughs = list(dict.fromkeys(self.summerised_troughs))
        print(f"INFO : {self.script_name} : do_summerise_peaks_troughs() -> summerised_peaks: {self.summerised_peaks}")
        print(
            f"INFO : {self.script_name} : do_summerise_peaks_troughs() -> summerised_troughs: {self.summerised_troughs}")

    def analyse_summerised_peaks(self):
        trend = []
        if len(self.summerised_peaks) > 1:
            for i in range(len(self.summerised_peaks) - 1):
                if i != len(self.summerised_peaks) - 1:
                    c_peak_value = self.summerised_peaks[i][1]
                    n_peak_value = self.summerised_peaks[i + 1][1]

                    if c_peak_value <= n_peak_value:
                        trend.append("up")
                    else:
                        trend.append("down")
            # no_of_ups = trend.count("up")
            # no_of_downs = trend.count("down")
            if trend.count("up") > 1:
                # print(f"INFO : analyse_peaks() -> Peak Trend may be zigzag")
                return "zz"  # zz = zigzag
            else:
                # print(f"INFO : analyse_peaks() -> Peak Trend is downward")
                return "dw"  # dw = downward

        else:
            # print("INFO : analyse_peaks() -> Only One Peak formed")
            return "op"  # op = one peak

    def analyse_last_peak_last_trough_diff(self):
        # For trough formed after peak
        if time_duration(self.peaks[-1][0], self.troughs[-1][0]) > 0:
            return round(self.peaks[-1][1] - self.troughs[-1][1], 2)

    def analyse_last_trough_last_peak_diff(self):
        # for peak formed after trough
        if time_duration(self.troughs[-1][0], self.peaks[-1][0]) > 0:
            return round(self.peaks[-1][1] - self.troughs[-1][1], 2)

    def set_last_peak_trough_price_diff(self):
        if len(self.peaks) > 0 and len(self.troughs) > 0 and time_duration(self.peaks[-1][0], self.troughs[-1][0]) > 0:
            print(
                f"INFO : {self.script_name} : set_last_peak_trough_price_diff() -> {self.script_name} - last Trough formed after last Peak...")
            self.last_peak_trough_price_diff = round(self.peaks[-1][1] - self.troughs[-1][1], 2)
            print(
                f"INFO : {self.script_name} : set_last_peak_trough_price_diff() -> {self.script_name} - Last Peak and Trough price difference : {self.last_peak_trough_price_diff}")

    def set_last_trough_peak_price_diff(self):
        if len(self.peaks) > 0 and len(self.troughs) > 0 and time_duration(self.troughs[-1][0], self.peaks[-1][0]) > 0:
            print(
                f"INFO : {self.script_name} : set_last_trough_peak_price_diff() -> {self.script_name} - last Trough formed after last Peak...")
            self.last_trough_peak_price_diff = round(self.peaks[-1][1] - self.troughs[-1][1], 2)
            print(
                f"INFO : {self.script_name} : set_last_trough_peak_price_diff() -> {self.script_name} - Last Trough and Peak price difference : {self.last_trough_peak_price_diff}")

    # Analyse peak to trough diff for every peaks and troughs
    def do_analyse_summerised_peak_trough_diff(self):
        # start_idx = 0
        # last_idx = 0
        if len(self.summerised_peaks) > 0 and len(self.summerised_troughs) > 0:
            if time_duration(self.summerised_peaks[0][0], self.summerised_troughs[0][0]) > 0:
                print(f"INFO : {self.script_name} : do_analyse_summerised_peak_trough_diff() -> 1st peak formed first.")
                start_idx = 0
                last_idx = len(self.summerised_troughs)

                for i in range(start_idx, last_idx):
                    # print(i)
                    self.peak_trough_diff.append((round(self.summerised_peaks[i][1] - self.summerised_troughs[i][1], 2),
                                                  time_duration(self.summerised_peaks[i][0],
                                                                self.summerised_troughs[i][0])))
            else:
                print(
                    f"INFO : {self.script_name} : do_analyse_summerised_peak_trough_diff() -> 1st peak formed second.")
                start_idx = 0
                if len(self.summerised_troughs) >= 2:
                    last_idx = len(self.summerised_troughs)

                    for i in range(start_idx, last_idx - 1):
                        # print(i)
                        self.peak_trough_diff.append(
                            (round(self.summerised_peaks[i][1] - self.summerised_troughs[i + 1][1], 2),
                             time_duration(self.summerised_peaks[i][0], self.summerised_troughs[i + 1][0])))
                # elif
                else:
                    print(
                        f"INFO : {self.script_name} : do_analyse_summerised_peak_trough_diff() -> No sufficient troughs")
                    print(f"INFO : {self.script_name} : do_analyse_summerised_peak_trough_diff() -> WAIT...")

    # Analyse trough to peak diff for every peaks and troughs
    def do_analyse_summerised_trough_peak_diff(self):
        # start_idx = 0
        # last_idx = 0
        if len(self.summerised_peaks) > 0 and len(self.summerised_troughs) > 0:
            if time_duration(self.summerised_troughs[0][0], self.summerised_peaks[0][0]) > 0:
                print(
                    f"INFO : {self.script_name} : do_analyse_summerised_trough_peak_diff() -> 1st trough formed first.")
                start_idx = 0
                last_idx = len(self.summerised_peaks)

                for i in range(start_idx, last_idx):
                    self.trough_peak_diff.append((round(self.summerised_peaks[i][1] - self.summerised_troughs[i][1], 2),
                                                  time_duration(self.summerised_troughs[i][0],
                                                                self.summerised_peaks[i][0])))
            else:
                print(
                    f"INFO : {self.script_name} : do_analyse_summerised_trough_peak_diff() -> 1st trough formed second.")
                start_idx = 0
                if len(self.summerised_peaks) >= 2:
                    last_idx = len(self.summerised_peaks)

                    for i in range(start_idx, last_idx - 1):
                        self.trough_peak_diff.append(
                            (round(self.summerised_peaks[i + 1][1] - self.summerised_troughs[i][1], 2),
                             time_duration(self.summerised_troughs[i][0], self.summerised_peaks[i + 1][0])))
                else:
                    print(
                        f"INFO : {self.script_name} : do_analyse_summerised_trough_peak_diff() -> No sufficient peaks")
                    print(
                        f"INFO : {self.script_name} : do_analyse_summerised_trough_peak_diff() -> do peak to ltp analysis.")

    def set_last_peak_ltp_diff(self):
        self.last_peak_ltp_diff = round(self.peaks[-1][1] - self.ltp, 2)

    def set_last_trough_ltp_diff(self):
        self.last_trough_ltp_diff = round(self.ltp - self.troughs[-1][1], 2)

    def do_analyse_last_peak_ltp_diff(self):
        self.set_last_peak_ltp_diff()
        print(
            f"INFO : {self.script_name} : do_analyse_last_peak_ltp_diff() -> last_peak_ltp_diff is {self.last_peak_ltp_diff}")

    def do_analyse_last_trough_ltp_diff(self):
        self.set_last_trough_ltp_diff()
        print(
            f"INFO : {self.script_name} : do_analyse_last_trough_ltp_diff() -> last_trough_ltp_diff is {self.last_trough_ltp_diff}")

    def set_min_avg_max_peak_trough_diff(self):
        values = [val[0] for val in self.peak_trough_diff]
        if len(values) == 0:
            self.min_avg_max_peak_trough_diff = (0.0, 0.0, 0.0)
        else:
            self.min_avg_max_peak_trough_diff = (min(values), round(sum(values) / len(values), 2), max(values))
        # print(f"INFO : set_min_avg_max_peak_trough_diff() (min, avg, max) -> {self.min_avg_max_peak_trough_diff}")

    def set_min_avg_max_trough_peak_diff(self):
        values = [val[0] for val in self.trough_peak_diff]
        if len(values) == 0:
            self.min_avg_max_trough_peak_diff = (0.0, 0.0, 0.0)
        else:
            self.min_avg_max_trough_peak_diff = (min(values), round(sum(values) / len(values), 2), max(values))
        # print(f"INFO : set_min_avg_max_trough_peak_diff() (min, avg, max) -> {self.min_avg_max_trough_peak_diff}")

    def set_max_peak(self):
        if len(self.summerised_peaks) > 0:
            max_peak = max(self.summerised_peaks, key=lambda x: x[1])
            return max_peak[1]
        else:
            return None

    def do_analyse_peaks_diff_max(self):
        if len(self.summerised_peaks) == 2:
            # diff_of_peaks = [self.summerised_peaks[i] - self.summerised_peaks[i+1] for i in range(len(self.summerised_peaks) - 1)]
            # # max_diff_of_peaks = max(diff_of_peaks)
            return round(self.summerised_peaks[0][1] - self.summerised_peaks[1][1], 2)
        elif len(self.summerised_peaks) > 2:
            diff_of_peaks = [self.summerised_peaks[i][1] - self.summerised_peaks[i + 1][1] for i in
                             range(len(self.summerised_peaks) - 1)]
            # max_diff_of_peaks = max(diff_of_peaks)
            return max(diff_of_peaks)
        else:
            return None

    def get_peaks_troughs(self, r_data):
        # filename = '25049.csv'
        # with open(filename, 'w', newline='') as csvfile:
        #     fieldnames = r_data[0].keys()
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #
        #     writer.writeheader()
        #     writer.writerows(r_data)
        #
        # print(f"Data saved to {filename}")

        # peak : closing value of a 1 minute interval w.r.t reference value.
        # if current value is greater than a peak, new peak is set and saved.
        # if current value is less than a peak, last peak is continued as a peak
        peak = 0.0
        # peak_time : time when a peak occurred
        peak_time = ""

        # trough : closing value of a 1 minute interval w.r.t reference value.
        # if current value is less than a trough, new trough is set and saved.
        # if current value is greater than a trough, last trough is continued as a trough
        trough = 0.0
        # trough_time : time when a trough occurred
        trough_time = ""

        # # reference_value : it is a reference value to determine peak or trough occurred or not.
        # # if a script value is going down after peak is formed, the peak is set as reference value to determine trough
        # # if a script value is going up after trough is formed, the trough is set as reference value to determine peak
        # reference_value = 0.0
        # # reference_value_time : time when a reference_value occurred
        # reference_value_time = ""

        # current_value : closing value of a 1-minute interval either interval high or interval low.
        current_value = 0.0

        # diff_percent : it is used to determine whether peak(hike) or trough(dip) is formed or not.
        # reference_time_duration : it is used to determine whether peak or trough is formed or not.
        current_hour_min = datetime.now().hour * 100 + datetime.now().minute
        if current_hour_min < 1235:
            # Market is more aggressive during early market hours.
            diff_percent = 0.3
            self.reference_time_duration = 2
        else:
            # Market is less aggressive during early market hours.
            diff_percent = 0.4
            self.reference_time_duration = 3

        # Looping through the data in reverse order
        for row in r_data:
            intvc = float(row['intc'])  # intvc is closing value of a 1-minute interval. Convert intvc to float
            if intvc == 0.0:
                continue
            elif intvc != 0.0 and current_value == 0.0:
                self.reference_value = intvc
                self.reference_value_time = row['time']
                current_value = intvc
            else:
                current_value = intvc
                # print(f"1. current value - {current_value},  reference value - {reference_value}")
                if current_value > self.reference_value:
                    if not self.is_reference_value_changed:
                        self.is_reference_value_changed = True
                    hike = round(self.reference_value * diff_percent / 100, 0)
                    if peak != 0.0:
                        if current_value > peak:
                            # if current value is greater than current peak, new peak is set.
                            peak = current_value
                            peak_time = row['time']
                            if len(self.peaks) > 0:
                                if peak > self.peaks[-1][1]:
                                    self.peaks.append((peak_time, peak))
                                    self.reference_value = peak
                                    self.reference_value_time = peak_time
                                    trough = 0.0
                                    trough_time = peak_time
                                    self.is_reference_value_changed = False
                                    # print(peaks)
                        elif len(self.peaks) > 1 and time_duration(self.peaks[-1][0],
                                                                   row['time']) < 2 and current_value < peak:
                            # to avoid duplicate peak value
                            continue

                        elif round(peak - self.reference_value, 0) > hike:
                            if peak - current_value > round(peak * diff_percent * 0.25 / 100, 0):
                                # print(f"peak formed...{peak}")
                                # any(value_to_check in tup for tup in list_of_tuples)
                                if not any(peak_time in time_value for time_value in self.peaks):
                                    self.peaks.append((peak_time, peak))
                                    self.reference_value = peak
                                    self.reference_value_time = peak_time
                                    trough = 0.0
                                    trough_time = peak_time
                                    self.is_reference_value_changed = False
                    else:
                        peak = current_value
                        peak_time = row['time']
                elif current_value < self.reference_value:
                    dip = round(self.reference_value * diff_percent / 100, 0)
                    if not self.is_reference_value_changed:
                        self.is_reference_value_changed = True
                    if trough != 0.0:
                        if current_value < trough:
                            # if current value is less than current trough, new trough is set.
                            trough = current_value
                            trough_time = row['time']
                            if len(self.troughs) > 0:
                                if trough < self.troughs[-1][1]:
                                    self.troughs.append((trough_time, trough))
                                    self.reference_value = trough
                                    self.reference_value_time = trough_time
                                    peak = 0.0
                                    peak_time = trough_time
                                    self.is_reference_value_changed = False
                                    # print(troughs)
                        elif len(self.troughs) > 1 and time_duration(self.troughs[-1][0],
                                                                     row['time']) < 2 and current_value > trough:
                            # to avoid duplicate trough value
                            continue

                        elif round(self.reference_value - current_value, 0) > dip:
                            if current_value - trough > round(trough * diff_percent * 0.2 / 100, 0):
                                # print(f"peak formed...{peak}
                                # any(value_to_check in tup for tup in list_of_tuples)
                                if not any(trough_time in time_value for time_value in self.troughs):
                                    self.troughs.append((trough_time, trough))
                                self.reference_value = trough
                                self.reference_value_time = trough_time
                                peak = 0.0
                                peak_time = trough_time
                                self.is_reference_value_changed = False
                                # print(troughs)
                    else:
                        trough = current_value
                        trough_time = row['time']
                        # print("trough is forming....")
                else:
                    continue

    # def script_analysis(self, exchange, script_token, script_name, action="buy"):
    def script_analysis(self):
        _ = self.api.set_session(userid=self.userid, password=self.userpasswd, usertoken=self.usersession)
        # get 1 minute data of a script upto current time. current interval is not included.
        is_data = False
        data = None
        while not is_data:
            data = self.api.get_time_price_series(exchange=self.exchange, token=self.script_token)
            if data is not None:
                is_data = True
        r_data = list(reversed(data))

        # Analysing Data
        # generating peaks and troughs from raw data
        self.get_peaks_troughs(r_data)
        print(f"INFO : {self.script_name} : script_analysis() -> All peaks found are {self.peaks}")
        print(f"INFO : {self.script_name} : script_analysis() -> All troughs found are {self.troughs}")
        # summarising peaks and troughs - removing consecutive peaks to consecutive troughs
        self.do_summerise_peaks_troughs(self.peaks, self.troughs)

        # Last Peak and Trough price difference
        self.set_last_peak_trough_price_diff()

        ### Logic for buying or not buying ####
        # Condition-01
        # peak = 0 and trough = 0 -> don't buy
        if len(self.peaks) == 0 and len(self.troughs) == 0:
            is_get_quote = False
            quote = None
            while not is_get_quote:
                quote = self.api.get_quotes(exchange=self.exchange, token=self.script_token)
                if quote is not None:
                    is_get_quote = True
            self.ltp = int(float(quote['lp']))
            # 'ltt' = '12:30:55'
            self.ltt = quote['ltt']

            # 'ltd' = '12-09-2024'
            self.ltd = quote['ltd']
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-01 -> LTP is {self.ltp} at {self.ltd} {self.ltt}")

            print(
                "INFO : {self.script_name} : script_analysis() -> Condition-01 -> There is no peak and no trough formed - NOT Tradable.")
            return False

        # Condition-02
        # peak = 0 and trough = 1 -> analyse for buying zpzz13up value from last trough ->
        # if (Opening_value - ltp > 1.2%*Opening_value) and (ltp - last_trough < 0.0013*last_trough):buy
        if len(self.peaks) == 0 and len(self.troughs) > 0:
            print(
                "INFO : {self.script_name} : script_analysis() -> Condition-02 -> There is no peak and trough(s) formed.")
            is_get_quote = False
            quote = None
            while not is_get_quote:
                quote = self.api.get_quotes(exchange=self.exchange, token=self.script_token)
                if quote is not None:
                    is_get_quote = True
            self.ltp = int(float(quote['lp']))

            # 'o' = '637.80' - Opening price
            self.opening_price = float(quote['o'])
            # 'ltt' = '12:30:55'
            self.ltt = quote['ltt']

            # 'ltd' = '12-09-2024'
            self.ltd = quote['ltd']

            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-02 ->  Opening Price is {self.opening_price}")
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-02 -> LTP is {self.ltp} at {self.ltd} {self.ltt}")
            # onep2_opening_price = round(0.012 * self.opening_price, 2)
            # zpzz13up_last_trough = round(self.troughs[-1][1] * 0.0013, 2)
            # if self.opening_price - self.ltp >= onep2_opening_price and self.ltp - self.troughs[-1][1] <= zpzz13up_last_trough:
            if is_down_ge(self.opening_price, self.ltp, DOWN_GE_MP_0) and is_up_le(self.troughs[-1][1], self.ltp,
                                                                                   UP_LE_MP) and self.duration_ltp_last_peak_trough() > 180:
                self.sell_margin = calculate_sell_margin(self.opening_price, self.ltp)
                print(
                    f"INFO : {self.script_name} : script_analysis() -> Condition-02 ->  {self.script_name} is Tradable sell margin {self.sell_margin}.")
                return True
            else:
                print(
                    f"INFO : {self.script_name} : script_analysis() -> Condition-02 ->  {self.script_name} is NOT Tradable.")
                return False

        # Condition-03
        # peak = 1 and trough = 0, -> analyse for buying using onep2down value from last peak ->
        # if (last_peak - ltp > 1.2%*last_peak):buy

        if len(self.peaks) > 0 and len(self.troughs) == 0:
            print(
                "INFO : {self.script_name} : script_analysis() -> Condition-03 -> There is no trough and peak(s) formed.")
            is_get_quote = False
            quote = None
            while not is_get_quote:
                quote = self.api.get_quotes(exchange=self.exchange, token=self.script_token)
                if quote is not None:
                    is_get_quote = True
            self.ltp = int(float(quote['lp']))

            # 'o' = '637.80' - Opening price
            self.opening_price = float(quote['o'])

            # 'ltt' = '12:30:55'
            self.ltt = quote['ltt']

            # 'ltd' = '12-09-2024'
            self.ltd = quote['ltd']
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-03 -> Opening Price is {self.opening_price}")
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-03 -> LTP is {self.ltp} at {self.ltd} {self.ltt}")

            if is_down_ge(self.peaks[-1][1], self.ltp, DOWN_GE_MP_1) and self.duration_ltp_last_peak_trough() > 180:
                self.sell_margin = calculate_sell_margin(self.opening_price, self.ltp)
                print(
                    f"INFO : {self.script_name} : script_analysis() -> Condition-03 ->  {self.script_name} is Tradable sell margin {self.sell_margin}.")
                return True
            else:
                print(
                    f"INFO : {self.script_name} : script_analysis() -> Condition-03 ->  {self.script_name} is NOT Tradable.")
                return False

        # Condition-04
        # peak > 1 and trough >1
        # Analyse peak to trough diff for every peaks and troughs

        if len(self.peaks) > 0 and len(self.troughs) > 0:
            is_get_quote = False
            quote = None
            while not is_get_quote:
                quote = self.api.get_quotes(exchange=self.exchange, token=self.script_token)
                if quote is not None:
                    is_get_quote = True
            self.ltp = int(float(quote['lp']))

            # 'o' = '637.80' - Opening price
            self.opening_price = float(quote['o'])

            # 'ltt' = '12:30:55'
            self.ltt = quote['ltt']

            # 'ltd' = '12-09-2024'
            self.ltd = quote['ltd']

            self.do_analyse_summerised_peak_trough_diff()

            # Analyse peak to trough diff for every peaks and troughs
            print(
                f"INFO: {self.script_name} : script_analysis() -> Condition-04  -> peak_trough_diff (Value_Difference, Time_Duration in min) - {self.peak_trough_diff}")

            # Analyse trough to peak diff for every peaks and troughs
            self.do_analyse_summerised_trough_peak_diff()
            print(
                f"INFO: {self.script_name} : script_analysis() -> Condition-04  -> trough_peak_diff (Value_Difference, Time_Duration in min) - {self.trough_peak_diff}")

            # Set min, average and max values for peak_trough_diff and trough_peak_diff
            self.set_min_avg_max_peak_trough_diff()
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> min_avg_max_peak_trough_diff (min, avg, max) -> {self.min_avg_max_peak_trough_diff}")

            self.set_min_avg_max_trough_peak_diff()
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> min_avg_max_trough_peak_diff (min, avg, max) -> {self.min_avg_max_trough_peak_diff}")

            # setting what(peak/trough) formed first and last.
            self.what_is_first()
            # print(f"INFO : script_analysis() -> Condition-04 -> first formed is {self.what_first}")
            self.what_is_last()
            # print(f"INFO : script_analysis() -> Condition-04 -> last formed is {self.what_last}")
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> Opening Price is {self.opening_price}")
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> LTP is {self.ltp} at {self.ltd} {self.ltt}")
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> last Peak is {self.summerised_peaks[-1]}")
            print(
                f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> last Trough is {self.summerised_troughs[-1]}")

            # self.duration_ltp_last_peak_trough()
            ####m Insert logic for Peak trend by self.analyse_peaks()
            if len(self.peaks) == 1 and len(self.troughs) == 1:
                # Condition-04 (PT/TP logic)
                print(
                    f"INFO : {self.script_name} : script_analysis() -> Condition-04 (PT/TP logic) -> first formed is {self.what_first}")
                # PT logic
                if self.what_first == 'peak' and is_up_le(self.troughs[-1][1], self.ltp, UP_LE_MP) and self.duration_ltp_last_peak_trough() > 180:
                    self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.ltp)
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (PT logic) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                    return True
                # TP logic
                elif self.what_first == 'trough' and is_down_ge(self.peaks[-1][1], self.ltp, DOWN_GE_MP_1) and self.duration_ltp_last_peak_trough() > 180:
                    self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.troughs[-1][1])
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (TP logic) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                    return True
                else:
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (PT/TP logic)->  {self.script_name} is NOT Tradable.")
                    return False

            elif len(self.peaks) == 2 and len(self.troughs) == 1 and self.what_first == 'peak':
                # Condition-04 (PTP logic)
                if is_down_ge(self.peaks[-1][1], self.ltp, DOWN_GE_MP_1) and self.duration_ltp_last_peak_trough() > 180:
                    self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.ltp)
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (PTP logic) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                    return True
                else:
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> Condition-04 (PTP logic) ->  {self.script_name} is NOT Tradable.")
                    return False

            elif len(self.peaks) == 1 and len(self.troughs) == 2 and self.what_first == 'trough':
                # Condition-04 (TPT logic)
                if is_up_le(self.troughs[-1][1], self.ltp, UP_LE_MP) and self.duration_ltp_last_peak_trough() > 180:
                    self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.troughs[-1][1])
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (TPT logic) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                    return True
                else:
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> Condition-04 (TPT logic) ->  {self.script_name} is NOT Tradable.")
                    return False

            elif len(self.peaks) == 2 and len(self.troughs) == 2 and self.what_first == 'peak':
                # Condition-04 (PTPT logic)
                if is_up_le(self.troughs[-1][1], self.ltp, UP_LE_MP) and self.duration_ltp_last_peak_trough() > 180:
                    self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.troughs[-1][1])
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (PTPT logic) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                    return True
                else:
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> Condition-04 (PTPT logic) ->  {self.script_name} is NOT Tradable.")
                    return False

            elif len(self.peaks) == 2 and len(self.troughs) == 2 and self.what_first == 'trough':
                # Condition-04 (TPTP logic)
                if is_down_ge(self.peaks[-1][1], self.ltp, DOWN_GE_MP_1) and self.duration_ltp_last_peak_trough() > 180:
                    self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.ltp)
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (TPTP logic) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                    return True
                else:
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 -> Condition-04 (TPTP logic) ->  {self.script_name} is NOT Tradable.")
                    return False

            else:
                # Condition-04 (any logic)
                summerised_peak_trend = self.analyse_summerised_peaks()
                if summerised_peak_trend == 'zz':
                    # Condition-04 (any+zz logic)
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+zz logic) -> Peak Trend is zigzag")
                    if self.what_last == 'peak':
                        if is_down_ge(self.peaks[-1][1], self.ltp, DOWN_GE_MP_1) and self.duration_ltp_last_peak_trough() > 180:
                            self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.ltp)
                            print(
                                f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+zz + peak_last logic ) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                            return True
                        print(f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+zz + peak_last logic ) ->  {self.script_name} is NOT Tradable.")
                        return False

                    elif self.what_last == 'trough':
                        if is_up_le(self.troughs[-1][1], self.ltp, UP_LE_MP) and self.duration_ltp_last_peak_trough() > 180:
                            self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.troughs[-1][1])
                            print(
                                f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+zz + trough_last logic) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                            return True
                        print(
                            f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+zz + trough_last logic) ->  {self.script_name} is NOT Tradable.")
                        return False
                    else:
                        print(
                            f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+zz logic) ->  {self.script_name} is NOT Tradable.")
                        return False
                elif summerised_peak_trend == 'dw':
                    # Condition-04 (any+dw logic)
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+dw logic) -> Peak Trend is downward")
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+dw logic) -> Analyse peaks diff")
                    peak_diff_max = self.do_analyse_peaks_diff_max()
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+dw logic) -> max diff amongst peaks is {peak_diff_max}")
                    max_peak = self.set_max_peak()
                    if peak_diff_max is not None and max_peak is not None and peak_diff_max < round(0.0032 * max_peak,
                                                                                                    2):
                        print(
                            f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+dw logic) -> max diff amongst peaks is within limit of 0.32 range")
                        if self.what_last == 'peak':
                            if is_down_ge(self.peaks[-1][1], self.ltp, DOWN_GE_MP_1) and self.duration_ltp_last_peak_trough() > 180:
                                self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.ltp, 0.30)
                                print(
                                    f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+dw + peak_last logic) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                                return True
                            print(
                                f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+dw + peak_last logic) ->  {self.script_name} is NOT Tradable.")
                            return False

                        elif self.what_last == 'trough':
                            if is_up_le(self.troughs[-1][1], self.ltp, UP_LE_MP) and self.duration_ltp_last_peak_trough() > 180:
                                self.sell_margin = calculate_sell_margin(self.peaks[-1][1], self.troughs[-1][1], 0.30)
                                print(
                                    f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+dw + trough_last logic) ->  {self.script_name} is Tradable with sell margin {self.sell_margin}.")
                                return True
                            print(
                                f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+dw + trough_last logic) ->  {self.script_name} is NOT Tradable.")
                            return False
                        else:
                            print(
                                f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+dw logic) ->  {self.script_name} is NOT Tradable.")
                            return False
                    else:
                        print(
                            f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any+zz logic) -> max diff amongst peaks is out of 0.32% range")
                        return False
                else:
                    print(
                        f"INFO : {self.script_name} : script_analysis() -> Condition-04 (any logic) ->  {self.script_name} is NOT Tradable.")
                    return False

api_ = NorenApiPy()
token = FTToken()
usersession = token.generate_token()
userid = token.user_id
userpasswd = token.passwd
s_name = 'ADANIGREEN-EQ'
s_token = '3563'
a_id = 'FT035389'

s_analysis = ScriptAnalysis(api_, userid=userid, userpasswd=userpasswd, usersession=usersession, script_name=s_name, script_token=s_token, account_id=a_id, exchange='NSE')
is_tradable = s_analysis.script_analysis()

if is_tradable:
    print("Tradable")
else:
    print("Not Tradable")