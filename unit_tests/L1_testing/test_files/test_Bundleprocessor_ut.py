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
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unit_tests.L1_testing import get_L1_test_results
from bundlegen.core.bundle_processor import BundleProcessor
from loguru import logger
#This class will test the functionality of API's in bundleprocessor.py file.
class TestBundleProcessor(unittest.TestCase):
    def setUp(self):
         logger.debug("Setup")
         get_L1_test_results.add_test_results.add_tests(self)

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
            get_L1_test_results.add_test_results.test_passed(self)

        for typ, errors in (('ERROR', result.errors), ('FAIL', result.failures)):
            for test, text in errors:
                if test is self:
                    #  the full traceback is in the variable `text`
                    msg = [x for x in text.split('\n')[1:]
                           if not x.startswith(' ')][0]
                    logger.debug("\n\n%s: %s\n     %s" % (typ, self.id(), msg))
                    get_L1_test_results.add_test_results.test_failed(self, msg)

    @classmethod
    def tearDownClass(self):
        get_L1_test_results.add_test_results.end_results(self)

    def test_process_oci_version(self):
    #When generate_compliant_config: True then it will parse the value of ociversion as 1.0.2
        logger.debug("-->It will parse oci_version as 1.0.2")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "dobby":{
            "generateCompliantConfig": True
            }
        }
        processor.oci_config = {
        }
        processor._should_generate_compliant_config()
        processor._process_oci_version()
        expected = {
            "ociVersion": "1.0.2"
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_oci_version_generate_false(self):
    #When generate_compliant_config: False then it will parse the value of ociversion as 1.0.2-dobby
        logger.debug("-->It will parse oci_version as 1.0.2-dobby")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "dobby":{
            "generateCompliantConfig": False
            }
        }
        processor.oci_config = {
        }
        processor._should_generate_compliant_config()
        processor._process_oci_version()
        expected = {
            "ociVersion": "1.0.2-dobby"
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_check_compatibility(self):
        #It will checks the api of check_compatibility, here if graphics in app_metadata and graphics in hardware of platform_cfg are true then only it will satisfy.
        logger.debug("-->Graphics value should be true in both appmetadata and platformcfg")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": True,
            "features": []
        }
        processor.platform_cfg= {
            "hardware": {
                "graphics": True,
            },
            "rdk": {
                "supportedFeatures": [
                ]
            }
        }
        actual=processor.check_compatibility()
        expected=True
        self.assertEqual(actual, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_resources(self):
        logger.debug("-->Parsing first value for devices inside resources of linux")
        #print("Parsing the value for devices inside resources")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "hardware": {
                "graphics": True,
            }
        }
        processor.oci_config = {
            "linux" : {
            "resources" : {
            }
            }
        }
        processor._process_resources()
        expected = {
            'linux': {
            'resources': {'devices': [
                {"allow": False,
                    "access": "rwm"}
                    ]
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_logging(self):
    #Assigning value "logging":{"mode": "file"}
        logger.debug("-->Parsing values inside logging plugin based on the value of mode:file")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "id": "com.rdk.wayland-egl-test"
        }
        processor.platform_cfg = {
            "logging":{
                "mode": "file",
                "logDir": "/var/log"
            }
        }
        processor.oci_config={
            "process": {
                "terminal": True
                },
            "annotations":
            {},
            "rdkPlugins":
            {
            }
        }
        processor._process_logging()
        expected={
            'process': {'terminal': True},
            'annotations': {'run.oci.hooks.stderr': '/dev/stderr',
                  'run.oci.hooks.stdout': '/dev/stdout'},
            'rdkPlugins': {'logging':
                        {'data':
                            {'fileOptions':
                                {'path': '/var/log/com.rdk.wayland-egl-test.log'},
                            'sink': 'file'},
                        'required': True}
                            }
                        }

        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_logging1(self):
    #Assigning value "logging":{"mode": ""journald""}
        logger.debug("-->Parsing values inside logging plugin based on the value of mode:journald")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "id": "com.rdk.wayland-egl-test"
        }
        processor.platform_cfg = {
            "logging":{
                "mode": "journald",
                 }
        }
        processor.oci_config={
            "process": {
                "terminal": True
                },
            "rdkPlugins":
            {
            }
        }
        processor._process_logging()
        expected={
            'process': {'terminal': True},
            'rdkPlugins': {'logging':
                        {"required": True,
                            "data": {
                            "sink": "journald"
                            }
                        }
                    }
                }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_process(self):
        #Parsing dobbyinitpath and appending ennvar values from platform_cfg to env, limit values platform_cfg to rlimits
        logger.debug("-->Parsing dobbyinitpath, ennvar and limit values")
        logger
        #print("Parsing values to process")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
             "envvar": [
                "XDG_RUNTIME_DIR=/tmp"
            ],
            "resourceLimits": [
            {
            "type": "RLIMIT_NPROC",
            "hard": 300,
            "soft": 300
            }
        ]
        }
        processor.oci_config = {
            "process":{
                "args":[
                ],
                "env":[],
                "rlimits": []
            },
            "mounts":[]
        }
        processor._process_process()
        expected={
            'process': {'args': ['/usr/libexec/DobbyInit'],
            "env":[
                "XDG_RUNTIME_DIR=/tmp"
            ],
            "rlimits": [
            {
            "type": "RLIMIT_NPROC",
            "hard": 300,
            "soft": 300
            }
            ]
            },
            'mounts': [
            {'destination': '/usr/libexec/DobbyInit',
            'options': ['rbind', 'nosuid', 'nodev', 'ro'],
            'source': '/usr/libexec/DobbyInit',
            'type': 'bind'
                }
            ]
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_hostname(self):
    #hostname mentioned in platform_cfg
        logger.debug("-->Parsing the hostname from platform_cfg")
        #print("Parsing the hostname which was mentioned in platform_cfg")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "id": "com.rdk.wayland-egl-test"
        }
        processor.platform_cfg = {
          "hostname": "umoci"
        }
        processor.oci_config = {
            "hostname": "umoci-default"
        }
        processor._process_hostname()
        expected={
            "hostname": "umoci"
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_gpu(self):
    #Assigning graphics in appmetadata to False then it will not parse any gpu values
        logger.debug("-->It will not parse any gpu values")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": False
        }
        processor.platform_cfg = {
        }
        processor.oci_config = {
        }
        processor._process_gpu()
        expected={
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_gpu_graphics_true(self):
    #Assigning graphics in appmetadata to True
    #Add mounts,envvar,devices
        logger.debug("-->It will parse all gpu values from platform_cfg")
        #print("Parsing values to gpu when value of graphics in appmetadata was True")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": True
        }
        processor.platform_cfg = {
            "hardware": {
            "graphics": True,
            },
            "gpu":{
            "extraMounts":[ ],
            "envvar":[ ],
            "gfxLibs":[ ],
            "devs":[ ]
            }
        }
        processor.oci_config = {
            "process":{
                "env":[ ]
            },
            "linux":{
                "devices":[ ]
            }
        }
        processor._process_gpu()
        expected={
            "process": {
            "env": ["WAYLAND_DISPLAY=westeros"]
            },
            "linux": {'devices': [], 'resources': {'devices': []}
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_mounts(self):
        logger.debug("-->Parsing all values of mounts from app_metadata")
        #print("Parsing the values to mounts")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "mounts": [
            {
            "destination": "/data",
            "type": "none",
            "source": "/volumes/testing",
            "options": [
                "rbind",
                "rw"
                    ]
                }
            ]
        }
        processor.platform_cfg = {

        }
        processor.oci_config = {
            "mounts":[]
        }
        processor._process_mounts()
        expected = {
            "mounts": [
            {
            "destination": "/data",
            "type": "none",
            "source": "/volumes/testing",
            "options": [
                "rbind",
                "rw"
                    ]
                }
            ]
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_mounts1(self):
        logger.debug("-->Parsing all values of mounts from app_metadata")
        #print("Parsing the values to mounts")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
        }
        processor.platform_cfg = {
         "mounts": [
            {
            "destination": "/data",
            "type": "none",
            "source": "/volumes/testing",
            "options": [
                "rbind",
                "rw"
                    ]
                }
            ]
        }
        processor.oci_config = {
            "mounts":[]
        }
        processor._process_mounts()
        expected = {
            "mounts": [
            {
            "destination": "/data",
            "type": "none",
            "source": "/volumes/testing",
            "options": [
                "rbind",
                "rw"
                    ]
                }
            ]
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_network(self):
        #Parsing all values to rdk_plugins from app_metadata which values were defined in network
        logger.debug("-->Parsing all values of network to rdkPlugins")
        processor = BundleProcessor()
        processor.rootfs_path = "/tmp/test"
        processor.createmountpoints = None
        processor.app_metadata = {
            "network": {
                "dnsmasq": "true",
            }
        }
        processor.oci_config = {
            "rdkPlugins": {}
        }
        processor._process_network()
        expected_result = {
            'rdkPlugins': {
                'networking': {
                    'required': True,
                    'data': {
                        "dnsmasq": "true",
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config,expected_result)
        logger.debug("-->Test was Successfully verified")

    def test_process_users_and_groups(self):
        logger.debug("-->It will add uidMappings and gidMappings")
        #print("It will add uidMappings and gidMappings")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.bundle_path = {
        }
        processor.createmountpoints = None
        processor.app_metadata = {
        }
        processor.platform_cfg = {
         }
        processor.oci_config = {
            "linux":{
                "uidmappings":[],
                "gidmappings":[]
            }
        }
        processor._process_users_and_groups()
        expected={
            "linux":{
                "uidMappings":[],
                "uidmappings":[],
                "gidMappings":[],
                "gidmappings":[],
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_root(self):
        logger.debug("-->Parsing all values of root to oci_config")
        #print("Parsing the values of root from platform_cfg")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "id": "com.rdk.netflix"
        }
        processor.platform_cfg = {
            "root": {
                "path": "rootfs_dobby",
                "readonly": True
            }
        }
        processor.oci_config = {
            "root":{
            }
        }
        processor._process_root()
        expected={
            "root": {
                "path": "rootfs_dobby",
                "readonly": True
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_storage(self):
    #if storage_settings are not present
        logger.debug("-->It will create mounts")
        #print("If storage_settings are not present")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
        }
        processor.oci_config = {
            "mounts":[]
        }
        processor._process_storage()
        expected = {
            "mounts":[]
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_add_annotation(self):
        logger.debug("-->Parsing annotation values to oci_config")
        #print("Parsing the values to annotations")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.oci_config = {
            "annotations": {
            }
        }
        processor._add_annotation("org.opencontainers.image.architecture", "arm")
        expected = {
            "annotations":{
                "org.opencontainers.image.architecture":"arm"
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_add_rdk_plugins(self):
    #If platform_cfg has plugindir inside the dobby then rdk_plugins dict was created inside oci_config
        logger.debug("-->Creates rdk_plugins inside oci_config")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "dobby" : {
                "pluginDir" : []
            }
        }
        processor.oci_config = {
        }
        processor._add_rdk_plugins()
        expected = {
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_add_bind_mount(self):
        logger.debug("-->Parsing values to mounts by passing source and destination paths")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.oci_config = {
            "mounts" : []
        }
        processor._add_bind_mount("/usr/share/X11/xkb","/usr/share/X11/xkb")
        expected = {
            "mounts" : [
                {
            "source": "/usr/share/X11/xkb",
            "destination": "/usr/share/X11/xkb",
            "type": "bind",
            "options": [
                "rbind",
                "nosuid",
                "nodev",
                "ro",
                ]
            }
            ]
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_should_generate_compliant_config(self):
        logger.debug("-->Assigning generateCompliantConfig to true")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "dobby": {
            "generateCompliantConfig": True
            }
        }
        actual = processor._should_generate_compliant_config()
        expected = True
        self.assertEqual(actual, expected)
        logger.debug("-->Test was Successfully verified")

    def test_should_generate_compliant_config_false(self):
        logger.debug("-->Assigning generateCompliantConfig to false")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "dobby": {
                "generateCompliantConfig": False
            }
        }
        actual = processor._should_generate_compliant_config()
        expected = False
        self.assertEqual(actual, expected)
        logger.debug("-->Test was Successfully verified")

    def test_is_mapped_1(self):
        logger.debug("-->Assigning value of id to None")
        processor = BundleProcessor()
        actual = processor._is_mapped(None,0)
        expected = True
        self.assertEqual(actual, expected)
        logger.debug("-->Test was Successfully verified")

    def test_is_mapped_2(self):
        logger.debug("-->Assigning value of mappings to None")
        processor = BundleProcessor()
        actual = processor._is_mapped(0,None)
        expected = False
        self.assertEqual(actual, expected)
        logger.debug("-->Test was Successfully verified")


if __name__ == "__main__":
    unittest.main()
