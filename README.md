# WiPiCap
A script enabling Raspberry Pi to capture wireless packets.

## picap.sh
This script apply Nexmon firmware patch (https://github.com/seemoo-lab/nexmon) which enables Raspberry Pi put an interface in monitor mode.
This script doesn't make any modification to original Nexmon software, so if you meet some kinds of errors, please check Nexmon official project page and deal with them.

## json2csi.py
This script extract VHT Compressed Beamforming Report from packet data represented by JSON.
This script recognize $N_c$
