#!/bin/sh

##############################################################################
# Copyright © 2021 Liberty Global B.V. and its Licensors.
# All rights reserved.
# Licensed by RDK Management, LLC under the terms of the RDK license.
# ============================================================================
# Liberty Global B.V. CONFIDENTIAL AND PROPRIETARY
# ============================================================================
# This file (and its contents) are the intellectual property of Liberty Global B.V.
# It may not be used, copied, distributed or otherwise disclosed in whole or in
# part without the express written permission of Liberty Global B.V.
# The RDK License agreement constitutes express written consent by Liberty Global.
# ============================================================================
# This software is the confidential and proprietary information of Liberty Global B.V.
# ("Confidential Information"). You shall not disclose this source code or
# such Confidential Information and shall use it only in accordance with the
# terms of the license agreement you entered into.
#
# LIBERTY GLOBAL B.V. MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE
# SUITABILITY OF THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE, OR NON-INFRINGEMENT. LIBERTY GLOBAL B.V. SHALL NOT BE LIABLE FOR
# ANY DAMAGES SUFFERED BY LICENSEE NOR SHALL THEY BE RESPONSIBLE AS A RESULT
# OF USING, MODIFYING OR DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
##############################################################################

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
