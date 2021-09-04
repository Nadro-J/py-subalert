#!/bin/bash
# ----------------------------------------------------------
# Frequency                         | Name
# ----------------------------------------------------------
# At minute 0 past every 12th hour. | validator monitoring
# At 17:00 every day.               | Era graph
# Every hour                        | Tip monitoring
# Every hour                        | Latest repository release
# ----------------------------------------------------------
user=$(whoami)

echo "[+] Attempting to create PM2 application(s)"
pm2 start tx-alert.py --name transactions --interpreter=python3
pm2 start referenda-alert.py --name referenda --interpreter=python3
pm2 save

echo "[+] Creating cronjobs if they haven't been created already"
(crontab -l; echo "0 */12 * * * cd /$user/py-subalert && /usr/bin/python3 /$user/py-subalert/commission.py >> /$user/py-subalert/logs/validator_commission.log 2>&1") | sort -u | crontab -
(crontab -l; echo "0 17 * * * cd /$user/py-subalert && /usr/bin/python3 /$user/py-subalert/era-graph.py >> /$user/py-subalert/logs/era-graph.log 2>&1") | sort -u | crontab -
(crontab -l; echo "0 * * * * cd /$user/py-subalert && /usr/bin/python3 /$user/py-subalert/tip-alert.py >> /$user/py-subalert/logs/tip-alert.log 2>&1") | sort -u | crontab -
(crontab -l; echo "0 * * * * cd /$user/py-subalert && /usr/bin/python3 /$user/py-subalert/latest_repo_release.py >> /$user/py-subalert/logs/latest_repo_release.log 2>&1") | sort -u | crontab -

if [ ! -d /$user/py-subalert/logs ]; then
	echo "[+] Creating /logs directory for cronjob logging"
	mkdir -p /$user/py-subalert/logs;
else
  echo "[!] /logs directory already exists"
fi

if [ ! -d /$user/py-subalert/data-cache ]; then
	echo "[+] Creating /data-cache directory to store data"
	mkdir -p /$user/py-subalert/data-cache;
else
  echo "[!] /data-cache diretory already exists"
fi
