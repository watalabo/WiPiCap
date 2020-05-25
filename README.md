# WiPiCap
This project gives useful scripts and documents that help wireless sensing researchers who try to do experiments with Raspberry Pis.
Detailed explanation of script is in Wiki.

## Codes
### picap.sh
This script apply Nexmon firmware patch (https://github.com/seemoo-lab/nexmon) which enables Raspberry Pis have an network interface in monitor mode.

This script doesn't make any modification to original Nexmon software, so if you meet some kinds of errors, please check Nexmon official project page and deal with them.

### json2csi.py
This script extracts VHT Compressed Beamforming Report from packet data represented by JSON.
If you don't know how you can transcode pcap into json, please see https://www.wireshark.org/docs/man-pages/tshark.html.

This script parses JSON and reconstruct PHI/PSI angle values from raw hex data.
If you don't know what VHT Compressed Beamforming Report is, please see Wiki of this project.

## How to enable Raspberry Pi to capture packets?
If you want to capture packets of wireless communication, you have to put a network interface into **Monitor mode**.  However, Raspberry Pi is not capable of having a monitor mode interface.  Nexmon firmware patch (https://github.com/seemoo-lab/nexmon) is C-based firmware patching framework for Broadcom WiFi chips that enables monitor mode on Raspberry Pi.

Nexmon firmware patch works with Broadcom WiFi chip **BCM43430A1** and **BCM43455C0**.  <br>BCM43430A1 is equipped on Raspberry Pi 3 and Zero W.  BCM43455C0 is equipped on Raspberry Pi 3B+ and 4.

The script `picap.sh` is for BCM43455C0 only, so if you have Raspberry Pi 3B+ or 4.  If you want to use the script on Raspberry Pi 3 or Zero W, you have to modify some part of the codes.  The script works only on **Raspbian**.

Follow the instruction below to install:

1. Type `sudo su` and enter the shell as root user.
2. Type `chmod u+x picap.sh`.
3. Type `./picap.sh`

## How to use json2csi.py?
This script extracts VHT Compressed Beamforming Report from packet data represented by JSON.  Before run this script, ensure your JSON file is on the same directory as json2csi.py.  All you have to do is run the script.  No argument is needed.  When the script works well, `csi_orig.pkl` will created on the same directory.

## Why do we use VHT Compressed Beamforming Report for wireless sensing application?
Recent years, many researchers are eager to create powerful wireless sensing system.  Many of them use 802.11n CSI Tools (https://dhalperi.github.io/linux-80211n-csitool/) or Atheros CSI Tool (https://wands.sg/research/wifi/AtherosCSI/) to obtain raw CSI data but these tools require certain kind of Network Interface Card, so technological cost is too high.  Moreover, most modern wifi chips on major laptops don't have system to send raw CSI to access point.

In contrast, many devices conformable to 802.11ac send VHT Compressed Beamforming Report back to access points, and this signal is mathematical transformation of the original Channel Matrix.  We assume this signal can convey channel status and thus we can use it for wireless sensing.  VHT Compressed Beamforming Report can be acquired by normal packet capture.  No limitation or requirement about what kind of wifi chipset you use to capture wireless packets.

If you are interested in what VHT Compressed Beamforming Report is, or if you want to know our idea to use this information for wireless sensing, please check Wiki of this repository.

### !!For English Speakers!!
All documents on Wiki are now written in Japanese only.  We are preparing English documents, so please be patient!
