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

Nexmon firmware patch doesn't overwrite Wifi driver.  Thus, Raspberry Pi will lose its ability to have monitor interface after reboot.  To enable the ability even after reboot, please follow the instruction below.

1. Run the command.  
`modinfo brcmfmac`
2. Output would be like this:  
```
filename:       /lib/modules/4.19.97-v7+/kernel/drivers/net/wireless/broadcom/brcm80211/brcmfmac/brcmfmac.ko
license:        Dual BSD/GPL
description:    Broadcom 802.11 wireless LAN fullmac driver.
author:         Broadcom Corporation
firmware:       brcm/brcmfmac4373-sdio.bin
.....
```
Remember `filename` shown in above.

3. Run the command.  In this case, `<PATH>` is `/lib/modules/4.19.97-v7+/kernel/drivers/net/wireless/broadcom/brcm80211/brcmfmac`.
```mv "<PATH>/brcmfmac.ko" "<PATH>/brcmfmac.ko.orig"
cp /home/pi/nexmon/patches/bcm43455c0/7_45_189/nexmon/brcmfmac_4.19.y-nexmon/brcmfmac.ko "<PATH>/"
depmod -a```


## How to use json2csi.py?
Writing.

## How to use VHT Compressed Beamforming Report for wireless sensing application?
We give some ideas and concepts in Wiki.
