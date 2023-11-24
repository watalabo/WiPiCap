# !!!Maintenance Announcement!!!
The author himself plans to re-check the scripts and make major updates. Maintenance will continue until the end of 2023 at the latest. Please be aware when referring to this repository.

# WiPiCap: Wi-Fi CBR Frames Parser
This project gives useful scripts and documents that help wireless sensing researchers who try to implement sensing system with IEEE 802.11ac VHT Compressed Beamforming Report.

# Installation
Content will be coming here soon...

## Packet Capture
Content will be coming here soon...

## FAQ
### Why do we use VHT Compressed Beamforming Report for wireless sensing application?
Recent years, many researchers are eager to create powerful wireless sensing system.  Many of them use 802.11n CSI Tools (https://dhalperi.github.io/linux-80211n-csitool/) or Atheros CSI Tool (https://wands.sg/research/wifi/AtherosCSI/) to obtain raw CSI data but these tools require certain kind of Network Interface Card, so technological cost is too high.  Moreover, most modern wifi chips on major laptops don't have system to send raw CSI to access point.

In contrast, many devices conformable to 802.11ac send VHT Compressed Beamforming Report back to access points, and this signal is mathematical transformation of the original Channel Matrix.  We assume this signal can convey channel status and thus we can use it for wireless sensing.  VHT Compressed Beamforming Report can be acquired by normal packet capture.  No limitation or requirement about what kind of wifi chipset you use to capture wireless packets.

If you are interested in our idea to use this information for wireless sensing, please check below:

"CSI2Image: Image Reconstruction From Channel State Information Using Generative Adversarial Networks" (https://ieeexplore.ieee.org/document/9380376)  
"CBR-ACE: Counting Human Exercise using Wi-Fi Beamforming Reports" (https://www.jstage.jst.go.jp/article/ipsjjip/30/0/30_66/_article/-char/ja/)
