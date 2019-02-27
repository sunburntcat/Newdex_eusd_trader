# Uses cmc_prices.txt to estimate newdex asset usd prices

import requests
import csv

import time
import datetime

ts = time.time()
print "Newdex price query USD ... " + datetime.datetime.fromtimestamp(ts).strftime('%m-%d %H:%M:%S')

with open('cmc_prices.txt', mode='r') as file:
    csv_reader = csv.reader(file,delimiter=' ')
    cmc_prices = dict((rows[0],rows[1]) for rows in csv_reader)


eos_usd_price=float(cmc_prices["EOS"])


with open('./newdex_prices.txt', 'wb') as f:
    writer = csv.writer(f,delimiter=' ')

    url = "https://api.newdex.io/v1/price?symbol=betdicetoken-dice-eos"
    data = requests.get(url).json()
    if data['code'] != 200:
        print "Newdex returned non-200 code when querying price"
        print data
        exit(-1)
    dice_eos_price=data['data']['price']
    dice_eusd_price = (eos_usd_price*dice_eos_price)

    url = "https://api.newdex.io/v1/price?symbol=eosiomeetone-meetone-eos"
    data = requests.get(url).json()
    if data['code'] != 200:
        print "Newdex returned non-200 code when querying price"
        print data
        exit(-1)
    meetone_eos_price=data['data']['price']
    meetone_eusd_price = (eos_usd_price*meetone_eos_price)

    url = "https://api.newdex.io/v1/price?symbol=eosvegascoin-mev-eos"
    data = requests.get(url).json()
    if data['code'] != 200:
        print "Newdex returned non-200 code when querying price"
        print data
        exit(-1)
    mev_eos_price=data['data']['price']
    mev_eusd_price = (eos_usd_price*mev_eos_price)

    writer.writerows([['Asset','USDprice'],
                    ['DICE',dice_eusd_price],
                    ['MEETONE',meetone_eusd_price],
                    ['MEV',mev_eusd_price]])

