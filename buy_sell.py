
import requests
import csv
import time
import os

import math


import get_asset_balances

if not get_asset_balances.Success:
    print "  Get asset balance script was not successful, so buy_sell will not run."
    exit(-1)

# Pause to avoid server limit error going forward
time.sleep(1)

asset_dict = { "EOS": "eosio.token",
        "EBTC": "bitpietokens",
        "EETH": "bitpietokens",
        "DICE": "betdicetoken",
        "MEETONE": "eosiomeetone",
        "MEV": "eosvegascoin"
        }

# Define truncate function to avoid attempting to sell amounts just outside our balance
def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n


##################################

#Read in newdex prices
with open('newdex_prices.txt', mode='r') as file:
    csv_reader = csv.reader(file,delimiter=' ')
    newdex_prices = dict((rows[0],rows[1]) for rows in csv_reader)
#Read in coinmarketcap prices
with open('cmc_prices.txt', mode='r') as file:
    csv_reader = csv.reader(file,delimiter=' ')
    cmc_prices = dict((rows[0],rows[1]) for rows in csv_reader)
#Concatenate the two dictionaries to obtain all prices
all_prices = dict(newdex_prices.items() + cmc_prices.items())


#Read in allotment dictionary
with open('allotment.input', mode='r') as file:
    csv_reader = csv.reader(file,delimiter=' ')
    allotments = dict((rows[0],rows[1]) for rows in csv_reader)


#Read in asset balances with account balance and entrusted as a tuple
with open('balances.txt', mode='r') as file:
    csv_reader = csv.reader(file,delimiter=' ')
    asset_balances = dict((rows[0],(rows[1],rows[2])) for rows in csv_reader)

##################################

#Unlock wallet
cmd="cleos wallet unlock --password " + <Your cleos password>
print os.popen(cmd).read()

# Begin looping over keys
for key in asset_dict.keys():

    if key == "EBTC" or key == "EETH":
        real_price = float(all_prices[key[1:]]) # Remove the E in front of BTC/ETH
    else:
        real_price = float(all_prices[key])

    # EUSD is backed by tether, so do slight adjustment to account for non-perfect tether price
    real_price = real_price / float(all_prices['USDT'])

    # Get last price
    query = "symbol=" + asset_dict[key] + "-" + key.lower() + "-eusd"
    url = "https://api.newdex.io/v1/price?" + query
    data = requests.get(url).json()
    if data['code'] != 200:
        print "Newdex returned non-200 code when querying price"
        print data
        exit(-1)
    last_price = float(data["data"]["price"])

    # Get the market inefficiency
    inefficiency = abs( real_price - last_price )
    if inefficiency / real_price < 0.005:  # If the inefficiency is too small, move to the next asset
        continue

    # Get prices we want to buy/sell at 
    buy_price = real_price - 0.75*inefficiency
    sell_price = real_price + 0.75*inefficiency
    
    
    # Determine sell amount
    sell_amt = float(asset_balances[key][0])
    sell_amt = truncate(sell_amt,4) # Avoids trying to sell amounts just outside our balance

    # Determine buy amount in eusd
    allotted_EUSD = float(allotments[key])
    buy_amt_eusd = allotted_EUSD - (float(asset_balances[key][1]) + sell_amt)*buy_price
    if buy_amt_eusd > float(asset_balances["EUSD"][0]): # If buy order too large, use what's available
        buy_amt_eusd = truncate(float(asset_balances["EUSD"][0]),4)

    print "Want to buy " + str(buy_amt_eusd) + " USD worth of tokens at " + key + " at " + str(buy_price)
    print "Want to sell " + str(sell_amt) + " " + key + " at " + str(sell_price)


    if sell_amt > 0.005:  # Even for BTC this is small.
        memo='{"type":"sell-limit","symbol":"'+asset_dict[key]+'-'+key.lower()+'-eusd","price":"'+str(sell_price)+'","channel":"API"}'
        cmd='cleos -u https://api.cypherglass.com transfer -c ' + asset_dict[key] + ' '+<Your EOS acct name>+' newdexpocket ' + '"'+str('%.4f' % sell_amt)+' '+key+'" \''+memo+'\''
        print cmd
        print os.popen(cmd).read()

    if buy_amt_eusd > 1.0:  # Greater than 1 dollar
        memo='{"type":"buy-limit","symbol":"'+asset_dict[key]+'-'+key.lower()+'-eusd","price":"'+str(buy_price)+'","channel":"API"}'
        cmd='cleos -u https://api.cypherglass.com transfer -c bitpietokens '+<Your EOS acct name>+' newdexpocket ' + '"'+str('%.4f' % buy_amt_eusd)+' EUSD" \''+memo+'\''
        print cmd
        print os.popen(cmd).read()


