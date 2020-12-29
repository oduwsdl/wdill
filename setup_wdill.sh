#!/bin/bash

sed -i "s@<WDILL_PATH>@$(pwd)@" crontab
sed -i "s@<WDILL_PATH>@$(pwd)@" execute_wdill.sh

crontab /etc/cron.d/wdill-cron
chmod 0644 /etc/cron.d/wdill-cron
touch /var/log/cron.log
pip install -r requirements.txt
npm install -g