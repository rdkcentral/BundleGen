#!/bin/sh

if [ "$#" -ne 2 ]; then
    echo "Usage:"
    echo "./build_and_test_on_rpi.sh RPI_IPADDRESS DAC-IMAGE.TAR"
    echo "For example:"
    echo "./build_and_test_on_rpi.sh 192.168.1.100 dac-image-wayland-egl-test.tar"
    echo "./build_and_test_on_rpi.sh 192.168.1.100 dac-image-qt-test.tar"
    echo "These DAC tarballs can be created using https://github.com/stagingrdkm/meta-dac-sdk"
    exit
fi

BOXIP=$1
OCI_TAR=$2
APP_NAME="${OCI_TAR%.*}"

if [ ! -f $OCI_TAR ]; then
  echo "File $OCI_TAR not found!"
  exit 1
fi

echo "--> Extracting OCI image..."
rm -rf ./oci-${APP_NAME}
mkdir ./oci-${APP_NAME}
tar -xvf $OCI_TAR -C ./oci-${APP_NAME}

echo "--> Generating runtime bundle..."
rm -rf ./rpi-${APP_NAME}
bundlegen -vvv generate --searchpath templates --platform rpi3_reference -m image oci:./oci-${APP_NAME}:latest rpi-${APP_NAME}

./test/testapp.sh $BOXIP rpi-${APP_NAME}.tar.gz
