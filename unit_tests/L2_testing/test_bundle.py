#!/usr/bin/env python3

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

import unittest
import os
import json
import sys
import re

from loguru import logger
from unit_tests.L2_testing import get_L2_test_results
from common import setup_sys_path, TestBase
setup_sys_path()

has_failures = []

netwrk_type_config = ""
netwrk_type= ""
path = ""
app_id = ""
arguments = "/usr/libexec/DobbyInit"
process_args = ""
process_env = ""
process_rlimits = ""
envvars = ""
envvars_1 = ""
resource_limits = ""
args=""
wayland_env= "westeros"
mounts=""
dev_list_platform = []
device_infor_1=""
linux_devices = []
linux_resource_dev_information = []


def load_json(file_path):
    # open JSON file and parse contents
    fh = open(file_path, "r")
    data = json.load(fh)
    fh.close()
    return data

class TestBundleData(TestBase):
    def setUp(self):
         logger.debug("Setup")
         get_L2_test_results.add_test_results.add_tests(self)

    def tearDown(self):
        logger.debug("tearDown")
        if hasattr(self._outcome, 'errors'):
            # Python 3.4 - 3.10  (These two methods have no side effects)
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            # Python 3.11+
            result = self._outcome.result
        ok = all(test != self for test, text in result.errors + result.failures)

        # Demo output:  (print short info immediately - not important)
        if ok:
            logger.debug('\nOK: %s' % (self.id(),))
            get_L2_test_results.add_test_results.test_passed(self)

        for typ, errors in (('ERROR', result.errors), ('FAIL', result.failures)):
            for test, text in errors:
                if test is self:
                    #  the full traceback is in the variable `text`
                    msg = [x for x in text.split('\n')[1:]
                           if not x.startswith(' ')][0]
                    logger.debug("\n\n%s: %s\n     %s" % (typ, self.id(), msg))
                    get_L2_test_results.add_test_results.test_failed(self, msg)

    @classmethod
    def tearDownClass(self):
        get_L2_test_results.add_test_results.end_results(self)

    def test_bundle(self):
        logger.debug("-->Verifying appmetadata path")
        path = "./bundlegen_images/"+sys.argv[1]+"-bundle/rootfs/usr/bin/"+sys.argv[1].replace("dac-image-","")
        status = os.stat(path)
        self.assertNotEqual(status.st_size,0)
        logger.debug("-->Successfully appmetadata path has verified")

    def test_config(self):
        logger.debug("-->Verifying config.json path")
        path = "bundlegen_images/"+sys.argv[1]+"-bundle/config.json"
        status = os.stat(path)
        self.assertNotEqual(status.st_size,0)
        logger.debug("-->Successfully config.json path was verified")

    def test_app_name(self):
        logger.debug("-->Retrieving appname from config.json")
        config_json_path = "bundlegen_images/"+sys.argv[1]+"-bundle/config.json"
        finalconfigdata = load_json(config_json_path)
        #iterating through all keys in finalconfigdata
        for k,v in finalconfigdata.items():
                if k == "process":
                    app_path=v['args'][1]
        #self.assertEqual(app_path,("/usr/bin/"+sys.argv[1]+"-test"))
        self.assertEqual(app_path,("/usr/bin/"+sys.argv[1].replace("dac-image-","")))
        logger.debug("-->Successfully App name was retrieved from config.json")

    def test_appmetadata(self):
        logger.debug("-->Validating values in config.json")
        #Passing the appmetadata.json(argv[1]= "wayland-egl") and platform config(argv[2]= "rpi3_reference") as an argument to input script command
        #We shall copy the app metadata in the same folder where we have this script test_bundle.py
        appmetadata_path = "metadatas/"+sys.argv[1]+"-appmetadata.json"
        config_json_path = "bundlegen_images/"+sys.argv[1]+"-bundle/config.json"
        platform_path = "../../templates/generic/"+sys.argv[2]+".json"
        appmetadata = load_json(appmetadata_path)
        platform_cfg = load_json(platform_path)
        finalconfigdata = load_json(config_json_path)

        #iterating through all keys in appmetadata.json
        for key,value in appmetadata.items():
            if key == "id":
                app_id = value
            if key == "network":
                netwrk_type = value['type']

        #iterating through all keys in platform_cfg.json
        for key,value in platform_cfg.items():
            if key == "dobby" :
                if value['dobbyInitPath'] is not None:
                    global arguments
                    arguments = value['dobbyInitPath']
            if key == "gpu":
                if value['devs'] is not None:
                    device_infor = value['devs']
                if value['envvar'] is not None:
                    envvars = value['envvar']
                if value['extraMounts'] is not None:
                    mounts = value
                if platform_cfg.get("wayland") is not None:
                    global wayland_env
                    wayland_env = value
            if key == "envvar":
                if value is not None:
                    envvars_1 = value
            if key == "resourceLimits":
                if value is not None:
                    resource_limits = value
            if key == "gpu":
                 device_infor_1 = value['devs']
                 for k in device_infor_1:
                    dev_list_platform.append(k)
        #iterating through all keys in finalconfigdata i.e config.json
        for k,v in finalconfigdata.items():
            if k == "rdkPlugins":
                netwrk_type_config=v['networking']['data']['type']
                path = v['logging']['data']['fileOptions']['path']
            if k == "process":
                process_args = v['args']
                process_env = v['env']
                process_rlimits = v['rlimits']
            if k == "linux":
                 linux_info = v['devices']
                 linux_resource_dev_info = v['resources']['devices']
                 for key in linux_info:
                    linux_devices.append(key)

                 for key in linux_resource_dev_info:
                    linux_resource_dev_information.append(key)
        #Validating the appmetadata,platform cfg in config.json
        #Check for the app metadata,.platform config fields in config.json
        self.assertEqual(netwrk_type_config,netwrk_type)
        #Finding app_id if its subset of rdkPlugins.logging.data.fileOptions.path(present in config.json)
        self.assertNotEqual(path.find(app_id),-1)

        flag = 0
        if(set(envvars_1).issubset(set(process_env)) and set(envvars).issubset(set(process_env))):
            flag = 1
        self.assertEqual(flag,1)

        flag = 0
        #converting to hashable datatype,dict to string
        resource_limits_string= json.dumps(resource_limits)
        process_rlimits_string= json.dumps(process_rlimits)
        if(set(resource_limits_string).issubset(set(process_rlimits_string))):
            flag = 1
        self.assertEqual(flag,1)
        if(set(arguments).issubset(set(process_args))):
            flag = 1
        self.assertEqual(flag,1)

        # Devs list is appended at the end of the config.json linux.resource.dev and linux.devices,
        # hence reversing and checking the value of config.json against the linux.devices/linux.resources.devices for that number of nodes
        linux_resource_dev_information.reverse()
        dev_list_platform.reverse()
        linux_devices.reverse()

        for f, b in zip(linux_devices, dev_list_platform):

                # Shall iterate till the required length
                if f == (len(f)-1) :
                    break

                self.assertEqual(f.get('path'),b.get('path'))

                self.assertEqual(f.get('type'),b.get('type'))

                self.assertEqual(f.get('major'),b.get('major'))

                self.assertEqual(f.get('minor'),b.get('minor'))

        for f, b in zip(linux_resource_dev_information, dev_list_platform):

            # Shall iterate till the required length
            if f == (len(f)-1) :
                break

            self.assertEqual(f.get('allow'),True)

            self.assertEqual(f.get('access'),b.get('access'))

            self.assertEqual(f.get('type'),b.get('type'))

            self.assertEqual(f.get('major'),b.get('major'))

            self.assertEqual(f.get('minor'),b.get('minor'))

        logger.debug("-->All values in config.json are validated")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'])