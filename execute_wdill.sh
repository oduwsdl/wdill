export PATH="/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
echo $(date)
echo "------------------------------------------"
cd <WDILL_PATH> && $(which python3) timelapseTwitter.py
echo "******************************************"
