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

The script `picap.sh` is for BCM43455C0 only, so if you have Raspberry Pi 3B+ or 4, all you have to do is run the script.  If you want to use the script on Raspberry Pi 3 or Zero W, you have to modify some part of the codes.  The script works only on **Raspbian**.

## How to use json2csi.py?
Writing.

## How to use VHT Compressed Beamforming Report for wireless sensing application?
We give some ideas and concepts in Wiki.
