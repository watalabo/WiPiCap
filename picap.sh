sudo su
apt update && apt upgrade
apt install raspberrypi-kernel-headers git libgmp3-dev gawk qpdf bison flex make libtool-bin automake texinfo
git clone https://github.com/seemoo-lab/nexmon.git
cd nexmon
cd buildtools/isl-0.10
autoreconf -f -i
./configure
make
make install
ln -s /usr/local/lib/libisl.so /usr/lib/arm-linux-gnueabihf/libisl.so.10
cd ../../
cd buildtools/mpfr-3.1.4
autoreconf -f -i
./configure
make
make install
ln -s /usr/local/lib/libmpfr.so /usr/lib/arm-linux-gnueabihf/libmpfr.so.4
cd ../../
source setup_env.sh
make
cd patches/bcm43455c0/7_45_189/nexmon/
make
make backup-firmware
make install-firmware

