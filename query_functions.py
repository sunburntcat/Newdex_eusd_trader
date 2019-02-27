
# Uses cmc_prices.txt to estimate newdex asset usd prices

import requests
import json
import csv
import time
import os

import hashlib
import hmac


def get_signature( message, secret_key ):

    utf8message = bytes(message).encode('utf-8')
    utf8secret_key = bytes(secret_key).encode('utf-8')
    signature = hmac.new(key=utf8secret_key, msg=message, digestmod=hashlib.sha256).hexdigest()

    return signature


def get_newdex_open_orders( symbol ):
    # Gets all open orders from newdex and returns the json data output

    api_key=<Your Newdex API key>
    secret_key=<Your Newdex API Secret key>

    message = 'api_key=' + api_key + '&symbol=' + symbol + '&state=pending&size=50&timestamp=' + str(int(time.time()))
    signature = get_signature( message, secret_key )
    url = "https://api.newdex.io/v1/order/orders?"+ message + "&sign=" + signature
    data = requests.get(url).json()

    if data["code"] != 200:
        # Try a second attempt
        message = 'api_key=' + api_key + '&symbol=' + symbol + '&state=pending&size=50&timestamp=' + str(int(time.time()))
        signature = get_signature( message, secret_key )
        url = "https://api.newdex.io/v1/order/orders?"+ message + "&sign=" + signature
        data = requests.get(url).json() # Try again.

        if data["code"] != 200:
            print data
            raise ValueError("  Newdex api returned non-200 status after OPEN ORDERS query")

        return data["data"]
    return data["data"]
    
    
def cancel_newdex_order( trx_id ):
    # Cancels an order on new_dex, given the EOS trx_id
    #   NOTE: This implementation assumes its ok if the cancel fails, since it's not a high priority

    api_key=<Your Newdex API key>
    secret_key=<Your Newdex API Secret key>

    message = 'api_key=' + api_key + '&trx_id=' + trx_id + '&timestamp=' + str(int(time.time()))
    signature = get_signature( message, secret_key )
    url = "https://api.newdex.io/v1/order/cancel?"+ message + "&sign=" + signature
    print "  Cancelling old API order associated with trx_id: " + trx_id
    data = requests.get(url).json()
    if data["code"] != 200:
        print "  Newdex api returned non-200 status after CANCEL ORDER assertion. This is ok. Not exitting at this time."
        print data

def get_trx_memo( trx_id ):
    # Return the memo of the transaction identified by trx_id

    url='cleos -u https://eos.greymass.com get transaction ' + trx_id
    trx_info = json.loads(os.popen(url).read())
    return trx_info["trx"]["trx"]["actions"][0]["data"]["memo"]

def get_currency_balance( symbol, contract ):
    # Return the balance of an asset on the EOS blockchain

    endpoint='https://mainnet.eoscanada.com'

    cmd = "cleos -u " + endpoint + " get currency balance " + contract + " "+<Your EOS acct name>+" " + symbol
    asset_balance = os.popen(cmd).read().split(" ")[0]
    if asset_balance == "":
        asset_balance = 0

    return asset_balance

with open('./balances.txt', 'wb') as f:
    writer = csv.writer(f,delimiter=' ')
    writer.writerow(['Asset','AcctBalance','Entrusted'])


    for key in asset_dict.keys():

        #### Deterimine the amount of ASSET in account ####
        cmd = "cleos -u https://mainnet.eoscanada.com get currency balance " + asset_dict[key] + " "+<Your EOS acct name>+" " + key.lower()
        asset_balance = os.popen(cmd).read().split(" ")[0]
        if asset_balance == "":
            asset_balance = 0

        #######################################################
        
        #### Determine the amount of ASSET locked away in newdex contracts ####


        symbol = asset_dict[key] +  "-" + key.lower() + "-eusd"

        timestamp = str(int(time.time()))

        message = 'api_key=' + api_key + '&symbol=' + symbol + '&state=pending&timestamp=' + timestamp

        utf8message = bytes(message).encode('utf-8')
        utf8secret_key = bytes(secret_key).encode('utf-8')
        signature = hmac.new(key=utf8secret_key, msg=message, digestmod=hashlib.sha256).hexdigest()

        url = "https://api.newdex.io/v1/order/orders?"+ message + "&sign=" + signature
        data = requests.get(url).json()
        if data["code"] != 200:
            data = requests.get(url).json() # Try again. NOTE: This needs to be updated. newdex doesn't like the expired timestamp
            if data["code"] != 200:
                print "  Newdex api returned non-200 status after OPEN ORDERS query"
                print data
                Success=0
                exit(-1)
                
        entrusted = 0
        for i in range(len(data["data"])):
            order = data["data"][i]

            # Check if order is open and adjust entrusted amount
            if (order["state"] == "new" or order["state"] == "partially-filled"):
                entrusted += ( float(order["amount"]) - float(order["deal_amount"]) )

                # Cancel order if hasn't been touched in 2 days
                if int(timestamp) - int(order["updated_at"]) > 172800: # 2 days

                    # Check if the order was initialized by API. We want to avoid cancelling manual orders done on web
                    url='cleos -u https://eos.greymass.com get transaction ' + order["trx_id"]
                    trx_info = json.loads(os.popen(url).read())

                    if "API" in trx_info["trx"]["trx"]["actions"][0]["data"]["memo"]:

                        timestamp = str(int(time.time())) #Update timestamp, because order query may have been a few secs ago
                        message = 'api_key=' + api_key + '&trx_id=' + order["trx_id"] + '&timestamp=' + timestamp
                        utf8message = bytes(message).encode('utf-8')
                        utf8secret_key = bytes(secret_key).encode('utf-8')
                        signature = hmac.new(key=utf8secret_key, msg=message, digestmod=hashlib.sha256).hexdigest()

                        print "  Cancelling old API order associated with trx_id: " + order["trx_id"]
                        url_cancel = "https://api.newdex.io/v1/order/cancel?"+ message + "&sign=" + signature
                        data_cancel = requests.get(url_cancel).json()
                        if data["code"] != 200:
                            print "  Newdex api returned non-200 status after CANCEL ORDER assertion. This is ok. Not exitting at this time."
                            print data

        #######################################################################


        writer.writerow([key,asset_balance,entrusted])

        # Wait half a second to reduce chance of server denial
        time.sleep(0.5)

    # Outside of the for loop, we'll write the number of EUSD to file, with "entrusted" equal to 0
    cmd = "cleos -u https://mainnet.eoscanada.com get currency balance bitpietokens "+<Your EOS acct name>+" EUSD"
    asset_balance = os.popen(cmd).read().split(" ")[0]
    if asset_balance == "":
        asset_balance = 0
    writer.writerow(["EUSD",asset_balance,"0"])


Success=1



