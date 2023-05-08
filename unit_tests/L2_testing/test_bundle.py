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
import humanfriendly

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loguru import logger
from get_L2_test_results import add_test_results
from common import setup_sys_path, TestBase
setup_sys_path()

args=""
capabilities_b = ["CAP_CHOWN","CAP_FSETID","CAP_NET_RAW","CAP_SETGID","CAP_SETUID","CAP_SETPCAP","CAP_NET_BIND_SERVICE","CAP_KILL","CAP_AUDIT_WRITE"]

#app_metadata feilds global declaration
meta_netwrk_type= ""
meta_app_id = ""
meta_ipc = ""
meta_minidump = ""
meta_thunder_bearerUrl = ""
meta_thunder_trusted = ""
meta_thunder_connLimit = ""
meta_oomcrash = ""
meta_resources_ram = ""
meta_resources_gpu = ""
meta_capabilities = ""
meta_capabilities_add = ""
meta_capabilities_drop = ""
meta_storage_persistent_info = []
meta_storage_persistent = []

#platform_config data global exclaration
platform_arguments = "/usr/libexec/DobbyInit"
platform_envvars = ""
platform_envvars_1 = ""
platform_resource_limits = ""
platform_wayland_env= "westeros"
platform_dev_list_platform = []
platform_generateCompliantConfig = ""
platform_graphics = ""
platform_mounts = ""
platform_root_readonly = ""
platform_root_path = ""
platform_apparmorProfile = ""
platform_ipc_session = ""
platform_ipc_system = ""
platform_minidump = ""
platform_oomcrash = ""
platform_hardware_maxram = ""
platform_uid = ""
platform_gid = ""
platform_gids = []
platform_dynamic_devices = []
platform_dynamic_devices_info = []
platform_seccomp_sys_info = []
platform_seccomp_sys = []
platform_seccomp_defaultaction = ""
platform_seccomp_architectures = ""
platform_main_mounts = ""
platform_hostname = ""
platform_uidMap = ""
platform_gidMap = ""

final_config_uidMap = ""
final_config_gidMap = ""
final_config_path = ""
final_config_process_rlimits = ""
final_config_seccomp_defaultaction = ""
final_config_seccomp_architectures = ""
final_config_storage_fstype = ""
final_config_storage_source = ""
final_config_process_args = ""
final_config_process_env = ""
final_config_linux_devices = []
final_config_linux_resource_dev_information = []
final_config_netwrk_type_config = ""
final_config_ipc_session = ""
final_config_ipc_system = ""
final_config_minidump = ""
final_config_oomcrash = ""
final_config_thunder_bearerUrl = ""
final_config_thunder_trusted = ""
final_config_thunder_connLimit = ""
final_ociVersion = ""
final_config_hostname = ""
final_config_root_readonly = ""
final_config_root_path = ""
final_config_apparmorProfile = ""
final_config_gpu_data = ""
final_config_memory_limit = ""
final_config_storage_persistent_info = []
final_config_storage_size = []
final_config_storage_path = ""
final_capabilities_bounding = ""
final_capabilities_permitted = ""
final_capabilities_effective = ""
final_capabilities_inheritable = ""
final_capabilities_ambient = ""
final_config_uid = ""
final_config_gid = ""
final_config_gids = []
final_config_devicemapper_data_info = []
final_config_devicemapper_data = []
final_config_seccomp = ""
final_config_seccomp_sys = []
final_config_seccomp_sys_info = []
final_config_main_mounts = ""

#Form all the app metadata ,platform, config related path below.
form_bundlegen_image_path = "./bundlegen_images/"+sys.argv[1]
form_executable_path = form_bundlegen_image_path+"-bundle/rootfs/usr/bin/"+sys.argv[1].replace("dac-image-","")
form_final_config_json_path = form_bundlegen_image_path+"-bundle/config.json"
form_platform_json_file_path = "../../templates/generic/"+sys.argv[2]+".json"

if os.path.isdir('metadatas') :
    form_app_metadata_json_file_path = "metadatas/"+sys.argv[1]+"-appmetadata.json"
else:
    form_app_metadata_json_file_path = ""+sys.argv[1]+"-appmetadata.json"

