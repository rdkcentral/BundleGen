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
import tarfile
import shutil
from bundlegen.core.utils import Utils
from loguru import logger
if os.path.exists("L2_test_results.txt"):
    os.remove("L2_test_results.txt")
platform = ['raspberrypi3','raspberrypi4','qemux']
parse = argparse.ArgumentParser()
parse.add_argument("-t")
parse.add_argument("-a")
parse.add_argument("-m")
args = parse.parse_args()
if args.t:
    platform_template = args.t
else:
    platform_template = "rpi3_reference_vc4_dunfell"
oci_images_list = os.listdir("oci_images")
if (len(oci_images_list)) == 0:
    logger.error("No oci_image was present inside oci_images folder")
    sys.exit(1)
result = open("L2_test_results.txt", "w")
result.close()
for i in oci_images_list:
    j = i.split("-")
    app = j[0]
    for k in j:
        if k in platform:
            platform_name = k
            logger.debug("platform name are [%s] " %platform_name)
            break
        elif k == "oci.tar":
            logger.error("File name should consists of platform name")
            sys.exit(1)
        else:
            if k!="dac":
                app = app+"-"+k
    appname = app
    if args.a:
        if args.a == appname:
           app_name = args.a
        else:
            continue
    else:
        app_name = appname
    os.chdir("oci_images")
    if os.path.isfile(i):
        file = tarfile.open(i)
        if os.path.isdir(''+app_name+'-oci'):
            shutil.rmtree(''+app_name+'-oci')
        file.extractall(''+app_name+'-oci')
        file.close()
    os.chdir("..")
    os.mkdir("bundlegen_images")
    os.chdir("../..")
    if os.path.isfile(''+app_name+'-bundle.tar.gz'):
        os.remove(''+app_name+'-bundle.tar.gz')
    if args.m and args.a:
        if args.m == app_name+"-appmetadata":
            if os.path.exists("unit_tests/L2_testing/"+args.m+".json"):
                return_value = os.system('bundlegen generate -y --platform '+platform_template+' --appmetadata ./unit_tests/L2_testing/'+args.m+'.json oci:./unit_tests/L2_testing/oci_images/'+app_name+'-oci:latest ./'+app_name+'-bundle')
            else:
                logger.error("Appmetadata File was not present")
                os.chdir("unit_tests/L2_testing")
                shutil.rmtree("bundlegen_images")
                sys.exit(1)
        else:
            logger.error("Metadata path was incorrect")
            logger.info("Metadata file should be saved as "+app_name+"-appmetadata")
            os.chdir("unit_tests/L2_testing")
            shutil.rmtree("bundlegen_images")
            sys.exit(1)
    else:
        return_value = os.system('bundlegen generate -y --platform '+platform_template+' oci:./unit_tests/L2_testing/oci_images/'+app_name+'-oci:latest ./'+app_name+'-bundle')
    if ( (return_value >> 8) != 0):
        os.chdir("unit_tests/L2_testing")
        shutil.rmtree("bundlegen_images")
        sys.exit(1)
    file = tarfile.open(''+app_name+'-bundle.tar.gz')
    os.chdir("unit_tests/L2_testing/bundlegen_images")
    file.extractall(''+app_name+'-bundle')
    file.close()
    if args.m:
        app_metadata_file = args.m
    else:
        os.chdir("..")
        os.chdir("oci_images")
        appname=str(app_name)
        # source OCI Image(tar image)
        oci_image= i
        src="oci_image_untar"
        #untaring OCI image and pasting in ./dac-image-wayland-egl-test directory
        oci_tar = tarfile.open(oci_image)
        oci_tar.extractall(src)
        oci_tar.close()
        dst="../metadatas"+"/"+appname+"-bundle"
        umoci_command = f'umoci unpack --rootless --image {src} {dst}'
        logger.debug(umoci_command)
        success = Utils().run_process(umoci_command)
        logger.debug(success)
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
    result = open("L2_test_results.txt", "a")
    result.write("APP_NAME : %s" %(app_name))
    result.write("  PLATFORM_NAME : %s\n" %(platform_template))
    result.write("TEST DETAILS")
    result.write("\n============")
    result.close()
    value = os.system('python test_bundle.py '+app_name +" "+platform_template)
    os.chdir("oci_images")
    shutil.rmtree(''+app_name+'-oci')
    os.chdir("..")
    shutil.rmtree("bundlegen_images")
    if  os.path.isdir('metadatas'):
        shutil.rmtree("metadatas")
    if ( (value >> 8) != 0):
       sys.exit(1)