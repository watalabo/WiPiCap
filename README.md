# WiPiCap: Caputuring Wi-Fi CBR Frames Using RaspberryPi 
This project gives useful scripts and documents that help wireless sensing researchers who try to do experiments with Raspberry Pis.

## How It Works
WiPiCap enables your Rapsberry Pi to be into monitor mode, capture wireless packets and extract 802.11ac/ax Compressed Beamforming Report.

## Installation
If you want to capture packets of wireless communication, you have to put a network interface into **Monitor mode**.  However, Raspberry Pi is not capable of having a monitor mode interface.  Nexmon firmware patch (https://github.com/seemoo-lab/nexmon) is C-based firmware patching framework for Broadcom WiFi chips that enables monitor mode on Raspberry Pi.

Nexmon firmware patch works with Broadcom WiFi chip **BCM43430A1** and **BCM43455C0**.  <br>BCM43430A1 is equipped on Raspberry Pi 3 and Zero W.  BCM43455C0 is equipped on Raspberry Pi 3B+ and 4.

The script `install.sh` is for BCM43455C0 only, so if you have Raspberry Pi 3B+ or 4.  If you want to use the script on Raspberry Pi 3 or Zero W, you have to modify some part of the codes.  The script works only on **Raspbian**, not for a latest Raspberry Pi OS.  Moreover, the setup script only works on kernel 5.4.  The raspberrypi-kernel-header for kernel 5.4 is currently not available from official package source, thus you have to build kernel headers by yourself before running install script(c.f. https://github.com/seemoo-lab/nexmon/issues/469).

Follow the instruction below to install:

```bash
sudo su
apt-mark hold raspberrypi-kernel
chmod u+x install.sh
./install.sh
```

Make sure you start working at `/home/pi/`.

<!-- To maintain the firmware changes after a reboot, perform the following steps:
- Find the path of the default driver at reboot: `modinfo brcmfmac`
- Backup the original driver: `mv "<PATH TO THE DRIVER>/brcmfmac.ko" "<PATH TO THE DRIVER>/brcmfmac.ko.orig"`
- Copy the modified driver: `cp /home/pi/WiPiCap/nexmon/patches/bcm43455c0/7_45_189/nexmon/brcmfmac_4.19.y-nexmon/brcmfmac.ko "<PATH>/"`
- Probe all modules and generate new dependency: `depmod -a` -->

## Capture Packets
You have to do two things: set a network interface in monitor mode, capture packets.

### **Set Monitor Mode Interface**
Using our setup script is the better way to set a network interface in monitor mode listening to a certain channel:

```bash
sh set_interface.sh <channel_number>
```

You must make sure `aircrack-ng` is installed on your system.  A new network interface `wlan0mon` should be created for given channel number.

### **Traffic Generation**
Our observations show that it is necessary to generate continuous traffic in order to keep the acquisition of Compressed Beamforming Report at a constant level.  Thus, we recommend using **iperf** or **ping** to send UDP packets from Raspberry Pi to devices.  It is known that the device communicates little or no Compressed Beamforming Report without intensive communiations.

### **Packet Capture**
We recommend you to use `tcpdump` for packet capture.

```bash
sudo apt install tcpdump
```

To capture packtets with the interface `wlan0mon` and save `output.pcap`, run the following:

```bash
sudo tcpdump -i wlan0mon -w output.pcap
```
## Scripts
### Step 1: pcap_to_csv.sh
```bash
sh pcap_to_csv.sh <path_to_pcap>
```
The above command generates a CSV file with the Beamforming Report extracted from the specified pcap file.
Basically, you need not to edit the csv file.

### Step 2: dataset_creator
Restore the V matrix from the CSV generated using `pcap_to_csv.sh`.

```bash
./dataset_creator --path <path_to_csv> --address <device_mac_addr>
```
The above command generates a matrix V restored from Compressed Beamforming Report.
The results are stored in a database file in SQLite format with the file name `cbr.db`.
The database

### Example
```bash
sh pcap_to_csv.sh example.pcap
./dataset_creator --path example.csv --address ff:ff:ff:ff:ff:ff
```

## FAQ
### Why do we use VHT Compressed Beamforming Report for wireless sensing application?
Recent years, many researchers are eager to create powerful wireless sensing system.  Many of them use 802.11n CSI Tools (https://dhalperi.github.io/linux-80211n-csitool/) or Atheros CSI Tool (https://wands.sg/research/wifi/AtherosCSI/) to obtain raw CSI data but these tools require certain kind of Network Interface Card, so technological cost is too high.  Moreover, most modern wifi chips on major laptops don't have system to send raw CSI to access point.

In contrast, many devices conformable to 802.11ac send VHT Compressed Beamforming Report back to access points, and this signal is mathematical transformation of the original Channel Matrix.  We assume this signal can convey channel status and thus we can use it for wireless sensing.  VHT Compressed Beamforming Report can be acquired by normal packet capture.  No limitation or requirement about what kind of wifi chipset you use to capture wireless packets.

If you are interested in our idea to use this information for wireless sensing, please check below:

"CSI2Image: Image Reconstruction From Channel State Information Using Generative Adversarial Networks" (https://ieeexplore.ieee.org/document/9380376)  
"CBR-ACE: Counting Human Exercise using Wi-Fi Beamforming Reports" (https://www.jstage.jst.go.jp/article/ipsjjip/30/0/30_66/_article/-char/ja/)

### - pcap_to_csv.sh returns nothing.
It is possible that you are not getting packets that contain Compressed Beamforming Report in the first place.
Try using iperf or ping to generate traffic while capturing packtes.
