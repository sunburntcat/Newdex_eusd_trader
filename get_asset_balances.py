# Uses cmc_prices.txt to estimate newdex asset usd prices

import requests
import json
import csv
import time
import os

import hashlib
import hmac

asset_dict = { "EOS": "eosio.token",
        "EBTC": "bitpietokens",
        "EETH": "bitpietokens",
        "DICE": "betdicetoken",
        "MEETONE": "eosiomeetone",
        "MEV": "eosvegascoin"
        }

with open('cmc_prices.txt', mode='r') as file:
    csv_reader = csv.reader(file,delimiter=' ')
    cmc_prices = dict((rows[0],rows[1]) for rows in csv_reader)

api_key=<Your newdex API key>
secret_key=<Your newdex API secret key>

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



