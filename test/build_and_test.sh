#!/bin/sh

# Copyright 2021 Liberty Global Service B.V.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

if [ "$#" -lt 2 ]; then
    echo "Usage for bundles generated with meta-dac-sdk:"
    echo "./build_and_test.sh RPI_IPADDRESS DAC-IMAGE.TAR"
    echo "Examples:"
    echo "./build_and_test.sh 192.168.1.100 dac-image-wayland-egl-test.tar"
    echo "./build_and_test.sh 192.168.1.100 dac-image-qt-test.tar"
    echo ""
    echo "Usage for existing OCI images:"
    echo "./build_and_test.sh 192.168.1.100 docker://us.icr.io/appcontainerstagingrdk/you.i:latest sample_app_metadata/youi_reference.json"
    echo "You might need to login first: skopeo login us.icr.io"
    echo ""
    exit
fi

BOXIP=$1
APPMETADATA=""
if [ ! -z "$3" ]; then
  APPMETADATA="--appmetadata $3"
fi

## normal, image or host
if [ -z "$MATCH_MODE" ]; then
  MATCH_MODE="normal"
fi

## targets: rpi3, 7218c
if [ -z "$TARGET" ]; then
  TARGET="rpi3"
fi

## target/host platform version, options: morty, dunfell
if [ -z "$TARGET_VERSION" ]; then
  TARGET_VERSION="morty"
fi
if [ "$TARGET_VERSION" == "morty" ]; then
  TARGET_VERSION=""
else
  TARGET_VERSION="_$TARGET_VERSION"
fi

if [[ $2 == docker://** ]]; then
  APP_NAME="testapp"
  echo "--> Generating runtime bundle..."
  rm -rf ./${TARGET}-${APP_NAME}
  ## you might need to login first like: skopeo login us.icr.io
  bundlegen -vvv generate -m ${MATCH_MODE} --searchpath templates --platform ${TARGET}_reference${TARGET_VERSION} $2 ${TARGET}-${APP_NAME} ${APPMETADATA}
else

  OCI_TAR=$2
  # get basename of OCI tar path and remove extension
  APP_NAME="${OCI_TAR##*/}"
  APP_NAME="${APP_NAME%.*}"

  if [ ! -f $OCI_TAR ]; then
    echo "File $OCI_TAR not found!"
    exit 1
  fi

  echo "--> Extracting OCI image..."
  rm -rf ./oci-${APP_NAME}
  mkdir ./oci-${APP_NAME}
  tar -xvf $OCI_TAR -C ./oci-${APP_NAME}

  echo "--> Generating runtime bundle..."
  rm -rf ./${TARGET}-${APP_NAME}
  bundlegen -vvv generate -m ${MATCH_MODE} --searchpath templates --platform ${TARGET}_reference${TARGET_VERSION} oci:./oci-${APP_NAME}:latest ${TARGET}-${APP_NAME}
fi

./test/testapp.sh $BOXIP ${TARGET}-${APP_NAME}.tar.gz
