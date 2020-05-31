# WiPiCap
This project gives useful scripts and documents that help wireless sensing researchers who try to do experiments with Raspberry Pis.
Detailed explanation of script is in Wiki.

## Codes
### picap.sh
This script apply Nexmon firmware patch (https://github.com/seemoo-lab/nexmon) which enables Raspberry Pis have an network interface in monitor mode.

This script doesn't make any modification to original Nexmon software, so if you meet some kinds of errors, please check Nexmon official project page and deal with them.

### csi_extractor.py
This script extracts VHT Compressed Beamforming Report from packet data represented by CSV.
If you don't know how you can transcode pcap into CSV, please see Wiki.

This script parses CSV and reconstruct PHI/PSI angle values from raw hex data.
If you don't know what VHT Compressed Beamforming Report is, please see Wiki of this project.

## How to enable Raspberry Pi to capture packets?
If you want to capture packets of wireless communication, you have to put a network interface into **Monitor mode**.  However, Raspberry Pi is not capable of having a monitor mode interface.  Nexmon firmware patch (https://github.com/seemoo-lab/nexmon) is C-based firmware patching framework for Broadcom WiFi chips that enables monitor mode on Raspberry Pi.

Nexmon firmware patch works with Broadcom WiFi chip **BCM43430A1** and **BCM43455C0**.  <br>BCM43430A1 is equipped on Raspberry Pi 3 and Zero W.  BCM43455C0 is equipped on Raspberry Pi 3B+ and 4.

The script `picap.sh` is for BCM43455C0 only, so if you have Raspberry Pi 3B+ or 4.  If you want to use the script on Raspberry Pi 3 or Zero W, you have to modify some part of the codes.  The script works only on **Raspbian**.

Follow the instruction below to install:

1. Type `sudo su` and enter the shell as root user.
2. Type `chmod u+x picap.sh`.
3. Type `./picap.sh`

Make sure you start working on `/home/pi/`.

## How to capture packets?
You have to do two things: set a network interface in monitor mode, capture packets.
### Set Monitor Mode Interface
To set a network interface in monitor mode, we recommend you to use aircrack-ng.  You can install the tool by the command:

`sudo apt install aircrack-ng`

then run the following:

`sudo airmon-ng check kill && sudo airmon-ng wlan0 start`

Airmon tool kills all the processes which might have to do with wifi chip, and set a new monitor mode interface.  To check the name of the interface, you can use `iwconfig`.  While the monitor mode interface is active, the Raspberry Pi will lose wireless internet connection.

Next, check the channel.  For example, if you want to capture packets communicating on channel 48, type

`iwconfig <NAME OF MONITOR INTERFACE> channel 48`


### Capture Packets
We recommend you to use `tcpdump` for packet capture.  You can install the tool by the following:

`sudo apt install tcpdump`

If you capture packtets with the interface `wlan0mon` and save `output.pcap`, run the following:

`sudo tcpdump -i wlan0mon -w output.pcap`

## How to use pcap2csv.sh?

If your pcap file named `example.pcap`, run the following:

`sh pcap2csv.sh example.pcap`

then you'll see `example.csv` is created.  Basically, you need not to edit the csv file.

## How to use csi_extractor.py?
This script extracts VHT Compressed Beamforming Report from the csv mentioned above.  Before run this script, ensure your csv file is on the same directory as this script.  And check the MAC address of the device (because your devices send Compressed CSI back to AP and in this respect the device is "transmitter").

If your csv file named `example.csv` and the MAC address is `XX:XX:XX:XX:XX:XX`, run the following:

`python csi_extractor.py -i example.csv -a XX:XX:XX:XX:XX:XX`

then you'll see `csi_orig.csv` is created.

If you want to get the result in pickle format, add `-t pkl`.

`csi_extractor.py` automatically eliminates duplicated packets to ensure that there is one packet every 100 milliseconds.  If you feel this is annoying and want to get raw output, add `--raw`.  If you want to interpolate missing time, you can use `csi_interpolation.py`(coming soon!).

You can also get AoA(Angle of Arrival) information calculated from V matrix, and `-v` argument enable you to do that.

If you get the error: `not compatible antenna set`, we are sorry to say that `csi_extractor.py` cannot work under your setting.  Please make sure that your device communicates with AP by 3x3 or 3x2 MIMO.  (Why such a thing happen?  For more detail, please see the article in Wiki)

## The shape of Compressed CSI
In csv format, you'll see two columns, **timestamps** and **Compressed CSI**.
In pickle format, Compressed CSI is provided as a **dictionary type** object.  The keys are timestamps, and the values are Compressed CSI sequences.

In both format, a Compressed CSI sequence is stored in an array.  For example, if your wireless link has 20MHz channel width and 3x3 MIMO, you can get 312 Compressed CSI values: each of 52 subcarriers has 6 values, and these 312 values are stored in order of the subcarrier indexes.

If you add `-v` argument, you get information corresponding to AoA.  For example, if your wireless link has 20MHz channel width and 3x3 MIMO, you can get 52 values.

## Why do we use VHT Compressed Beamforming Report for wireless sensing application?
Recent years, many researchers are eager to create powerful wireless sensing system.  Many of them use 802.11n CSI Tools (https://dhalperi.github.io/linux-80211n-csitool/) or Atheros CSI Tool (https://wands.sg/research/wifi/AtherosCSI/) to obtain raw CSI data but these tools require certain kind of Network Interface Card, so technological cost is too high.  Moreover, most modern wifi chips on major laptops don't have system to send raw CSI to access point.

In contrast, many devices conformable to 802.11ac send VHT Compressed Beamforming Report back to access points, and this signal is mathematical transformation of the original Channel Matrix.  We assume this signal can convey channel status and thus we can use it for wireless sensing.  VHT Compressed Beamforming Report can be acquired by normal packet capture.  No limitation or requirement about what kind of wifi chipset you use to capture wireless packets.

If you are interested in what VHT Compressed Beamforming Report is, or if you want to know our idea to use this information for wireless sensing, please check Wiki of this repository.

### !!For English Speakers!!
All documents on Wiki are now written in Japanese only.  We are preparing English documents, so please be patient!
