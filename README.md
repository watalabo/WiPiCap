# WiPiCap
This project gives useful scripts and documents that help wireless sensing researchers who try to do experiments with Raspberry Pis.
Detailed explanation of script is in Wiki.

## Codes
Sorry!! **All codes are currently not available**.  But don't worry.  We will back to you in a few weeks.

## How to enable Raspberry Pi to capture packets?
If you want to capture packets of wireless communication, you have to put a network interface into **Monitor mode**.  However, Raspberry Pi is not capable of having a monitor mode interface.  Nexmon firmware patch (https://github.com/seemoo-lab/nexmon) is C-based firmware patching framework for Broadcom WiFi chips that enables monitor mode on Raspberry Pi.

Nexmon firmware patch works with Broadcom WiFi chip **BCM43430A1** and **BCM43455C0**.  <br>BCM43430A1 is equipped on Raspberry Pi 3 and Zero W.  BCM43455C0 is equipped on Raspberry Pi 3B+ and 4.

The script `picap.sh` is for BCM43455C0 only, so if you have Raspberry Pi 3B+ or 4.  If you want to use the script on Raspberry Pi 3 or Zero W, you have to modify some part of the codes.  The script works only on **Raspbian**.  Moreover, Nexmon firmware patch only works on kernel 4.19.x.  Thus, if Rasbian runs on newer kernel, you have to downgrade the kernel in some way.

Follow the instruction below to install:

1. Type `sudo su` and enter the shell as root user.
2. Type `apt-mark hold raspberrypi-kernel` (this commmand prevent Raspbian kernel from updating.)
3. Type `chmod u+x picap.sh`.
4. Type `./picap.sh`

Make sure you start working at `/home/pi/`.

To maintain the firmware changes after a reboot, perform the following steps:
- Find the path of the default driver at reboot: `modinfo brcmfmac`
- Backup the original driver: `mv "<PATH TO THE DRIVER>/brcmfmac.ko" "<PATH TO THE DRIVER>/brcmfmac.ko.orig"`
- Copy the modified driver: `cp /home/pi/WiPiCap/nexmon/patches/bcm43455c0/7_45_189/nexmon/brcmfmac_4.19.y-nexmon/brcmfmac.ko "<PATH>/"`
- Probe all modules and generate new dependency: `depmod -a`

## How to capture packets?
You have to do two things: set a network interface in monitor mode, capture packets.
### Set Monitor Mode Interface
To set a network interface in monitor mode, we recommend you to use aircrack-ng.  You can install the tool by the command:

`sudo apt install aircrack-ng`

then run the following:

`sh set_interface.sh <channel_number>`


### Capture Packets
We recommend you to use `tcpdump` for packet capture.  You can install the tool by the following:

`sudo apt install tcpdump`

If you capture packtets with the interface `wlan0mon` and save `output.pcap`, run the following:

`sudo tcpdump -i wlan0mon -w output.pcap`

## How to use pcap2csv.sh?

Let your pcap file is `example.pcap`.  Then, run the following:

`sh pcap2csv.sh example`

then you'll see `example.csv` is created.  Basically, you need not to edit the csv file.

## How to use csi_extractor.py?


## The shape of Compressed CSI


## Why do we use VHT Compressed Beamforming Report for wireless sensing application?
Recent years, many researchers are eager to create powerful wireless sensing system.  Many of them use 802.11n CSI Tools (https://dhalperi.github.io/linux-80211n-csitool/) or Atheros CSI Tool (https://wands.sg/research/wifi/AtherosCSI/) to obtain raw CSI data but these tools require certain kind of Network Interface Card, so technological cost is too high.  Moreover, most modern wifi chips on major laptops don't have system to send raw CSI to access point.

In contrast, many devices conformable to 802.11ac send VHT Compressed Beamforming Report back to access points, and this signal is mathematical transformation of the original Channel Matrix.  We assume this signal can convey channel status and thus we can use it for wireless sensing.  VHT Compressed Beamforming Report can be acquired by normal packet capture.  No limitation or requirement about what kind of wifi chipset you use to capture wireless packets.

If you are interested in what VHT Compressed Beamforming Report is, or if you want to know our idea to use this information for wireless sensing, please check Wiki of this repository.

### !!For English Speakers!!
All documents on Wiki are now written in Japanese only.  We are preparing English documents, so please be patient!