def load_json(file_path):
    # open JSON file and parse contents
    fh = open(file_path, "r")
    try:
        data = json.load(fh)
    finally:
        fh.close()
    return data

def exists(obj, chain):
    _key = chain.pop(0)
    if _key in obj:
        return exists(obj[_key], chain) if chain else obj[_key]
    else:
        return None

class TestBundleData(TestBase):
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

    def test_verify_final_executable_path(self):
        logger.debug("-->Verifying appmetadata executable path in bundlegen_image")
        status = os.stat(form_executable_path)
        self.assertNotEqual(status.st_size,0)
        logger.debug("-->Successfully appmetadata executable path has been verified")

    def test_verify_final_config_path(self):
        logger.debug("-->Verifying final config.json path in bundlegen_image")
        status = os.stat(form_final_config_json_path)
        self.assertNotEqual(status.st_size,0)
        logger.debug("-->Successfully final config.json path has been verified")

    def test_verify_final_gpu_devs(self):
        #get the optianl feilds from app_metadata to check if copied to final_config
        platform_graphics = exists(platform_cfg, ['hardware','graphics'])

        if platform_graphics:
            platform_dynamic_devices = exists(platform_cfg, ['gpu','devs'])

            for dev in platform_dynamic_devices:
                if 'dynamic' in dev and dev['dynamic']:
                    global platform_dynamic_devices_info
                    platform_dynamic_devices_info.append(dev['path'])

            if len(platform_dynamic_devices_info) != 0:
                final_config_devicemapper_data = exists(finalconfigdata,['rdkPlugins','devicemapper','data','devices'])

                for key in final_config_devicemapper_data:
                    global final_config_devicemapper_data_info
                    final_config_devicemapper_data_info.append(key)
                flag = 0
                if(set(platform_dynamic_devices_info).issubset(set(final_config_devicemapper_data_info))):
                    flag = 1
                self.assertEqual(flag,1)

    def test_verify_final_ipc_plugin(self):
        #changes related to the ipc
        meta_ipc = exists(appmetadata, ['ipc','enable'])

        if meta_ipc:
            platform_ipc_session = exists(platform_cfg, ['ipc', 'session'])
            platform_ipc_system = exists(platform_cfg, ['ipc', 'system'])
            final_config_ipc_session = exists(finalconfigdata,['rdkPlugins','ipc','data','session'])
            final_config_ipc_system = exists(finalconfigdata,['rdkPlugins','ipc','data','system'])

            if platform_ipc_session and final_config_ipc_session:
                self.assertEqual(final_config_ipc_session,platform_ipc_session)
            if platform_ipc_system and final_config_ipc_system:
                self.assertEqual(final_config_ipc_system,platform_ipc_system)

    def test_verify_final_oomcrash_plugin(self):
        #changes related to ommcrash
        meta_oomcrash = exists(appmetadata, ['oomcrash','enable'])
        if meta_oomcrash:
            platform_oomcrash = exists(platform_cfg, ['oomcrash','path'])
            final_config_oomcrash = exists(finalconfigdata,['rdkPlugins','oomcrash','data','path'])
            self.assertEqual(final_config_oomcrash,platform_oomcrash)

    def test_verify_final_minidump_plugin(self):
        #changes related to minidump
        meta_minidump = exists(appmetadata, ['minidump','enable'])
        if meta_minidump:
            platform_minidump = exists(platform_cfg, ['minidump','destinationPath'])
            final_config_minidump = exists(finalconfigdata,['rdkPlugins','minidump','data','destinationPath'])
            self.assertEqual(final_config_minidump,platform_minidump)

    def test_verify_final_thunder_plugin(self):
        #changes related to thunder plugin
        meta_thunder_bearerUrl = exists(appmetadata, ['thunder', 'bearerUrl'])
        meta_thunder_trusted = exists(appmetadata, ['thunder', 'trusted'])
        meta_thunder_connLimit = exists(appmetadata, ['thunder', 'connLimit'])

        if meta_thunder_bearerUrl is not None and meta_thunder_trusted is not None and meta_thunder_connLimit is not None:
            final_config_thunder_bearerUrl = exists(finalconfigdata,['rdkPlugins','thunder','data','bearerUrl'])
            final_config_thunder_trusted = exists(finalconfigdata,['rdkPlugins','thunder','data','trusted'])
            final_config_thunder_connLimit = exists(finalconfigdata,['rdkPlugins','thunder','data','connLimit'])
            self.assertEqual(final_config_thunder_bearerUrl,meta_thunder_bearerUrl)
            self.assertEqual(final_config_thunder_trusted,meta_thunder_trusted)
            self.assertEqual(final_config_thunder_connLimit,meta_thunder_connLimit)

    def test_verify_final_seccomp(self):
        #changes related to seccomp
        if exists(platform_cfg, ['seccomp']) is not None:
            platform_seccomp_defaultaction = exists(platform_cfg, ['seccomp','defaultAction'])
            platform_seccomp_architectures = exists(platform_cfg,['seccomp','architectures'])
            final_config_seccomp_defaultaction = exists(finalconfigdata,['linux','seccomp','defaultAction'])
            final_config_seccomp_architectures = exists(finalconfigdata,['linux','seccomp','architectures'])
            self.assertEqual(final_config_seccomp_defaultaction,platform_seccomp_defaultaction)

            flag = 0
            if(set(platform_seccomp_architectures).issubset(set(final_config_seccomp_architectures))):
                flag = 1
            self.assertEqual(flag,1)

            platform_seccomp_sys = exists(platform_cfg, ['seccomp','syscalls'])
            for key in platform_seccomp_sys:
                global platform_seccomp_sys_info
                platform_seccomp_sys_info.append(key)

            final_config_seccomp_sys = exists(finalconfigdata,['linux','seccomp','syscalls'])
            for key in final_config_seccomp_sys:
                global final_config_seccomp_sys_info
                final_config_seccomp_sys_info.append(key)

            for f, b in zip(final_config_seccomp_sys_info, platform_seccomp_sys_info):
                # Shall iterate till the required length
                if f == (len(f)-1) :
                    break

                self.assertEqual(f.get('action'),b.get('action'))
                flag = 0
                if(set(b.get('names')).issubset(set(f.get('names')))):
                    flag = 1
                self.assertEqual(flag,1)

    def test_verify_final_apparmorprofile(self):
        #changes related to apparmorProfile
        platform_apparmorProfile = exists(platform_cfg, ['apparmorProfile'])
        final_config_apparmorProfile = exists(finalconfigdata,['process','apparmorProfile'])

        if platform_apparmorProfile is not None:
            self.assertEqual(final_config_apparmorProfile,platform_apparmorProfile)

    def test_verify_final_usersAndGroups(self):
        #changes related to user and groups ids
        if exists(platform_cfg, ['usersAndGroups']):
            platform_user = exists(platform_cfg, ['usersAndGroups','user'])
            platform_uid = exists(platform_cfg, ['usersAndGroups','user','uid']) if platform_user else None
            platform_gid = exists(platform_cfg, ['usersAndGroups','user','gid']) if platform_user else None
            platform_gids = exists(platform_cfg, ['usersAndGroups','user','additionalGids']) if platform_user else None

            if platform_uid is not None:
                final_config_uid = exists(finalconfigdata,['process','user','uid'])
                if final_config_uid is not None:
                    self.assertEqual(final_config_uid,platform_uid)

            if platform_gid is not None:
                final_config_gid = exists(finalconfigdata,['process','user','gid'])
                if final_config_gid is not None:
                    self.assertEqual(final_config_gid,platform_gid)

            if platform_gids is not None:
                final_config_gids = exists(finalconfigdata,['process','user','additionalGids'])
                flag = 0
                if(set(platform_gids).issubset(set(final_config_gids))):
                    flag = 1
                self.assertEqual(flag,1)

    def test_verify_final_uidandgidMappings(self):
        if exists(platform_cfg, ['usersAndGroups']):
            platform_uidMap = exists(platform_cfg, ['usersAndGroups','uidMap'])
            platform_gidMap = exists(platform_cfg, ['usersAndGroups','gidMap'])

            if platform_uidMap is not None:
                final_config_uidMap = exists(finalconfigdata,['linux','uidMappings'])
                if final_config_uidMap is not None:
                    platform_uidMap_string= json.dumps(platform_uidMap)
                    final_config_uidMap_string= json.dumps(final_config_uidMap)
                    flag = 0
                    if(set(platform_uidMap_string).issubset(set(final_config_uidMap_string))):
                        flag = 1
                    self.assertEqual(flag,1)

            if platform_gidMap is not None:
                final_config_gidMap = exists(finalconfigdata,['linux','gidMappings'])
                if final_config_gidMap is not None:
                    platform_gidMap_string= json.dumps(platform_gidMap)
                    final_config_gidMap_string= json.dumps(final_config_gidMap)
                    flag = 0
                    if(set(platform_gidMap_string).issubset(set(final_config_gidMap_string))):
                        flag = 1
                    self.assertEqual(flag,1)

    def test_verify_final_resource_gpu(self):
        #changes related to resources gpu
        meta_resources_gpu = exists(appmetadata, ['resources', 'gpu'])

        if meta_resources_gpu:
            meta_resources_gpu_parse = humanfriendly.parse_size(meta_resources_gpu, binary=True)
            final_config_gpu_data = exists(finalconfigdata,['rdkPlugins','gpu','data','memory'])
            self.assertEqual(final_config_gpu_data,meta_resources_gpu_parse)

    def test_verify_final_hookLaucher(self):
        #changes related to the hookLauncher
        platform_hookLauncherExecutablePath = exists(platform_cfg,['dobby','hookLauncherExecutablePath'])
        final_config_hook_createRuntime = exists(finalconfigdata,['hooks','createRuntime'])
        if final_config_hook_createRuntime is not None:
            for key in final_config_hook_createRuntime:
                if key['path'] is not None:
                    self.assertEqual(platform_hookLauncherExecutablePath,key['path'])
                if key['args'] is not None:
                    self.assertNotEqual(key['args'][4].find(meta_app_id),-1)

        final_config_hook_createContainer = exists(finalconfigdata,['hooks','createContainer'])
        if final_config_hook_createContainer is not None:
            for key in final_config_hook_createContainer:
                if key['path'] is not None:
                    self.assertEqual(platform_hookLauncherExecutablePath,key['path'])
                if key['args'] is not None:
                    self.assertNotEqual(key['args'][4].find(meta_app_id),-1)

        final_config_hook_poststart = exists(finalconfigdata,['hooks','poststart'])
        if final_config_hook_poststart is not None:
            for key in final_config_hook_poststart:
                if key['path'] is not None:
                    self.assertEqual(platform_hookLauncherExecutablePath,key['path'])
                if key['args'] is not None:
                    self.assertNotEqual(key['args'][4].find(meta_app_id),-1)

        final_config_hook_poststop = exists(finalconfigdata,['hooks','poststop'])
        if final_config_hook_poststop is not None:
            for key in final_config_hook_poststop:
                if key['path'] is not None:
                    self.assertEqual(platform_hookLauncherExecutablePath,key['path'])
                if key['args'] is not None:
                    self.assertNotEqual(key['args'][4].find(meta_app_id),-1)

    def test_verify_final_capabilities(self):
        #changes related to capabilities
        if exists(platform_cfg,['capabilities']) is not None:
            meta_capabilities = exists(platform_cfg,['capabilities'])
        else:
            meta_capabilities = capabilities_b

        if exists(appmetadata,['capabilities']) is not None:
            if exists(appmetadata,['capabilities','add']) is not None:
                meta_capabilities_add = exists(appmetadata,['capabilities','add'])
                for add_caps in meta_capabilities_add:
                    meta_capabilities.append(add_caps)
            if exists(appmetadata,['capabilities','drop']) is not None:
                meta_capabilities_drop = exists(appmetadata,['capabilities','drop'])
                for rem_caps in meta_capabilities_drop:
                    meta_capabilities.remove(rem_caps)

        final_capabilities_bounding = exists(finalconfigdata,['process','capabilities','bounding'])
        final_capabilities_permitted = exists(finalconfigdata,['process','capabilities','permitted'])
        final_capabilities_effective = exists(finalconfigdata,['process','capabilities','effective'])
        final_capabilities_inheritable = exists(finalconfigdata,['process','capabilities','inheritable'])
        final_capabilities_ambient = exists(finalconfigdata,['process','capabilities','ambient'])

        if meta_capabilities is not None:
            flag = 0
            if(set(meta_capabilities).issubset(set(final_capabilities_bounding)) and set(meta_capabilities).issubset(set(final_capabilities_permitted)) and
            set(meta_capabilities).issubset(set(final_capabilities_effective)) and set(meta_capabilities).issubset(set(final_capabilities_inheritable)) and
            set(meta_capabilities).issubset(set(final_capabilities_ambient))):
                flag = 1
            self.assertEqual(flag,1)

    def test_verify_final_ociversion(self):
        #changes related to ociversion
        final_ociVersion = exists(finalconfigdata, ['ociVersion'])
        if not platform_generateCompliantConfig:
            self.assertEqual(final_ociVersion,"1.0.2-dobby")
        else:
            self.assertEqual(final_ociVersion,"1.0.2")

    def test_verify_final_hostname(self):
        #changes related to hostname
        platform_hostname = exists(platform_cfg, ['hostname'])
        if platform_hostname:
            final_config_hostname = exists(finalconfigdata,['hostname'])
            if final_config_hostname is not None:
                self.assertNotEqual(final_config_hostname.find(meta_app_id),-1)

    def test_verify_final_annotations(self):
        #changes related to annotations
        final_config_annotations_stderr = exists(finalconfigdata,['annotations','run.oci.hooks.stderr'])
        final_config_annotations_stdout = exists(finalconfigdata,['annotations','run.oci.hooks.stdout'])
        if final_config_annotations_stderr is not None and final_config_annotations_stdout is not None:
            self.assertEqual(final_config_annotations_stderr,"/dev/stderr")
            self.assertEqual(final_config_annotations_stdout,"/dev/stdout")

    def test_verify_final_hardware_maxram(self):
        #changes related to hardware
        platform_hardware_maxram = exists(platform_cfg, ['hardware', 'maxRam'])
        if platform_hardware_maxram:
            global meta_resources_ram
            meta_resources_ram = exists(appmetadata, ['resources', 'ram'])
            final_config_memory_limit =  exists(finalconfigdata,['linux','resources','memory','limit'])

            print(meta_resources_ram)
            meta_resources_ram_c = humanfriendly.parse_size(meta_resources_ram, binary=True)
            platform_hardware_maxram_c = humanfriendly.parse_size(platform_hardware_maxram, binary=True)

            if meta_resources_ram_c > platform_hardware_maxram_c:
                self.assertEqual(platform_hardware_maxram_c,final_config_memory_limit)
            else:
                self.assertEqual(final_config_memory_limit,meta_resources_ram_c)

    def test_verify_final_logging_pugin(self):
        #changes related to logging
        if exists(platform_cfg, ['logging','mode']) == 'file':
            platform_logging_logdir = exists(platform_cfg, ['logging','logDir'])
            final_config_logging_logdir = exists(finalconfigdata, ['rdkPlugins','logging','data','fileOptions','path'])
            self.assertNotEqual(final_config_logging_logdir.find(platform_logging_logdir),-1)

        if exists(platform_cfg, ['logging','limit']):
            platform_logging_limit = exists(platform_cfg, ['logging','limit'])
            final_config_logging_limit = exists(finalconfigdata,['rdkPlugins','logging','data','fileOptions','limit'])
            self.assertEqual(final_config_logging_limit,platform_logging_limit)
        elif exists(platform_cfg, ['logging','mode']) == 'journald':
            platform_logging_mode_journald = exists(platform_cfg, ['logging','mode'])
            final_config_logging_mode_journald = exists(finalconfigdata,['rdkPlugins','logging','data','sink'])
            self.assertEqual(final_config_logging_mode_journald,platform_logging_mode_journald)

        if exists(platform_cfg, ['logging','journaldOptions']):
            platform_logging_journaldOptions = exists(platform_cfg, ['logging','journaldOptions'])
            final_config_logging_journaldOptions = exists(finalconfigdata,['rdkPlugins','logging','data','journaldOptions'])
            self.assertEqual(final_config_logging_journaldOptions,platform_logging_journaldOptions)
        elif exists(platform_cfg, ['logging','mode']) == 'devnull':
            platform_logging_mode_devnull = exists(platform_cfg, ['logging','mode'])
            final_config_logging_mode_devnull = exists(finalconfigdata,['rdkPlugins','logging','data','sink'])
            self.assertEqual(final_config_logging_mode_devnull,platform_logging_mode_devnull)

    def test_verify_final_storage_persistent(self):
        #changes related to storage persistent
        if exists(appmetadata, ['storage']) is not None:
            meta_storage_persistent = exists(appmetadata, ['storage','persistent'])
            if meta_storage_persistent and len(meta_storage_persistent) > 0:
                platform_storage_fstype = exists(platform_cfg, ['storage','persistent','fstype'])
                platform_storage_dir = exists(platform_cfg, ['storage','persistent','storageDir'])
                final_config_storage_size = exists(finalconfigdata,['rdkPlugins','storage','data','loopback'])

                for key in meta_storage_persistent:
                    global meta_storage_persistent_info
                    meta_storage_persistent_info.append(key)

                for key in final_config_storage_size:
                    global final_config_storage_persistent_info
                    final_config_storage_persistent_info.append(key)

                for f, b in zip(final_config_storage_persistent_info, meta_storage_persistent_info):
                    # Shall iterate till the required length
                    if f == (len(f)-1) :
                        break

                    imgsize = humanfriendly.parse_size(b.get('size'), binary=True)
                    final_config_storage_source = f.get('source')
                    self.assertEqual(f.get('imgsize'),imgsize)
                    self.assertEqual(f.get('destination'),b.get('path'))
                    self.assertEqual(f.get('fstype'),platform_storage_fstype)
                    self.assertNotEqual(final_config_storage_source.find(platform_storage_dir),-1)

    def test_verify_final_root(self):
        #changes relate to root
        platform_root_readonly =  exists(platform_cfg, ['root','readonly'])
        platform_root_path = exists(platform_cfg, ['root','path'])

        if platform_root_readonly is not None and platform_root_path is not None:
            final_config_root_readonly =  exists(finalconfigdata,['root','readonly'])
            final_config_root_path =  exists(finalconfigdata,['root','path'])
            self.assertEqual(final_config_root_readonly,platform_root_readonly)
            self.assertNotEqual(final_config_root_path.find(meta_app_id),-1)

    def test_verify_final_config_mounts(self):
        logger.debug("-->Verifying feilds copied form appmata data and platform to final_config files")
        #changes related to main mounts
        platform_main_mounts =  exists(platform_cfg, ['mounts'])
        final_config_main_mounts =  exists(finalconfigdata,['mounts'])
        flag = 0
        #converting to hashable datatype,dict to string
        platform_main_mounts_string= json.dumps(platform_main_mounts)
        final_config_main_mounts_string= json.dumps(final_config_main_mounts)
        if(set(platform_main_mounts_string).issubset(set(final_config_main_mounts_string))):
            flag = 1
        self.assertEqual(flag,1)

    def test_verify_data_in_final_config(self):
        logger.debug("-->Validating feilds been copied to final config.json")
        #Passing the appmetadata.json(argv[1]= "wayland-egl") and platform config(argv[2]= "rpi3_reference") as an argument to input script command
        #We shall copy the app metadata in the same folder where we have this script test_bundle.py

        global appmetadata
        global platform_cfg
        global finalconfigdata
        appmetadata = load_json(form_app_metadata_json_file_path)
        platform_cfg = load_json(form_platform_json_file_path)
        finalconfigdata = load_json(form_final_config_json_path)
        logger.debug("\n\n     %s" % (finalconfigdata))

        #iterating through all keys in appmetadata.json
        for key,value in appmetadata.items():
            if key == "id":
                global meta_app_id
                meta_app_id = value
            if key == "network":
                meta_netwrk_type = value['type']

        #iterating through all keys in platform_cfg.json
        for key,value in platform_cfg.items():
            if key == "dobby" :
                if value['dobbyInitPath'] is not None:
                    global platform_arguments
                    platform_arguments = value['dobbyInitPath']
                if value['generateCompliantConfig'] is not None:
                    global platform_generateCompliantConfig
                    platform_generateCompliantConfig = value['generateCompliantConfig']

            if key == "gpu":
                if value['devs'] is not None:
                    platform_device_infor = value['devs']
                    for k in platform_device_infor:
                        platform_dev_list_platform.append(k)
                if value['envvar'] is not None:
                    platform_envvars = value['envvar']
                if value['extraMounts'] is not None:
                    platform_mounts = value
                    logger.debug(platform_mounts)
                if platform_cfg.get("wayland") is not None:
                    global platform_wayland_env
                    platform_wayland_env = value
            if key == "envvar":
                if value is not None:
                    platform_envvars_1 = value
            if key == "resourceLimits":
                if value is not None:
                    platform_resource_limits = value

        #iterating through all keys in finalconfigdata i.e config.json
        for k,v in finalconfigdata.items():
            if k == "rdkPlugins":
                final_config_netwrk_type_config=v['networking']['data']['type']
                final_config_path = v['logging']['data']['fileOptions']['path']
            if k == "process":
                final_config_process_args = v['args']
                final_config_process_env = v['env']
                final_config_process_rlimits = v['rlimits']
            if k == "linux":
                 final_config_linux_info = v['devices']
                 final_config_linux_resource_dev_info = v['resources']['devices']
                 for key in final_config_linux_info:
                    final_config_linux_devices.append(key)

                 for key in final_config_linux_resource_dev_info:
                    final_config_linux_resource_dev_information.append(key)

        #Validating the appmetadata,platform cfg in config.json
        #Check for the app metadata,.platform config fields in config.json
        self.assertEqual(final_config_netwrk_type_config,meta_netwrk_type)
        #Finding app_id if its subset of rdkPlugins.logging.data.fileOptions.path(present in config.json)
        self.assertNotEqual(final_config_path.find(meta_app_id),-1)

        flag = 0
        if(set(platform_envvars_1).issubset(set(final_config_process_env)) and set(platform_envvars).issubset(set(final_config_process_env))):
            flag = 1
        self.assertEqual(flag,1)

        flag = 0
        #converting to hashable datatype,dict to string
        platform_resource_limits_string= json.dumps(platform_resource_limits)
        final_config_process_rlimits_string= json.dumps(final_config_process_rlimits)
        if(set(platform_resource_limits_string).issubset(set(final_config_process_rlimits_string))):
            flag = 1
        self.assertEqual(flag,1)
        if(set(platform_arguments).issubset(set(final_config_process_args))):
            flag = 1
        self.assertEqual(flag,1)

        # Devs list is appended at the end of the config.json linux.resource.dev and linux.devices,
        # hence reversing and checking the value of config.json against the linux.devices/linux.resources.devices for that number of nodes
        final_config_linux_resource_dev_information.reverse()
        platform_dev_list_platform.reverse()
        final_config_linux_devices.reverse()

        for f, b in zip(final_config_linux_devices, platform_dev_list_platform):

                # Shall iterate till the required length
                if f == (len(f)-1) :
                    break

                self.assertEqual(f.get('path'),b.get('path'))

                self.assertEqual(f.get('type'),b.get('type'))

                self.assertEqual(f.get('major'),b.get('major'))

                self.assertEqual(f.get('minor'),b.get('minor'))

        for f, b in zip(final_config_linux_resource_dev_information, platform_dev_list_platform):

            # Shall iterate till the required length
            if f == (len(f)-1) :
                break

            self.assertEqual(f.get('allow'),True)

            self.assertEqual(f.get('access'),b.get('access'))

            self.assertEqual(f.get('type'),b.get('type'))

            self.assertEqual(f.get('major'),b.get('major'))

            self.assertEqual(f.get('minor'),b.get('minor'))

        logger.debug("-->All values in config.json are validated")

        #iterating through all keys in finalconfigdata
        for k,v in finalconfigdata.items():
                if k == "process":
                    final_config_app_path=v['args'][1]
        self.assertEqual(final_config_app_path,("/usr/bin/"+sys.argv[1].replace("dac-image-","")))
        logger.debug("-->Successfully verified app name from config.json")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'])