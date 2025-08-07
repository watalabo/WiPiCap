# 🎉 Latest Update (08/07/2025)
C++ implementation is released!  Much faster than Python version, fast enough for real-time stream decoding and visualization.

# WiPiCap: Wi-Fi CBR Frames Parser
This project gives useful scripts and documents to help researchers who try to implement wireless sensing system with IEEE 802.11ac VHT / 802.11ax HE Compressed Beamforming Report.

## Motivation

In recent years, numerous researchers have been actively pursuing the development of robust wireless sensing systems that can be seamlessly integrated with widely deployed Wi-Fi networks. Many of these researchers have opted to utilize 802.11n CSI Tools (https://dhalperi.github.io/linux-80211n-csitool/) or Atheros CSI Tool (https://wands.sg/research/wifi/AtherosCSI/) to obtain raw CSI data. However, these tools necessitate the use of specific network interface cards, resulting in a significant technological cost. Furthermore, the majority of contemporary Wi-Fi chips incorporated in major laptops lack the capability to transmit raw CSI data to the access point.

In contrast, many devices conforming to 802.11ac transmit VHT Compressed Beamforming Report (CBR) back to access points. This signal is a mathematical transformation of the original channel matrix. We presume this signal conveys channel status, enabling its utilization for wireless sensing. VHT CBR can be acquired through standard packet capture. Notably, there are no limitations or requirements regarding the Wi-Fi chipset because CBR is protocol-compliant feedback. For further details on the mathematical transformation from CSI into CBR, please refer to the appendix (which will be available shortly).

If you are interested in our idea to use this information for wireless sensing, please check our previous works:
CSI2Image: Image Reconstruction From Channel State Information Using Generative Adversarial Networks (https://ieeexplore.ieee.org/document/9380376)

CBR-ACE: Counting Human Exercise using Wi-Fi Beamforming Reports (https://www.jstage.jst.go.jp/article/ipsjjip/30/0/30_66/_article/-char/ja/)

---

## Installation
1. Install dependencies. `pip install -r requirements.txt`
2. Build the package. `python setup.py build_ext --inplace`

## Example
WiPiCap is an easy-to-use CBR parser that reconstruct V matrix from pcap file directly.
```python
from wipicap import get_v_matrix

v_matrix = get_v_matrix(pcap_file='./test.pcap', address='11:22:33:44:55:66', bw=80)
# v_matrix is a complex-valued ndarray with the shape of (packets, subcarriers, rx, tx)
```

![wipicap_example](wipicap_example.png)

---

## Packet Capture
Please check appendix (will be ready soon...) to know how to build your own testbed for packet capture, on Raspberry Pi 3B+/4 using Nexmon firmware patch (https://github.com/seemoo-lab/nexmon).

---

## FAQ
N/A

## Changelog
- 12/06/2024
  - Universal support for both IEEE 802.11ac VHT and 802.11ax HE beamforming report extraction.

## Citation
If you use WiPiCap in your work, please consider citing the following paper:
```
@ARTICLE{cbrace,
  title   = "{CBR-ACE}: Counting Human Exercise using {Wi-Fi} Beamforming
             Reports",
  author  = "Sorachi Kato and Tomoki Murakami and Takuya Fujihashi and
             Takashi Watanabe and Shunsuke Saruwatari",
  journal = "Journal of Information Processing",
  volume  =  30,
  pages   = "66--74",
  year    =  2022
}
```

# Who cites our works
1. C. Wu, X. Huang, J. Huang, and G. Xing, “Enabling ubiquitous WiFi sensing with beamforming reports,” in Proceedings of the ACM SIGCOMM 2023 Conference, New York NY USA, 2023.
2. E. Yi et al., “BFMSense: WiFi Sensing Using Beamforming Feedback Matrix,” NSDI, pp. 1697–1712, 2024.
3. E. Yi, F. Zhang, J. Xiong, K. Niu, Z. Yao, and D. Zhang, “Enabling WiFi sensing on new-generation WiFi cards,” Proc. ACM Interact. Mob. Wearable Ubiquitous Technol., vol. 7, no. 4, pp. 1–26, Dec. 2023.
4. A. Liu, Y.-T. Lin, and K. Sundaresan, “View-agnostic human exercise cataloging with single MmWave radar,” Proc. ACM Interact. Mob. Wearable Ubiquitous Technol., vol. 8, no. 3, pp. 1–23, Aug. 2024.
5. R. Xiao, X. Chen, Y. He, J. Han, and J. Han, “Lend me your beam: Privacy implications of plaintext beamforming feedback in WiFi,” Netw Distrib Syst Secur Symp, 2025.

# Author
S. Kato

Graduate School of Information Science and Technology, Osaka University
<img src="https://upload.wikimedia.org/wikipedia/commons/1/15/%E5%A4%A7%E9%98%AA%E5%A4%A7%E5%AD%A6.svg" height="90">
