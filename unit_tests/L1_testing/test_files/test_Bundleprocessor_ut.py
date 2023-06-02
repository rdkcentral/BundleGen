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
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from get_L1_test_results import add_test_results
from bundlegen.core.bundle_processor import BundleProcessor
from bundlegen.core.library_matching import LibraryMatching
from loguru import logger

#This class will test the functionality of API's in bundleprocessor.py file.
class TestBundleProcessor(unittest.TestCase):
    def setUp(self):
         logger.debug("Setup")
         add_test_results.add_tests(self)

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
            add_test_results.test_passed(self)

        for typ, errors in (('ERROR', result.errors), ('FAIL', result.failures)):
            for test, text in errors:
                if test is self:
                    #  the full traceback is in the variable `text`
                    msg = [x for x in text.split('\n')[1:]
                           if not x.startswith(' ')][0]
                    logger.debug("\n\n%s: %s\n     %s" % (typ, self.id(), msg))
                    add_test_results.test_failed(self, msg)

    @classmethod
    def tearDownClass(self):
        add_test_results.end_results(self)

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

    def test_process_logging1(self):
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
            'rdkPlugins': {
                'logging': {
                    'required': True,
                    'data': {
                        'sink': 'file',
                        'fileOptions':
                        {
                        'path': '/var/log/com.rdk.wayland-egl-test.log',
                        },
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_logging_journald1(self):
    #Assigning value "logging":{"mode": ""journald""}
        logger.debug("-->Parsing values inside logging plugin based on the value of mode:journald")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
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
            "process": {'terminal': True},
            "rdkPlugins": {
                "logging": {
                    "required": True,
                        "data": {
                        "sink": "journald",
                            }
                        }
                    }
                }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_process(self):
        #Parsing dobbyinitpath and appending ennvar values from platform_cfg to env, limit values platform_cfg to rlimits
        logger.debug("-->Parsing dobbyinitpath, ennvar and limit values")
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
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "id": "com.rdk.netflix",
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
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "id": "com.rdk.netflix"
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

#Adding new plugins
    def test_process_logging2(self):
        #Assigning value "logging":{"mode": "file"} and giving limit inside loggin plugin
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
                "logDir": "/var/log",
                "limit": 65536
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
            'rdkPlugins': {
                'logging': {
                    'required': True,
                    'data': {
                        'sink': 'file',
                        'fileOptions':
                        {
                        'path': '/var/log/com.rdk.wayland-egl-test.log',
                        'limit': 65536
                        },
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_logging_devnull(self):
    #Assigning value "logging":{"mode": ""devnull""}
        logger.debug("-->Parsing values inside logging plugin based on the value of mode:devnull")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
        }
        processor.platform_cfg = {
            "logging":{
                "mode": "devnull",
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
        expected= {
            "process": {
                "terminal": True
                },
            'rdkPlugins': {'logging':
                        {"required": True,
                            "data": {
                            "sink": "devnull"
                            }
                        }
                    }
                }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_logging_journald2(self):
    #Assigning value "logging":{"mode": ""journald""} along with journaldOptions
        logger.debug("-->Parsing values inside logging plugin based on the value of mode:journald")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
        }
        processor.platform_cfg = {
            "logging":{
                "mode": "journald",
                "journaldOptions": {
                    "priority": "LOG_INFO"
                        }
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
        expected = {
            "process": {
                "terminal": True
                },
            "rdkPlugins": {
                "logging": {
                    "required": True,
                        "data": {
                        "sink": "journald",
                            "journaldOptions": {
                                "priority": "LOG_INFO"
                            }
                        }
                    }
                }
             }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_thunder1(self):
        #Adding thunder plugin inside appmetadata
        logger.debug("-->Mentioning thunder in appmetadata")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "thunder": {
                "bearerUrl": "http://localhost",
                "trusted": True,
                "connLimit": 32
            }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_thunder()
        expected={
        "rdkPlugins":
            {
                "thunder": {
                    "required": True,
                    "dependsOn": ["networking"],
                    "data": {"bearerUrl": "http://localhost",
                        "trusted": True,
                        "connLimit": 32
                        }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_thunder2(self):
        #Adding thunder plugin inside appmetadata
        logger.debug("-->Not Mentioning thunder in appmetadata")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_thunder()
        expected={
        "rdkPlugins":
            {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_gpu_plugin1(self):
        #Adding gpu plugin
        logger.debug("-->Mentioning GPU in appmetadata")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "resources": {
                "gpu": "128M"
            }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_gpu_plugin()
        expected={
            "rdkPlugins": {
                "gpu": {
                    "required": True,
                    "data": {
                        "memory": 134217728
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_gpu_plugin2(self):
        #Adding gpu plugin
        logger.debug("-->Not Mentioning GPU in appmetadata")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "resources":{ }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_gpu_plugin()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_ipc1(self):
        #Adding ipc plugin
        #Assigning enable : True and Assigining values in platform_cfg
        logger.debug("-->Mentioning ipc in both appmetadata and platform_cfg")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "ipc": {
                "enable": True
            }
        }
        processor.platform_cfg = {
            "ipc": {
                "session": "/path/to/dbus/session",
                "system": "/var/run/dbus/system_bus_socket",
                "debug": "<path/to/dbus>"
            }
        }
        processor.oci_config={
            "rdkPlugins":
            {
            }
        }
        processor._process_ipc()
        expected={
            "rdkPlugins": {
                "ipc": {
                    "required": True,
                    "data":{
                        "session": "/path/to/dbus/session",
                        "system": "/var/run/dbus/system_bus_socket",
                        "debug": "<path/to/dbus>"
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_ipc2(self):
        #Adding ipc plugin
        #Assigning enable : True
        logger.debug("-->Mentioning ipc, only in appmetadata by giving value of enable as true")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "ipc": {
                "enable": True
            }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            {
            }
        }
        processor._process_ipc()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_ipc3(self):
        #Assigning enable : False and Assigining values in platform_cfg
        logger.debug("-->Mentioning ipc in both appmetadata and platform_cfg, giving value of enable as false")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "ipc": {
                "enable": False
            }
        }
        processor.platform_cfg = {
            "ipc": {
                "session": "<path to dbus session>",
                "system": "<system>",
                "debug": "<path to debug dbus session>"
            }
        }
        processor.oci_config={
            "rdkPlugins":
            {
            }
        }
        processor._process_ipc()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_ipc4(self):
        #Assigning enable : False and Assigining values in platform_cfg
        logger.debug("-->Mentioning ipc, only in appmetadata by giving value of enable as false")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "ipc": {
                "enable": False
            }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            {
            }
        }
        processor._process_ipc()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_ipc5(self):
        #Assigning enable : False and Assigining values in platform_cfg
        logger.debug("-->Not mentioning ipc in both appmetadata and platform_cfg")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            {
            }
        }
        processor._process_ipc()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_minidump1(self):
        #Adding minidump
        #Assigning enable : True and Assigining values in platform_cfg
        logger.debug("-->Mentioning minidump in both appmetadata and platform_cfg")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "minidump": {
              "enable": True
            }
        }
        processor.platform_cfg = {
            "minidump": {
                "destinationPath": "/opt/minidumps"
            }
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_minidump()
        expected={
            "rdkPlugins": {
                "minidump": {
                    "required": True,
                    "data": {
                        "destinationPath": "/opt/minidumps"
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_minidump2(self):
        #Adding minidump
        #Assigning enable : True
        logger.debug("-->Mentioning minidump, only in appmetadata by giving value of enable as true")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "minidump": {
              "enable": True
            }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_minidump()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_minidump3(self):
        #Assigning enable : False and Assigining values in platform_cfg
        logger.debug("-->Mentioning minidump in both appmetadata and platform_cfg, giving value of enable as false")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "minidump": {
              "enable": False
            }
        }
        processor.platform_cfg = {
            "minidump": {
                "destinationPath": "/opt/minidumps"
            }
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_minidump()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_minidump4(self):
        #Assigning enable : False
        logger.debug("-->Mentioning minidump, only in appmetadata by giving value of enable as false")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "minidump": {
              "enable": False
            }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_minidump()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_minidump5(self):
        #Assigning enable : False and Assigining values in platform_cfg
        logger.debug("-->Not mentioning minidump in both appmetadata and platform_cfg")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            {
            }
        }
        processor._process_minidump()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_oomcrash1(self):
        #Adding oomcrash
        #Assigning enable : True and Assigining values in platform_cfg
        logger.debug("-->Mentioning oomcrash in both appmetadata and platform_cfg")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "oomcrash": {
                "enable": True
            }
        }
        processor.platform_cfg = {
            "oomcrash": {
                "path": "/opt/dobby_container_crashes"
            }
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_oomcrash()
        expected={
            "rdkPlugins": {
                "oomcrash": {
                    "required": True,
                    "data": {
                    "path": "/opt/dobby_container_crashes"
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_oomcrash2(self):
        #Adding oomcrash
        #Assigning enable : True
        logger.debug("-->Mentioning oomcrash, only in appmetadata by giving value of enable as true")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "oomcrash": {
                "enable": True
            }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_oomcrash()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_oomcrash3(self):
        #Assigning enable : False and Assigining values in platform_cfg
        logger.debug("-->Mentioning oomcrash in both appmetadata and platform_cfg, giving value of enable as false")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "oomcrash": {
                "enable": False
            }
        }
        processor.platform_cfg = {
            "oomcrash": {
                "path": "/opt/dobby_container_crashes"
            }
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_oomcrash()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_oomcrash4(self):
        #Assigning enable : False
        logger.debug("-->Mentioning oomcrash, only in appmetadata by giving value of enable as false")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
            "oomcrash": {
                "enable": False
            }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            { }
        }
        processor._process_oomcrash()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_process_oomcrash5(self):
        #Assigning enable : False and Assigining values in platform_cfg
        logger.debug("-->Not mentioning oomcrash in both appmetadata and platform_cfg")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata={
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            "rdkPlugins":
            {
            }
        }
        processor._process_oomcrash()
        expected={
            "rdkPlugins": {
            }
        }
        self.assertEqual(processor.oci_config, expected)
        logger.debug("-->Test was Successfully verified")

    def test_app_meta_data_schema(self):
        #this test is to check, jsonschema of app meta data is proper.
        #one more changes is been added chdir because test been running in folder
        #/BundleGen/unit_tests/L1_testing to validate schema changing the directory to /BundleGen
        logger.debug("--> checking the appmetadata schema")
        os.chdir('../../')
        validate = BundleProcessor()
        validate.app_metadata = {
            "id": "com.rdk.wayland-egl-test",
            "type": "application/vnd.rdk-app.dac.native",
            "version": "1.0.0",
            "description": "Simple wayland egl demo, showing green rectangle",
            "priority": "optional",
            "graphics": True,
            "network": {
             "type": "open"
            },
            "storage": {},
            "resources": {
             "ram": "128M"
            }
        }
        actual = validate.validate_app_metadata_config()
        expected = True
        os.chdir('unit_tests/L1_testing')
        self.assertEqual(actual, expected)
        logger.debug("-->Test was Successfully verified")

    def test_remove_required_app_meta_data_schema(self):
        #this test is to validate required fields when are removed.
        logger.debug("--> checking the appmetadata schema by removing the required fields ")
        os.chdir('../../')
        validate = BundleProcessor()
        validate.app_metadata = {
            "id": "com.rdk.wayland-egl-test"
        }
        actual = validate.validate_app_metadata_config()
        expected = False
        os.chdir('unit_tests/L1_testing')
        self.assertEqual(actual, expected)
        logger.debug("-->Test was Successfully verified")

    def test_optional_field_app_meta_data_schema(self):
        #this test is to validate optional fields by removing required fields.
        logger.debug("--> Validating schema removing reqired fields and adding optional fields ")
        os.chdir('../../')
        validate = BundleProcessor()
        validate.app_metadata = {
            "priority": "optional",
            "thunder": {
                "bearerUrl": "http://localhost",
                "trusted": True,
                "connLimit": 32
            },
            "ipc": {
                "enable": True
            },
            "minidump": {
                "enable": True
            },
            "oomcrash": {
                "enable": True
            }
        }
        actual = validate.validate_app_metadata_config()
        expected = False
        os.chdir('unit_tests/L1_testing')
        self.assertEqual(actual, expected)
        logger.debug("-->Test was Successfully verified")

    def test_network_field_compatibility(self):
        logger.debug("-->checking Platform does support Network field output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": True,
            "network": {
                "type": "open",
                "dnsmasq": "true"
            }
        }
        processor.platform_cfg = {
            "hardware":{
                "graphics":True
                },
            "network": {
                "options": [
                    "nat",
                    "private"
                ]
            },
            "rdk": {
                "supportedFeatures": []
            }
        }
        actual = processor.check_compatibility()
        expected = False
        self.assertEqual(actual, expected)

    def test_graphic_field_compatibility(self):
        logger.debug("-->checking Platform does support graphics output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": True
        }
        processor.platform_cfg = {
            "hardware":{
            }
        }
        actual = processor.check_compatibility()
        expected = False
        self.assertEqual(actual, expected)

    def test_persistent_storage_field_compatibility(self):
        logger.debug("-->checking Platform does support persistent storage output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": False,
            "storage": {
                "persistent":[
                    {
                    "size": "62M",
                    "path": "/home/private"
                    }
                ]
            }
        }
        processor.platform_cfg = {
            "rdk":{
            },
            "storage":{
            }
        }
        actual = processor.check_compatibility()
        expected = False
        self.assertEqual(actual, expected)

    def test_storage_persistent_maxsize_field_compatibility(self):
        logger.debug("-->checking Platform does support maxsize output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": False,
            "storage": {
                "persistent":[
                    {
                    "size": "62M",
                    "path": "/home/private"
                    }
                ]
            }
        }
        processor.platform_cfg = {
            "rdk":{
            },
            "storage":{
                "persistent":{
                    "storageDir": "/opt/dac_apps/data/0/dac",
                    "maxSize": "60M"
                }
            }
        }
        actual = processor.check_compatibility()
        expected = False
        self.assertEqual(actual, expected)

    def test_storage_temp_maxsize_field_compatibility(self):
        logger.debug("-->checking Platform does support temp storage maxsize")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": False,
            "storage": {
                "persistent":[
                    {
                    "size": "12M",
                    "path": "/home/private"
                    }
                ],
                "temp":[
                    {
                    "size": "9M",
                    "path": "/home/private"
                    }
                ]
            }
        }
        processor.platform_cfg = {
            "rdk":{
            },
            "storage":{
                "persistent":{
                    "storageDir": "/opt/dac_apps/data/0/dac",
                    "maxSize": "20M"
                },
                "temp":{
                    "storageDir": "/opt/dac_apps/data/0/dac",
                    "maxSize": "5M"
                }
            }
        }
        actual = processor.check_compatibility()
        expected = False
        self.assertEqual(actual, expected)

    def test_storage_persistent_totalsize_field_compatibility(self):
        logger.debug("-->checking Platform does support storage persistent totalsize")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": False,
            "storage": {
                "persistent":[
                    {
                    "size": "12M",
                    "path": "/home/private"
                    }
                ]
            }
        }
        processor.platform_cfg = {
            "rdk":{
            },
            "storage":{
                "persistent":{
                    "storageDir": "/opt/dac_apps/data/0/dac",
                    "maxSize": "20M",
                    "maxTotalSize":"10"
                }
            }
        }
        actual = processor.check_compatibility()
        expected = False
        self.assertEqual(actual, expected)

    def test_storage_persistent_size_lesser_than_minsize_field_compatibility(self):
        logger.debug("-->Persistent storage requested by app is less than minimum required by platform")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": False,
            "storage": {
                "persistent":[
                    {
                    "size": "10M",
                    "path": "/home/private"
                    }
                ]
            }
        }
        processor.platform_cfg = {
            "rdk":{
            },
            "storage":{
                "persistent":{
                    "storageDir": "/opt/dac_apps/data/0/dac",
                    "maxSize": "20M",
                    "minSize":"15M",
                    "maxTotalSize":"10"
                }
            }
        }
        actual = processor.check_compatibility()
        expected = False
        self.assertEqual(actual, expected)

    def test_temp_storage_app_less_than_min_req_compatibility(self):
        logger.debug("-->Temporary storage requested by app is less than minimum required by platform ")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": False,
            "storage": {
                "temp":[
                    {
                    "size": "5M",
                    "path": "/home/private"
                    }
                ],
                "persistent":[{
                    "size": "5M",
                    "storageDir": "/opt/dac_apps/data/0/dac"
                }]
            }
        }
        processor.platform_cfg = {
            "rdk":{
            },
            "storage":{
                "temp":{
                    "maxSize": "15M",
                    "minSize":"7M",
                    "maxTotalSize":"10M"
                },
                "persistent":{
                    "storageDir": "/opt/dac_apps/data/0/dac",
                    "size": "1M"
                }
            }
        }
        actual = processor.check_compatibility()
        expected = True
        self.assertEqual(actual, expected)

    def test_storage_temp_totalsize_field_compatibility(self):
        logger.debug("-->checking Platform does support storage temp totalsize")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "graphics": False,
            "storage": {
                "temp":[
                    {
                    "size": "9M",
                    "path": "/home/private"
                    }
                ]
            }
        }
        processor.platform_cfg = {
            "rdk":{
            },
            "storage":{
                "temp":{
                    "maxSize": "15M",
                    "minSize":"7",
                    "maxTotalSize":"10"
                }
            }
        }
        actual = processor.check_compatibility()
        expected = False
        self.assertEqual(actual, expected)

    def test_rdk_feature_compatibility(self):
        logger.debug("-->checking rdk feature are supported")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "hardware":{
                "graphics":True
            },
            "rdk":{
                "supportedFeatures":[
                    "com.comcast.CoPilot",
                    "com.comcast.DeviceProvisioning",
                    "com.comcast.FrameRate",
                    "com.comcast.HdcpProfile",
                    "com.comcast.HdmiInput",
                    "com.comcast.StateObserver",
                    "com.comcast.StorageManager",
                    "org.rdk.ActivityMonitor",
                    "org.rdk.DeviceDiagnostics",
                    "org.rdk.DisplaySettings"
                ]
            }
        }
        processor.app_metadata={
            "graphics":True,
            "features":{
                "com.comcast.HdmiInput",
                "com.comcast.StateObserver",
                "com.comcast.StorageManager",
                "org.rdk.ActivityMonitor",
                "org.rdk.DeviceDiagnostics",
                "org.rdk.DisplaySettings",
                "org.rdk.FrontPanel",
                "org.rdk.HomeNetworking",
                "org.rdk.LoggingPreferences",
                "org.rdk.Network"
            }
        }
        actual = processor._compatibility_check()
        expected = False
        self.assertEqual(actual, expected)

    def test_apparmorProfile(self):
        logger.debug("-->checking apparmorProfile output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "apparmorProfile": "profilename"
        }
        processor.oci_config={
            "process":{
                "apparmorProfile" : {}
            }
        }
        processor._process_apparmorProfile()
        expected = {
            "process":{
                "apparmorProfile":"profilename"
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_empty_apparmorProfile(self):
        logger.debug("-->checking empty apparmorProfile output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "apparmorProfile": ""
        }
        processor.oci_config={
            "process":{
                "apparmorProfile" : {}
            }
        }
        processor._process_apparmorProfile()
        expected = {
            "process":{
                "apparmorProfile":{}
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_seccomp(self):
        logger.debug("-->checking seccomp output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "seccomp":{
                "defaultAction": "SCMP_ACT_ALLOW",
                "architectures": ["SCMP_ARCH_X86","SCMP_ARCH_X32"],
                "syscalls": [{
                    "names": [
                        "getcwd",
                        "chmod"
                    ],
                    "action": "SCMP_ACT_ERRNO"
                    }
                ]
            }
        }
        processor.oci_config={
            "linux":{
                "seccomp": {}
            }
        }
        processor._process_seccomp()
        expected = {
            "linux":{
                "seccomp":{
                    "defaultAction": "SCMP_ACT_ALLOW",
                    "architectures": ["SCMP_ARCH_X86","SCMP_ARCH_X32"],
                    "syscalls": [{
                        "names": [
                            "getcwd",
                            "chmod"
                        ],
                        "action": "SCMP_ACT_ERRNO"
                        }
                    ]
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_empty_seccomp(self):
        logger.debug("-->checking empty seccomp output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "seccomp":{}
        }
        processor.oci_config={
            "linux":{
                "seccomp": {}
            }
        }
        processor._process_seccomp()
        expected = {
            "linux":{
                "seccomp":{}
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_drop_capabilities(self):
        logger.debug("-->checking deleting capabilities output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "capabilities":{
                "drop":["CAP_AUDIT_WRITE", "CAP_NET_RAW"]
            }
        }
        processor.platform_cfg = {
            "capabilities": ["CAP_CHOWN","CAP_AUDIT_WRITE", "CAP_NET_RAW","CAP_FSETID"]
        }
        processor.oci_config={
            'process': {
                'capabilities': {
                    'bounding': [],
                    'permitted': [],
                    'effective': [],
                    'inheritable': [],
                    'ambient': []
                }
            }
        }
        processor._process_capabilities()
        expected = {
            'process': {
                'capabilities': {
                    'bounding': ['CAP_FSETID', 'CAP_CHOWN'],
                    'permitted': ['CAP_FSETID', 'CAP_CHOWN'],
                    'effective': ['CAP_FSETID', 'CAP_CHOWN'],
                    'inheritable': ['CAP_FSETID', 'CAP_CHOWN'],
                    'ambient': ['CAP_FSETID', 'CAP_CHOWN']
                }
            }
        }
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['bounding']), sorted(expected['process']['capabilities']['bounding']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['permitted']), sorted(expected['process']['capabilities']['permitted']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['effective']), sorted(expected['process']['capabilities']['effective']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['inheritable']), sorted(expected['process']['capabilities']['inheritable']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['ambient']), sorted(expected['process']['capabilities']['ambient']))

    def test_add_to_existing_platform_capabilities(self):
        logger.debug("-->checking add to existing platform capabilities output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "capabilities":{
                "add": ["CAP_SETGIDS"]
            }
        }
        processor.platform_cfg = {
            "capabilities": ["CAP_CHOWN"]
        }
        processor.oci_config={
            'process': {
                'capabilities': {
                    'bounding': [],
                    'permitted': [],
                    'effective': [],
                    'inheritable': [],
                    'ambient': []
                }
            }
        }
        processor._process_capabilities()
        expected = {
            'process': {
                'capabilities': {
                    'bounding': ['CAP_CHOWN','CAP_SETGIDS'],
                    'permitted': ['CAP_CHOWN', 'CAP_SETGIDS'],
                    'effective': ['CAP_CHOWN', 'CAP_SETGIDS'],
                    'inheritable': ['CAP_CHOWN', 'CAP_SETGIDS'],
                    'ambient': ['CAP_CHOWN', 'CAP_SETGIDS']
                    }
                }
        }
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['bounding']), sorted(expected['process']['capabilities']['bounding']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['permitted']), sorted(expected['process']['capabilities']['permitted']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['effective']), sorted(expected['process']['capabilities']['effective']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['inheritable']), sorted(expected['process']['capabilities']['inheritable']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['ambient']), sorted(expected['process']['capabilities']['ambient']))

    def test_add_to_default_platform_capabilities(self):
        logger.debug("-->checking defalut capabilities output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "capabilities":{
                "add": ["CAP_SETGIDS"]
            }
        }
        processor.platform_cfg = {
        }
        processor.oci_config={
            'process': {
                'capabilities': {
                    'bounding': [],
                    'permitted': [],
                    'effective': [],
                    'inheritable': [],
                    'ambient': []
                }
            }
        }
        processor._process_capabilities()
        expected = {
            'process': {
                'capabilities': {
                    'bounding': ['CAP_AUDIT_WRITE', 'CAP_CHOWN', 'CAP_FSETID', 'CAP_KILL', 'CAP_NET_BIND_SERVICE', 'CAP_NET_RAW', 'CAP_SETGID', 'CAP_SETGIDS', 'CAP_SETPCAP', 'CAP_SETUID'],
                    'permitted': ['CAP_AUDIT_WRITE', 'CAP_CHOWN', 'CAP_FSETID', 'CAP_KILL', 'CAP_NET_BIND_SERVICE', 'CAP_NET_RAW', 'CAP_SETGID', 'CAP_SETGIDS', 'CAP_SETPCAP', 'CAP_SETUID'],
                    'effective': ['CAP_AUDIT_WRITE', 'CAP_CHOWN', 'CAP_FSETID', 'CAP_KILL', 'CAP_NET_BIND_SERVICE', 'CAP_NET_RAW', 'CAP_SETGID', 'CAP_SETGIDS', 'CAP_SETPCAP', 'CAP_SETUID'],
                    'inheritable': ['CAP_AUDIT_WRITE', 'CAP_CHOWN', 'CAP_FSETID', 'CAP_KILL', 'CAP_NET_BIND_SERVICE', 'CAP_NET_RAW', 'CAP_SETGID', 'CAP_SETGIDS', 'CAP_SETPCAP', 'CAP_SETUID'],
                    'ambient': ['CAP_AUDIT_WRITE', 'CAP_CHOWN', 'CAP_FSETID', 'CAP_KILL', 'CAP_NET_BIND_SERVICE', 'CAP_NET_RAW', 'CAP_SETGID', 'CAP_SETGIDS', 'CAP_SETPCAP', 'CAP_SETUID']
                }
            }
        }
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['bounding']), sorted(expected['process']['capabilities']['bounding']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['permitted']), sorted(expected['process']['capabilities']['permitted']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['effective']), sorted(expected['process']['capabilities']['effective']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['inheritable']), sorted(expected['process']['capabilities']['inheritable']))
        self.assertEqual(sorted(processor.oci_config['process']['capabilities']['ambient']), sorted(expected['process']['capabilities']['ambient']))

    def test_empty_capabilities(self):
        logger.debug("-->checking empty capabilities output")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "capabilities": {}
        }
        processor.app_metadata = {
            "capabilities":{}
        }
        processor.oci_config={
            'process': {
                'capabilities': {}
            }
        }
        processor._process_capabilities()
        expected = {
            "process":{
                'capabilities': {
                    'bounding': [],
                    'permitted': [],
                    'effective': [],
                    'inheritable': [],
                    'ambient': []
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_users_and_groups(self):
        logger.debug("-->checking user and group testing")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "usersAndGroups": {
                "user":{
                    "uid":0,
                    "gid":0,
                    "additionalGids":0
                    },
                "uidMap": [
                {
                    "containerID": 1,
                    "hostID": 234,
                    "size": 45
                }
                ],
                "gidMap": [
                {
                    "containerID": 3,
                    "hostID": 254,
                    "size": 15
                }
                ]
            }
        }
        processor.oci_config={
            "process": {
                "user": {}
            },
            "linux":{
            }
        }
        processor._process_users_and_groups()
        expected = {
            "process": {
                "user": {}
            },
            "linux":{
                "uidMappings" : [{
                        "containerID": 1,
                        "hostID": 234,
                        "size": 45
                    }
                    ],
                "gidMappings" :[
                    {
                        "containerID": 3,
                        "hostID": 254,
                        "size": 15
                    }
                ]
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_users_and_groups_disableUserNamespacing(self):
        logger.debug("-->checking user and group testing")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "disableUserNamespacing":True,
            "usersAndGroups": {
                "user":{
                    "uid":2,
                    "gid":3
                },
                "uidMap": [
                {
                    "containerID": 1,
                    "hostID": 234,
                    "size": 45
                }
                ],
                "gidMap": [
                {
                    "containerID": 3,
                    "hostID": 254,
                    "size": 15
                }
                ]
            }
        }
        processor.oci_config={
            "process": {
                "user": {}
            },
            "linux":{
                'namespaces': [
                    {'type': 'pid'},
                    {'type': 'ipc'}
                ],
                "uidMappings":[],
                "gidMappings":[]
            }
        }
        actual = processor._process_users_and_groups()
        print(actual)
        self.assertEqual(None, actual)

    def test_resources_with_zero_value(self):
        logger.debug("-->checking resources with empty values")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "hardware":{
                "maxRam":"0M"
            }
        }
        processor.app_metadata = {
            "resources":{
                "ram": "0M"
                }
        }
        processor.oci_config={
            "linux":{
                "resources":{
                    "devices":[],
                    "memory":{}
                }
            }
        }
        processor._process_resources()
        expected = {
            "linux":{
                "resources":{
                    "devices":[{
                        "allow": False,
                        "access": "rwm"
                        }
                    ],
                    "memory":{
                        "limit": 0
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_resources_app_value_larger_than_platform(self):
        logger.debug("-->checking ram of app value is larger than the platform")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "hardware":{
                "maxRam":"10M"
            }
        }
        processor.app_metadata = {
            "resources":{
                "ram": "12M"
                }
        }
        processor.oci_config={
            "linux":{
                "resources":{
                    "devices":[],
                    "memory":{}
                }
            }
        }
        processor._process_resources()
        expected = {
            "linux":{
                "resources":{
                    "devices":[{
                        "allow": False,
                        "access": "rwm"
                        }
                    ],
                    "memory":{
                        "limit": 10485760
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_hardware_ram_with_platform_value_larger_than_app(self):
        logger.debug("-->checking hardware ram with platform larger than app")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "hardware":{
                "maxRam":"122M"
            }
        }
        processor.app_metadata = {
            "resources":{
                "ram":"120M"
            }
        }
        processor.oci_config={
            "linux":{
                "resources":{
                    "devices":[],
                    "memory":{}
                }
            }
        }
        processor._process_resources()
        expected = {
            "linux":{
                "resources":{
                    "devices":[{
                        "allow": False,
                        "access": "rwm"
                        }
                    ],
                    "memory":{
                        "limit": 125829120
                    }
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_dynamic_devices_graphic_True_case(self):
        logger.debug("-->checking dynamic devices if graphic is true")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "hardware":{
                "graphics":True
            },
            "gpu":{
                "devs":[
                {
                    "type": "c",
                    "path": "/dev/vchiq",
                    "major": 243,
                    "minor": 0,
                    "access": "rw",
                    "dynamic": True
                },
                {
                    "type": "c",
                    "path": "/dev/snd/controlC0",
                    "major": 116,
                    "minor": 0,
                    "access": "rw",
                    "dynamic": True
                }]
            }
        }
        processor.oci_config={
            "rdkPlugins":{
                "devicemapper":{
                    "data":{
                    "devices":[]
                    }
                }
            }
        }
        processor._process_dynamic_devices()
        expected = {
            "rdkPlugins":{
                'devicemapper': {
                    'required': True,
                    'data': {
                        'devices': ['/dev/vchiq', '/dev/snd/controlC0']
                        }
                    }
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_dynamic_devices_graphic_False_case(self):
        logger.debug("-->checking dynamic devices if graphic is false")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "hardware":{
                "graphics":False
            }
        }
        processor.oci_config={}
        processor._process_dynamic_devices()
        expected = {}
        self.assertEqual(processor.oci_config, expected)

    def test_get_real_uid_gid(self):
        logger.debug("-->checking get uid gid")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
            "disableUserNamespacing":False,
            "usersAndGroups":{
                "uidMap":"",
                "gidMap":""
            }
        }
        processor.oci_config={
            "process":{
                "user":{
                    "gid": '2',
                    "uid": '1'
                }
            }
        }
        processor.get_real_uid_gid()
        expected = {
            "process": {
                "user": {
                    "gid": '2',
                    "uid": '1'
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_logging_missing_in_platform(self):
        logger.debug("-->Platform does not contain logging options")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.platform_cfg = {
        }
        actual = processor._process_logging()
        self.assertEqual(None, actual)

    def test_checking_storage_in_persistent(self):
    #if storage_settings are not present
        logger.debug("-->It will create mounts")
        processor = BundleProcessor()
        processor.rootfs_path = "/tmp/test"
        processor.createmountpoints = None
        processor.app_metadata = {
            "id":"com.rdk.flutter",
            "storage": {
                "persistent":[{
                    "size": "10M",
                    "path": "/home/private"
                }]
            }
        }
        processor.platform_cfg = {
            "storage":{
                "persistent":{
                    "storageDir": "/opt/dac_apps/data/0/dac",
                    "maxSize": "20M",
                    "minSize":"15M",
                    "maxTotalSize":"10"
                }
            }
        }
        processor.oci_config = {
            "mounts":[],
            "rdkPlugins":{
                "storage":{
                    "data":{
                        "loopback":[]
                    }
                }
            }
        }
        processor._process_storage()
        expected = {
            "mounts":[],
            'rdkPlugins': {
                'storage': {
                    'data': {
                        'loopback': [{
                            'destination': '/home/private',
                                'flags': 14,
                                'fstype': 'ext4',
                                'imgsize': 10485760,
                                'source': '/opt/dac_apps/data/0/dac/com.rdk.flutter/23e959658f5082a89c6db72c842271a117887b8658ab703f60eaba650b3d5f20.img'}]
                            },
                            'required': True
                        }
                    }
                }
        self.assertEqual(processor.oci_config, expected)

    def test_checking_storage_in_temp(self):
    #if storage_settings are not present
        logger.debug("-->It will create mounts")
        processor = BundleProcessor()
        processor.rootfs_path = "/tmp/test"
        processor.createmountpoints = None
        processor.app_metadata = {
            "id":"com.rdk.flutter",
            "storage": {
                "temp":[
                    {
                    "size": "5M",
                    "path": "/home/private"
                    }
                ],
                "persistent":[{
                    "size": "10M",
                    "path": "/home/private"
                }]
            }
        }
        processor.platform_cfg = {
            "storage":{
                "persistent":{
                    "storageDir": "/opt/dac_apps/data/0/dac",
                    "maxSize": "20M",
                    "minSize":"15M",
                    "maxTotalSize":"10"
                }
            }
        }
        processor.oci_config = {
            "mounts":[],
            "process":{
                "user":{
                    "uid":1,
                    "gid":2
                }
            },
            "rdkPlugins":{
                "storage":{
                    "data":{
                        "loopback":[]
                    }
                }
            }
        }
        processor._process_storage()
        expected = {
            'mounts': [{
                'destination': '/home/private',
                'type': 'tmpfs',
                'source': 'tmpfs',
                'options': ['nosuid', 'strictatime', 'mode=755', 'size=5242880', 'uid=1', 'gid=2']
                }],
            'process': {
                'user': {
                    'uid': 1, 'gid': 2
                    }
                },
            'rdkPlugins': {
                'storage': {
                'required': True,
                'data': {
                    'loopback': [{
                        'destination': '/home/private',
                        'flags': 14,
                        'fstype': 'ext4',
                        'source': '/opt/dac_apps/data/0/dac/com.rdk.flutter/23e959658f5082a89c6db72c842271a117887b8658ab703f60eaba650b3d5f20.img',
                        'imgsize': 10485760
                        }
                    ]}
                }
            }
        }
        self.assertEqual(processor.oci_config, expected)

    def test_checking_missing_hookLauncherParametersPath(self):
        logger.debug("-->Config dobby.hookLauncherParametersPath is required when dobby.generateCompliantConfig is true")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "id":"com.rdk.flutter"
        }
        processor.platform_cfg = {
            "dobby":{
                "generateCompliantConfig": True,
                "dobbyInitPath":"/usr/libexec/DobbyInit",
                "hookLauncherExecutablePath": "/usr/bin/DobbyPluginLauncher"
            }
        }
        processor.oci_config = {
            "rdkPlugins":{
                "networking":{
                    "required":True
                }
            },
            "hooks":{
            }        
        }
        actual = processor._process_hooks()
        self.assertEqual(None, actual)

    def test_checking_hooks(self):
        logger.debug("-->checking the hooks api")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "id":"com.rdk.flutter"
        }
        processor.platform_cfg = {
            "dobby":{
                "generateCompliantConfig": True,
                "dobbyInitPath":"/usr/libexec/DobbyInit",
                "hookLauncherExecutablePath": "/usr/bin/DobbyPluginLauncher",
                "hookLauncherParametersPath": "/opt/dac_apps/data/{id}/dac/"
            }
        }
        processor.oci_config = {
            "rdkPlugins":{
                "networking":{
                    "required":True
                }
            },
            "hooks":{
            }
        }
        processor._process_hooks()
        expected = {
            "rdkPlugins":{
                "networking":{
                    "required":True
                }
            },
            "hooks":{
                'createRuntime': [{
                    'path': '/usr/bin/DobbyPluginLauncher',
                    'args': ['DobbyPluginLauncher', '-h', 'createRuntime', '-c', '/opt/dac_apps/data/com.rdk.flutter/dac/config.json']
                    }],
                'createContainer': [{
                    'path': '/usr/bin/DobbyPluginLauncher',
                    'args': ['DobbyPluginLauncher', '-h', 'createContainer', '-c', '/opt/dac_apps/data/com.rdk.flutter/dac/config.json']
                    }],
                'poststart': [{
                    'path': '/usr/bin/DobbyPluginLauncher',
                    'args': ['DobbyPluginLauncher', '-h', 'poststart', '-c', '/opt/dac_apps/data/com.rdk.flutter/dac/config.json']
                    }],
                'poststop': [{
                    'path': '/usr/bin/DobbyPluginLauncher',
                    'args': ['DobbyPluginLauncher', '-h', 'poststop', '-c', '/opt/dac_apps/data/com.rdk.flutter/dac/config.json']
                    }]
                }
            }
        self.assertEqual(processor.oci_config, expected)
        
    def test_checking_executablepath_missing(self):
        logger.debug("-->checking the executable path missing from hooks api")
        processor = BundleProcessor()
        processor.rootfs_path = None
        processor.createmountpoints = None
        processor.app_metadata = {
            "id":"com.rdk.flutter"
        }
        processor.platform_cfg = {
            "dobby":{
                "generateCompliantConfig": True,
                "dobbyInitPath":"/usr/libexec/DobbyInit",
                "hookLauncherParametersPath": "/opt/dac_apps/data/{id}/dac/"
            }
        }
        processor.oci_config = {
            "rdkPlugins":{
                "networking":{
                    "required":True
                }
            },
            "hooks":{
            }
        }
        processor._process_hooks()
        expected = {
            "rdkPlugins":{
                "networking":{
                    "required":True
                }
            },
            "hooks":{
                'createRuntime': [{
                    'path': '/usr/bin/DobbyPluginLauncher',
                    'args': ['DobbyPluginLauncher', '-h', 'createRuntime', '-c', '/opt/dac_apps/data/com.rdk.flutter/dac/config.json']
                    }],
                'createContainer': [{
                    'path': '/usr/bin/DobbyPluginLauncher',
                    'args': ['DobbyPluginLauncher', '-h', 'createContainer', '-c', '/opt/dac_apps/data/com.rdk.flutter/dac/config.json']
                    }],
                'poststart': [{
                    'path': '/usr/bin/DobbyPluginLauncher',
                    'args': ['DobbyPluginLauncher', '-h', 'poststart', '-c', '/opt/dac_apps/data/com.rdk.flutter/dac/config.json']
                    }],
                'poststop': [{
                    'path': '/usr/bin/DobbyPluginLauncher',
                    'args': ['DobbyPluginLauncher', '-h', 'poststop', '-c', '/opt/dac_apps/data/com.rdk.flutter/dac/config.json']
                    }]
                }
            }
        self.assertEqual(processor.oci_config, expected)

    def test_checking_gfxlibs_in_gpu(self):
        logger.debug("-->checking _gfxlibs in gpu")
        processor = BundleProcessor()
        processor.rootfs_path = "/tmp/test/rootfs"
        processor.bundle_path = "/tmp/test"
        processor.createmountpoints = False
        processor.app_metadata = {
            "id": "com.rdk.netflix",
            "graphics":True
        }
        processor.platform_cfg = {
            "hardware":{
                "graphics":True
            },
            "gpu": {
                "westeros": {
                    "hostSocket": "/tmp/westeros-dac"
                },
                "extraMounts": [
                    {
                        "source": "/tmp/nxserver_ipc",
                        "destination": "/tmp/nxserver_ipc",
                        "type": "bind",
                        "options": [
                            "bind",
                            "ro"
                        ]
                    }
                ],
                "envvar": [
                    "LD_PRELOAD=/usr/lib/libwayland-client.so.0:/usr/lib/libwayland-egl.so.0"
                ],
                "devs": [
                    {
                        "type": "c",
                        "path": "/dev/nexus",
                        "major": 33,
                        "minor": 0,
                        "access": "rw"
                    }
                ],
                "gfxLibs": [
                    {
                        "src": "/usr/lib/libEGL.so",
                        "dst": "/usr/lib/libEGL.so"
                    },
                    {
                        "src": "/usr/lib/libEGL.so",
                        "dst": "/usr/lib/libEGL.so.1"
                    },
                    {
                        "src": "/usr/lib/libGLESv2.so",
                        "dst": "/usr/lib/libGLESv2.so"
                    },
                    {
                        "src": "/usr/lib/libGLESv2.so",
                        "dst": "/usr/lib/libGLESv2.so.2"
                    }
                ]
            },
            "libs": [
            {
                "apiversions": [
                    "GLIBC_2.4",
                    "GLIBC_PRIVATE"
                ],
                "deps": [],
                "name": "/lib/ld-2.31.so"
            },
            {
                "apiversions": [
                    "GLIBC_2.4",
                    "GLIBC_PRIVATE"
                ],
                "deps": [],
                "name": "/lib/ld-linux-armhf.so.3"
            }]
        }
        processor.oci_config = {
            "linux":{
                "devices":{ },
                "resources":{
                    "devices":[]
                    }
            },
            "mounts":[],
            "process":{
                "env":[]
            }
        }
        processor.libmatcher = LibraryMatching(processor.platform_cfg, processor.bundle_path, processor._add_bind_mount, False, "normal", processor.createmountpoints)
        processor._process_gpu()
        expected = {
            'linux': {
                'devices': [{'path': '/dev/nexus', 'type': 'c', 'major': 33, 'minor': 0}], 
                'resources': {'devices': [{'allow': True, 'type': 'c', 'major': 33, 'minor': 0, 'access': 'rw'}]}}, 
            'mounts': [
                {'source': '/tmp/nxserver_ipc', 'destination': '/tmp/nxserver_ipc', 'type': 'bind', 'options': ['bind', 'ro']},
                {'source': '/usr/lib/libEGL.so', 'destination': '/usr/lib/libEGL.so', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']},
                {'source': '/usr/lib/libEGL.so', 'destination': '/usr/lib/libEGL.so.1', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']},
                {'source': '/usr/lib/libGLESv2.so', 'destination': '/usr/lib/libGLESv2.so', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']},
                {'source': '/usr/lib/libGLESv2.so', 'destination': '/usr/lib/libGLESv2.so.2', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']},
                {'source': '/tmp/westeros-dac', 'destination': '/tmp/westeros', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev']}],
            'process': {'env': ['LD_PRELOAD=/usr/lib/libwayland-client.so.0:/usr/lib/libwayland-egl.so.0', 'WAYLAND_DISPLAY=westeros']}
        }
        self.assertEqual(processor.oci_config, expected)

    def test_checking_dobby_plugindependies01(self):
        logger.debug("-->checking the dobby_plugindependies with libmatching is given as normal")
        processor = BundleProcessor()
        processor.rootfs_path = "/tmp/rootfs"
        processor.bundle_path = "/tmp"
        processor.createmountpoints = False
        processor.platform_cfg = {
            "dobby":{
                "pluginDependencies":[
                    "/lib/libanl.so.1",
                    "/lib/libnsl.so.1"
                ]
            },
            "libs": [
            {
                "apiversions": [
                    "GLIBC_2.4"
                ],
                "deps": [
                    "/lib/libc.so.6",
                    "/lib/libpthread.so.0"
                ],
                "name": "/lib/libanl.so.1"
            },
            {
                "apiversions": [
                    "GLIBC_2.4",
                    "GLIBC_PRIVATE"
                ],
                "deps": [
                    "/lib/libc.so.6"
                ],
                "name": "/lib/libnsl.so.1"
            }]
        }
        processor.oci_config = {
            "mounts":[]
        }
        processor.libmatcher = LibraryMatching(processor.platform_cfg, processor.bundle_path, processor._add_bind_mount, False, "normal", processor.createmountpoints)
        processor._process_dobby_plugin_dependencies()
        expected = {
            'mounts': [{
                'source': '/lib/libnsl.so.1', 'destination': '/lib/libnsl.so.1', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']},
                {'source': '/lib/libanl.so.1', 'destination': '/lib/libanl.so.1', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']},
                {'source': '/lib/libc.so.6', 'destination': '/lib/libc.so.6', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']
                }]
            }
        self.assertEqual(processor.oci_config, expected)

    def test_checking_dobby_plugindependies02(self):
        logger.debug("-->checking the dobby_plugindependies with libmatching is given as image")
        processor = BundleProcessor()
        processor.rootfs_path = "BundleGen/dac-image-wayland-egl-test-bundle/rootfs"
        processor.bundle_path = "BundleGen/dac-image-wayland-egl-test-bundle"
        processor.createmountpoints = False
        processor.platform_cfg = {
            "dobby":{
                "pluginDependencies":[
                    "/usr/lib/libffi.so.7",
                    "/lib/libnsl.so.1"
                ]
            },
            "libs": [
            {
                "apiversions": [
                    "GLIBC_2.4"
                ],
                "deps": [
                    "/lib/libc.so.6",
                    "/lib/libpthread.so.0"
                ],
                "name": "/usr/lib/libffi.so.7"
            },
            {
                "apiversions": [
                    "GLIBC_2.4",
                    "GLIBC_PRIVATE"
                ],
                "deps": [
                    "/lib/libc.so.6"
                ],
                "name": "/lib/libnsl.so.1"
            }]
        }
        processor.oci_config = {
            "mounts":[]
        }
        processor.libmatcher = LibraryMatching(processor.platform_cfg, processor.bundle_path, processor._add_bind_mount, False, "image", processor.createmountpoints)
        processor._process_dobby_plugin_dependencies()
        expected = {
            'mounts': [{
                'source': '/usr/lib/libffi.so.7', 'destination': '/usr/lib/libffi.so.7', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']},
                {'source': '/lib/libc.so.6', 'destination': '/lib/libc.so.6', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']},
                {'source': '/lib/libpthread.so.0', 'destination': '/lib/libpthread.so.0', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']},
                {'source': '/lib/libnsl.so.1', 'destination': '/lib/libnsl.so.1', 'type': 'bind', 'options': ['rbind', 'nosuid', 'nodev', 'ro']}]}

        self.assertEqual(processor.oci_config, expected)

if __name__ == "__main__":
    unittest.main()
