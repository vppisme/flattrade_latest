def get_margin(ltp):
    if ltp < 100:
        return {'buy_margin': 0.2,
                'sell_margin': 0.5,
                'new_buy_value_margin': 0.4,
                'too_high_diff': 1.1,
                'max_buy_order_update_margin': 2.0}

    elif ltp < 201:
        return {'buy_margin': 0.3,
                'sell_margin': 0.7,
                'new_buy_value_margin': 0.6,
                'too_high_diff': 2.5,
                'max_buy_order_update_margin': 2.5}

    elif ltp < 301:
        return {'buy_margin': 0.3,
                'sell_margin': 0.9,
                'new_buy_value_margin': 0.7,
                'too_high_diff': 3.1,
                'max_buy_order_update_margin': 2.5}

    elif ltp < 400:
        return {'buy_margin': 0.3,
                'sell_margin': 1.1,
                'new_buy_value_margin': 1.0,
                'too_high_diff': 3.7,
                'max_buy_order_update_margin': 3.0}

    elif ltp < 501:
        return {'buy_margin': 0.3,
                'sell_margin': 1.2,
                'new_buy_value_margin': 1.0,
                'too_high_diff': 3.7,
                'max_buy_order_update_margin': 4.0}

    elif ltp < 801:
        return {'buy_margin': 0.4,
                'sell_margin': 1.5,
                'new_buy_value_margin': 1.0,
                'too_high_diff': 4.3,
                'max_buy_order_update_margin': 5.0}

    elif ltp < 901:
        return {'buy_margin': 0.4,
                'sell_margin': 1.8,
                'new_buy_value_margin': 1.2,
                'too_high_diff': 3.0,
                'max_buy_order_update_margin': 5.0}

    elif ltp < 1001:
        return {'buy_margin': 0.5,
                'sell_margin': 2.0,
                'new_buy_value_margin': 1.5,
                'too_high_diff': 3.3,
                'max_buy_order_update_margin': 10.0}

    elif ltp < 1401:
        return {'buy_margin': 0.5,
                'sell_margin': 2.3,
                'new_buy_value_margin': 1.5,
                'too_high_diff': 5.7,
                'max_buy_order_update_margin': 10.0}

    elif ltp < 1501:
        return {'buy_margin': 0.5,
                'sell_margin': 2.5,
                'new_buy_value_margin': 2.0,
                'too_high_diff': 6.7,
                'max_buy_order_update_margin': 10.0}

    elif ltp < 2001:
        return {'buy_margin': 1.0,
                'sell_margin': 2.8,
                'new_buy_value_margin': 2.5,
                'too_high_diff': 6.7,
                'max_buy_order_update_margin': 12.0}

    elif ltp < 2501:
        return {'buy_margin': 1.0,
                'sell_margin': 3.3,
                'new_buy_value_margin': 2.7,
                'too_high_diff': 6.7,
                'max_buy_order_update_margin': 12.0}

    elif ltp < 3001:
        return {'buy_margin': 2.0,
                'sell_margin': 4.2,
                'new_buy_value_margin': 3.75,
                'too_high_diff': 9.7,
                'max_buy_order_update_margin': 15.0}

    elif ltp < 3501:
        return {'buy_margin': 2.0,
                'sell_margin': 5.2,
                'new_buy_value_margin': 4.0,
                'too_high_diff': 10.7,
                'max_buy_order_update_margin': 15.0}

    elif ltp < 3801:
        return {'buy_margin': 2.0,
                'sell_margin': 6.5,
                'new_buy_value_margin': 4.0,
                'too_high_diff': 10.7,
                'max_buy_order_update_margin': 15.0}

    elif ltp < 4001:
        return {'buy_margin': 2.5,
                'sell_margin': 7.5,
                'new_buy_value_margin': 5.0,
                'too_high_diff': 15.7,
                'max_buy_order_update_margin': 20.0}

    elif ltp < 4501:
        return {'buy_margin': 2.5,
                'sell_margin': 15.0,
                'new_buy_value_margin': 5.0,
                'too_high_diff': 20.7,
                'max_buy_order_update_margin': 20.0}

    elif ltp < 5001:
        return {'buy_margin': 3.0,
                'sell_margin': 20.0,
                'new_buy_value_margin': 5.0,
                'max_buy_order_update_margin': 25.0}

    elif ltp < 5501:
        return {'buy_margin': 3.0,
                'sell_margin': 25.0,
                'new_buy_value_margin': 5.0,
                'too_high_diff': 35.7,
                'max_buy_order_update_margin': 25.0}

    elif ltp < 6001:
        return {'buy_margin': 3.0,
                'sell_margin': 30.0,
                'new_buy_value_margin': 5.0,
                'too_high_diff': 50.7,
                'max_buy_order_update_margin': 30.0}

    else:
        return {'buy_margin': 3.0,
                'sell_margin': 40.0,
                'new_buy_value_margin': 5.0,
                'too_high_diff': 60.7,
                'max_buy_order_update_margin': 30.0}
