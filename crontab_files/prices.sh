cd /home/ubuntu/newdex/new_newdex  # Pointing to your project directory

# Get coinmarketcap prices
python parse_cmc.py >> cron_prices.log

counter=0
false  # Want to set $? to non-zero return
while [ $? -ne 0 ]
do

   sleep 10
   counter=$((counter+1))

   if [ $counter -gt 5 ]
   then
        echo "Maximum number of newdex price query attempts reached." >> cron_prices.log
   else
        # Get newdex prices
        python newdex_usd.py >> cron_prices.log
   fi

done
