# If not stated otherwise in this file or this component's license file the
# following copyright and licenses apply:
#
# Copyright 2021 RDK Management
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

import os
import sys
import argparse
import glob
import tarfile
import shutil
from bundlegen.core.utils import Utils
from loguru import logger
parse = argparse.ArgumentParser()
parse.add_argument("-a")
parse.add_argument("-p")
args = parse.parse_args()
if args.a and args.p:
    os.chdir("oci_images")
    if os.path.isfile(''+args.a+'-oci.tar'):
        file = tarfile.open(''+args.a+'-oci.tar')
        if os.path.isdir(''+args.a+'-oci'):
            shutil.rmtree(''+args.a+'-oci')
        file.extractall(''+args.a+'-oci')
        file.close()
    else:
        logger.error('Oci Image for '+args.a+' App is not present inside oci_images folder')
        sys.exit(1)
    os.chdir("..")
    os.mkdir("bundlegen_images")
    os.chdir("../..")
    if os.path.isfile(''+args.a+'-bundle.tar.gz'):
        os.remove(''+args.a+'-bundle.tar.gz')
    return_value = os.system('bundlegen generate -y --platform '+args.p+' oci:./unit_tests/L2_testing/oci_images/'+args.a+'-oci:latest ./'+args.a+'-bundle')
    if ( (return_value >> 8) != 0):
        os.chdir("unit_tests/L2_testing")
        shutil.rmtree("bundlegen_images")
        sys.exit(1)
    file = tarfile.open(''+args.a+'-bundle.tar.gz')
    os.chdir("unit_tests/L2_testing/bundlegen_images")
    file.extractall(''+args.a+'-bundle')
    file.close()
    os.chdir("..")
    oci_images_dir_path = os.chdir("oci_images")
    oci_images_path = os.getcwd()
    appname=str(args.a)
    # source OCI Image(tar image)
    oci_image=appname+"-oci."+"tar"
    src="oci_image_untar"
    #untaring OCI image and pasting in ./dac-image-wayland-egl-test directory
    oci_tar = tarfile.open(oci_image)
    oci_tar.extractall(src)
    oci_tar.close()
    dst="../metadatas"+"/"+appname+"-bundle"
    umoci_command = f'umoci unpack --rootless --image {src} {dst}'
    logger.debug(umoci_command)
    success = Utils().run_process(umoci_command)
    if(os.path.isdir(src)):
        shutil.rmtree(src)
    os.chdir("../metadatas")
    app_metadata_file_path=appname+"-bundle"+"/"+"rootfs"+"/"+"appmetadata.json"
    app_metadata_file= appname+"-appmetadata.json"
    if(os.path.isfile(app_metadata_file)):
        os.remove(app_metadata_file)
        logger.debug("Old [%s] file deleted successfully" %app_metadata_file)
    shutil.copy(app_metadata_file_path, ".")
    if(os.path.isdir(appname+"-bundle")):
        shutil.rmtree(appname+"-bundle")
    os.rename('appmetadata.json', app_metadata_file)
    if(os.path.isfile(app_metadata_file)):
        logger.debug("App Metadata extracted from Oci Image successfully...")
    os.chdir("..")
    return_value = os.system('python test_bundle.py '+args.a +" "+args.p)
    os.chdir("oci_images")
    shutil.rmtree(''+args.a+'-oci')
    os.chdir("..")
    shutil.rmtree("bundlegen_images")
    shutil.rmtree("metadatas")
    if ( (return_value >> 8) != 0):
       sys.exit(1)
else:
    logger.error("\n usage: run_L2_test.py [-h] [-a App_Name] [-p Platform_Name] \n")
    sys.exit(1)