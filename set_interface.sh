airmon-ng check kill
sleep 1
airmon-ng start wlan0
ifconfig wlan0 down
iwconfig wlan0mon channel $1
ifconfig wlan0 up