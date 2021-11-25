# WiPiCap: Caputuring Wi-Fi CBR Frames Using RaspberryPi 
This project gives useful scripts and documents that help wireless sensing researchers who try to do experiments with Raspberry Pis.

## How It Works
WiPiCap enables your Rapsberry Pi to be into monitor mode, capture wireless packets and extract 802.11ac/ax Compressed Beamforming Report.

### **Installation**
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

## Capture Packets & Extract Compressed Beamforming Report
You have to do two things: set a network interface in monitor mode, capture packets.

### **Set Monitor Mode Interface**
Using our setup script is the better way to set a network interface in monitor mode listening to a certain channel:

```bash
sh set_interface.sh <channel_number>
```

You must make sure `aircrack-ng` is installed on your system.  A new network interface `wlan0mon` should be created for given channel number.

### **Traffic Generation**
Our observations show that it is necessary to generate continuous traffic in order to keep the acquisition of Compressed Beamforming Report at a constant level.  Thus, we recommend using iperf or ping to send UDP packets from Raspberry Pi to devices.  It is known that if there is no intentional traffic, the device communicates little or no Compressed Beamforming Report.

### **Packet Capture**
We recommend you to use `tcpdump` for packet capture.

```bash
sudo apt install tcpdump
```

To capture packtets with the interface `wlan0mon` and save `output.pcap`, run the following:

```bash
sudo tcpdump -i wlan0mon -w output.pcap
```

### **pcap_to_csv.sh**

Let your pcap file is `example.pcap`.  Then, run the following:

```bash
sh pcap_to_csv.sh example
```

You'll see `example.csv` is created.  Basically, you need not to edit the csv file.

### **binary_to_cbr.py**
This script convert Compressed Beamforming binary to a sort of real numbers.  Those numbers are called "phis and psis" which are given in the CSI compression procedure defined by 802.11ac standard.  For more detail, please read pp. 2398-2400 of [this](https://ieeexplore.ieee.org/document/7786995).

```python
python binary_to_cbr.py -i [INPUT CSV FILE] -a [TARGET MAC ADDRESS] -s [YYYYMMDDhhmmss] -e [YYYYMMDDhhmmss]
```

An input csv file should be generated by `pcap_to_csv.sh`.  In this case, "target mac address" indicates the mac address of the device (not APs or Raspberry Pis).

`binary_to_cbr.py` returns a pickle file that contains a Numpy matrix of compressed beamforming report.  The shape of the matrix is (packets, subcarriers, angles). 


### **Why do we use VHT Compressed Beamforming Report for wireless sensing application?**
Recent years, many researchers are eager to create powerful wireless sensing system.  Many of them use 802.11n CSI Tools (https://dhalperi.github.io/linux-80211n-csitool/) or Atheros CSI Tool (https://wands.sg/research/wifi/AtherosCSI/) to obtain raw CSI data but these tools require certain kind of Network Interface Card, so technological cost is too high.  Moreover, most modern wifi chips on major laptops don't have system to send raw CSI to access point.

In contrast, many devices conformable to 802.11ac send VHT Compressed Beamforming Report back to access points, and this signal is mathematical transformation of the original Channel Matrix.  We assume this signal can convey channel status and thus we can use it for wireless sensing.  VHT Compressed Beamforming Report can be acquired by normal packet capture.  No limitation or requirement about what kind of wifi chipset you use to capture wireless packets.

If you are interested in our idea to use this information for wireless sensing, please check below:

"CSI2Image: Image Reconstruction From Channel State Information Using Generative Adversarial Networks" (https://ieeexplore.ieee.org/document/9380376)

## FAQ
### - pcap_to_csv.sh returns nothing.
It is possible that you are not getting packets that contain Compressed Beamforming Report in the first place.
Try using iperf or ping to generate traffic while capturing packtes.
