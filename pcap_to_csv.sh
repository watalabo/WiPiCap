filename=`basename $1 .pcap`
tshark -r $1 -Y 'wlan.fc.type_subtype == 0x000e' -T fields -e frame.time -e wlan.ta -e wlan.vht.mimo_control.ncindex -e wlan.vht.mimo_control.nrindex -e wlan.vht.compressed_beamforming_report -e wlan.vht.mimo_control.codebookinfo -e wlan.vht.mimo_control.chanwidth -E header=y -E separator=, -E quote=d > $filename.csv
