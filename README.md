# WiPiCap
A script enabling Raspberry Pi to capture wireless packets.
Detailed explanation of script is in Wiki.

## picap.sh
This script apply Nexmon firmware patch (https://github.com/seemoo-lab/nexmon) which enables Raspberry Pi put an interface in monitor mode.

This script doesn't make any modification to original Nexmon software, so if you meet some kinds of errors, please check Nexmon official project page and deal with them.

## json2csi.py
This script extracts VHT Compressed Beamforming Report from packet data represented by JSON.
If you don't know how you can transcode pcap into json, please see https://www.wireshark.org/docs/man-pages/tshark.html.

This script parses JSON and reconstruct PHI/PSI angle values from raw hex data.
If you don't know what VHT Compressed Beamforming Report is, please see Wiki of this project.
