import time
import requests as re
import sys
from Robinhood import Robinhood
import json
import datetime
from twilio.rest import Client
import os

twilio_send_number = f"+1{os.environ['TWILIO_FROM_NO']}"
recv_number = f"+1{os.environ['CELLPHONE_NO']}"
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']

client = Client(account_sid, auth_token)

def send_message(msg):
    client.messages.create(
    to = recv_number,
    from_ = twilio_send_number,
    body = msg
    )
    return True


rb = Robinhood()
rb.login()

positions_response = rb.securities_owned()
symbols = []
positions = {}


for p in positions_response['results']:
    url = p['instrument']
    response = re.get(url)
    data = response.json()
    # print(data['symbol'])
    symbols.append(data['symbol'])
    positions[data['symbol']] = {'Position': float(p['average_buy_price']),
                                # 'Non_intraday_quantity': float(p['quantity']) - float(p['intraday_quantity']),
                                'Quantity': float(p['quantity']),
                                }

symbols_str = ",".join(symbols)

print('checking if its 8 am..')
while datetime.datetime.utcnow().hour < 14:
    time.sleep(60*20)
    continue

counter  = 0
potential_sell_list = {}
second_strike = []
print('starting quote checker...')
print(symbols_str)
while datetime.datetime.utcnow().hour < 23:
    text_list = {
    'Initial Strike': [],
    'Second Strike': [],}
    try:
        quote = rb.quote_data(symbols_str)
        # print(json.dumps(quote, indent=4, sort_keys=False))
        # print(len(quote['results']))
        for q in quote['results']:
            # print(json.dumps(q, indent=4, sort_keys=False))
            pct_diff = (float(q['last_trade_price']) - positions[q['symbol']]['Position']) / positions[q['symbol']]['Position']
            # print(pct_diff)
            if pct_diff > .02:
                if q['symbol'] in potential_sell_list.keys():
                    if (counter - potential_sell_list[q['symbol']]['counter'] > 20) and (q['symbol'] not in second_strike):
                        text_list['Second Strike'].append(q['symbol'])
                        second_strike.append(q['symbol'])
                else:
                    potential_sell_list[q['symbol']] = {'pct_diff': pct_diff,
                                                'counter': counter,}
                    text_list['Initial Strike'].append(q['symbol'])
        if text_list['Initial Strike'] or text_list['Second Strike']:
            send_message(
            f"First Strike: {text_list['Initial Strike']} \nSecond Strike: {text_list['Second Strike']}")

    except Exception as e:
        print(e)
        rb.login()

    counter += 1
    time.sleep(20)
