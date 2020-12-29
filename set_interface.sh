sudo airmon-ng check kill && sudo airmon-ng wlan0 start
ifconfig wlan0 down
iwconfig wlan0mon channel $1
ifconfig wlan0 up