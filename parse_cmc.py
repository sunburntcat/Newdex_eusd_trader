
# Generates a cmc text file and then parses it to display the prices

import requests
import csv

from pprint import pprint

import time
import datetime

ts = time.time()
print "CMC price query USD ... " + datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M:%S')


with open('./cmc_prices.txt', 'wb') as f:
    writer = csv.writer(f,delimiter=' ')

    # Bitcoin
    url = "https://api.coinmarketcap.com/v1/ticker/bitcoin/"
    data = requests.get(url).json()
    btc_price=data[0]['price_usd']

    #url = "https://api.newdex.io/v1/price?symbol=bitpietokens-ebtc-eusd"
    #data = requests.get(url).json()
    #print(btc_price)
    #last_price=data['data']['price']
    #dist = abs((float(last_price) - float(btc_price))/2.0)
    #print(dist)

    # Ethereum
    url = "https://api.coinmarketcap.com/v1/ticker/ethereum/"
    data = requests.get(url).json()
    eth_price=data[0]['price_usd']

    # EOS
    url = "https://api.coinmarketcap.com/v1/ticker/eos/"
    data = requests.get(url).json()
    eos_price=data[0]['price_usd']

    # Tether
    url = "https://api.coinmarketcap.com/v1/ticker/tether/"
    data = requests.get(url).json()
    tether_price=data[0]['price_usd']

    # IQ
    url = "https://api.coinmarketcap.com/v1/ticker/everipedia/"
    data = requests.get(url).json()
    iq_price=data[0]['price_usd']

    writer.writerows([['Asset','USDprice'],['BTC',btc_price],['ETH',eth_price],['EOS',eos_price],['USDT',tether_price],['IQ',iq_price]])

