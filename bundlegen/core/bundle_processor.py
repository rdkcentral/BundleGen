# If not stated otherwise in this file or this component's license file the
# following copyright and licenses apply:
#
# Copyright 2020 Consult Red
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
import re
import json
import glob
import humanfriendly
import textwrap
from loguru import logger
from pathlib import Path
from bundlegen.core.utils import Utils
from bundlegen.core.readelf import ReadElf


class BundleProcessor:
    def __init__(self, platform_cfg, bundle_path, app_metadata):
        self.platform_cfg: dict = platform_cfg
        self.bundle_path = bundle_path
        self.rootfs_path = os.path.join(self.bundle_path, "rootfs")
        self.app_metadata = app_metadata
        self.handled_libs = set()

        self.oci_config: dict = self.load_config()
        self._determine_sublibs()

    # Umoci will produce a config based on a "good, sane default" configuration
    # as defined here: https://github.com/opencontainers/umoci/blob/master/oci/config/convert/default.go
    # which then has the image configs applied on top.

    # We need to modify this config based on the platform configuration, without
    # breaking it. Work through and process each section individually, then
    # perform a final validation of the config

    def check_compatibility(self):
        if not self._compatibility_check():
            logger.error("App is not compatible with the selected platform")
            return False

        return True

    # ==========================================================================
    def begin_processing(self):
        logger.info("Starting processing of bundle using platform template")

        # Basic config
        self._process_oci_version()
        self._process_process()
        self._process_mounts()
        self._process_resources()
        self._process_gpu()
        self._process_lib_matching()
        self._process_users_and_groups()

        # RDK Plugins section
        self._add_rdk_plugins()
        self._process_network()
        self._process_storage()
        self._process_logging()

        self.write_config_json()
        self._cleanup_umoci_leftovers()

        return True

    # ==========================================================================
    def _compatibility_check(self):
        logger.debug("Checking app compatibility")

        # If the app requires graphics but the hardware does not (e.g dev VM)
        if self.app_metadata['graphics'] and not self.platform_cfg.get('hardware').get('graphics'):
            logger.warning("Platform does not support graphics output")
            return False

        # Does platform support necessary features?
        if self.platform_cfg['rdk'].get('supportedFeatures'):
            missing_features = [f for f in self.app_metadata['features'] if f not in set(
                self.platform_cfg['rdk'].get('supportedFeatures'))]

            if missing_features:
                logger.warning(
                    'App requires the following features which are not supported by the platform: ' + ', '.join(missing_features))
                return False

        # Does platform support required network mode
        if self.app_metadata.get('network'):
            app_network_type = self.app_metadata['network'].get('type')
            if not app_network_type in self.platform_cfg['network']['options']:
                logger.warning(
                    f"App requires {app_network_type} networking, which is not supported by the platform")

        # TODO:: Implement more checks here...
        return True

    # ==========================================================================

    def write_config_json(self):
        """Writes the updated config.json file back to disk
        """
        config_json_path = os.path.join(self.bundle_path, 'config.json')
        logger.debug(f'Saving modified OCI config to {config_json_path}')

        with open(config_json_path, 'w', encoding='utf-8') as config_file:
            json.dump(self.oci_config, config_file,
                      ensure_ascii=False, indent=4)

        logger.debug('Written config.json successfully')

    # ==========================================================================
    def _add_bind_mount(self, src, dst, options=None):
        """Adds a bind mount for a file on the host into the container

        Args:
            src (string): Library path on host
            dst (string): Library path relative to container rootfs
        """
        logger.debug(f"Adding bind mount [src: {src}, dst: {dst}]")

        # If we don't specify any mount options, go for a basic read-only but exec-able
        # mount
        mnt_to_add = {}
        if not options or not isinstance(options, list):
            mnt_to_add = {
                "source": src,
                "destination": dst,
                "type": "bind",
                "options": ["rbind", "nosuid", "nodev", "ro"]
            }
        else:
            mnt_to_add = {
                "source": src,
                "destination": dst,
                "type": "bind",
                "options": options
            }

        # Crun automatically creates the entries in the rootfs if the permissions are correct
        # on the bundle (e.g. match the mapped in user)

        # Add bind mount
        if not mnt_to_add in self.oci_config['mounts']:
            self.oci_config['mounts'].append(mnt_to_add)

    # ==========================================================================
    def load_config(self):
        """Loads the config generated by umoci into a dictionary for manipulation

        Returns:
            dict: Config as dictionary
        """
        # Generated config will be called config.json and located in the root
        # of the dir created by umoci
        config_path = os.path.join(self.bundle_path, "config.json")

        # Convert config into dict
        with open(config_path) as config:
            return json.load(config)

    # ==========================================================================
    def _process_oci_version(self):
        """Sets the config OCI version to 1.0.2-dobby
        """
        logger.debug("Setting OCI version")
        self.oci_config['ociVersion'] = "1.0.2-dobby"

    # ==========================================================================
    def _process_process(self):
        logger.debug("Processing process section")

        # uid/gid set automatically from image by umoci

        # Args will be set to entrypoint from the image
        # Add DobbyInit to start of arguments

        self.oci_config['process']['args'].insert(0, '/usr/libexec/DobbyInit')

        # We'll need to mount DobbyInit into the container so we can actually use it
        self._add_bind_mount(
            '/usr/libexec/DobbyInit', '/usr/libexec/DobbyInit')

        # Add platform envvars
        for envvar in self.platform_cfg.get('envvar'):
            self.oci_config['process']['env'].append(envvar)

        # Add capabilities
        # TODO:: Where will these come from? Not a core part of the image spec

        # Set resource limits on the process
        resource_limits = self.platform_cfg.get('resourceLimits')
        if resource_limits:
            for limit in resource_limits:
                self.oci_config['process']['rlimits'].append(limit)

    # ==========================================================================
    def _process_mounts(self):
        """Adds various mounts to the config file
        """
        logger.debug("Processing mounts")

        # Add any extra misc mounts if there are any
        if self.platform_cfg.get('mounts'):
            for mount in self.platform_cfg.get('mounts'):
                self.oci_config['mounts'].append(mount)

        # Add any app-specific mounts
        if self.app_metadata.get('mounts'):
            for mount in self.app_metadata.get('mounts'):
                self.oci_config['mounts'].append(mount)

    # ==========================================================================
    def _process_gpu(self):
        """Adds various GPU mounts/libs
        """
        logger.debug("Processing GPU")

        # Only configure GPU stuff if the app needs graphics
        if self.app_metadata.get('graphics') == True:
            # Check if the platform supports graphics
            if not self.platform_cfg['hardware']['graphics']:
                logger.error(
                    "App requires graphics but platform does not support graphics output")
                return

            # Add mounts
            for mount in self.platform_cfg.get('gpu').get('extraMounts'):
                self.oci_config['mounts'].append(mount)

            # Add envvars
            for envvar in self.platform_cfg.get('gpu').get('envvar'):
                self.oci_config['process']['env'].append(envvar)

            # Now mount in any GPU libraries - these will just have a src/dst
            for lib in self.platform_cfg.get('gpu').get('gfxLibs'):
                if lib['dst'] in self.handled_libs:
                    logger.debug(f"No need to add explicitely: {lib['dst']}")
                self._mount_or_use_rootfs(lib['src'], lib['dst'])

            # Add a mount for the westeros socket and set envvar in container
            # This is optional as can be set at container startup
            if self.platform_cfg.get('gpu').get('westeros'):
                socket = self.platform_cfg['gpu']['westeros'].get('hostSocket')
                if socket:
                    self._add_bind_mount(
                        socket, "/tmp/westeros", ["rbind", "nosuid", "nodev"])

            self.oci_config['process']['env'].append(
                "WAYLAND_DISPLAY=westeros")

            # Add the GPU devices

            # Create the necessary config sections if they don't already exist
            if not self.oci_config['linux'].get('devices'):
                self.oci_config['linux']['devices'] = []

            if not self.oci_config['linux'].get('resources'):
                self.oci_config['linux']['resources'] = {}

            if not self.oci_config['linux']['resources'].get('devices'):
                self.oci_config['linux']['resources']['devices'] = []

            for dev in self.platform_cfg.get('gpu').get('devs'):
                # First add the node
                dev_cfg = {
                    "path": dev['path'],
                    "type": dev['type'],
                    "major": dev['major'],
                    "minor": dev['minor']
                }
                self.oci_config['linux']['devices'].append(dev_cfg)

                # Second set the cgroup permissions
                dev_permissions = {
                    "allow": True,
                    "type": dev['type'],
                    "major": dev['major'],
                    "minor": dev['minor'],
                    "access": dev['access']
                }
                self.oci_config['linux']['resources']['devices'].append(
                    dev_permissions)

    # ==========================================================================

    def _process_resources(self):
        """Set cgroup resource limits

        There's a lot we can do here for security/performance limiting
        in the future. Need to decide what can be set on a per-app basis
        and what should be set per-device.

        For now, it just sets RAM limit based on app requirement

        Device whitelist will be set by Dobby at runtime based on Dobby settings
        file as needs the major/minor numbers for devices
        """
        logger.debug("Processing resources")

        # Create config sections
        if not self.oci_config['linux'].get('resources'):
            self.oci_config['linux']['resources'] = {}

        if not self.oci_config['linux']['resources'].get('devices'):
            self.oci_config['linux']['resources']['devices'] = []

        # If the device cgroup list doesn't contain a "block-all" rule, add it
        # Note: This must come first in the array
        deny_all_devs_cgroup = {
            "allow": False,
            "access": "rwm"
        }

        if not deny_all_devs_cgroup in self.oci_config['linux']['resources']['devices']:
            self.oci_config['linux']['resources']['devices'].append(
                deny_all_devs_cgroup)

        # If the platform defines a max RAM amount for an app, set it if we can
        hw_max_ram = self.platform_cfg.get('hardware').get('maxRam')
        if hw_max_ram:
            app_ram_requirement = self.app_metadata.get('resources').get('ram')
            app_ram_bytes = humanfriendly.parse_size(app_ram_requirement)
            platform_ram_bytes = humanfriendly.parse_size(hw_max_ram)

            self.oci_config['linux']['resources']['memory'] = {}

            if app_ram_bytes > platform_ram_bytes:
                logger.warning(
                    f"App memory requirements too large for platform ({app_ram_requirement}>{hw_max_ram}). Setting RAM to platform limit")
                self.oci_config['linux']['resources']['memory']['limit'] = platform_ram_bytes
            else:
                self.oci_config['linux']['resources']['memory']['limit'] = app_ram_bytes

    # ==========================================================================
    def _process_users_and_groups(self):
        """If a specific user/group mapping has been added to the platform config
        then we need to add that.
        """
        logger.debug("Adding user/group mappings")

        # If the platform doesn't use user namespacing, delete the user namespace
        if self.platform_cfg.get('disableUserNamespacing'):
            logger.debug("User namespacing disabled on this platform")

            # Remove the user namespace type set by umoci
            self.oci_config['linux']['namespaces'][:] = [
                x for x in self.oci_config['linux']['namespaces'] if not x['type'] == 'user']

            # Umoci will have automatically added a uid/gid map based on the user
            # that ran bundlegen. Remove these
            del self.oci_config['linux']['uidMappings']
            del self.oci_config['linux']['gidMappings']

            return

        # Platform supports user namespaces
        self.oci_config['linux']['uidMappings'] = []
        self.oci_config['linux']['gidMappings'] = []

        # If the platform doesn't have a user/group set, it will have to be
        # set dynamically by Dobby at runtime
        if not self.platform_cfg.get('usersAndGroups'):
            logger.debug(
                "Platform does not have a user/group ID mapping set - this must be set at runtime")
            return

        # Syntax in platform cfg is the same as OCI config, so can just copy over
        for uidmap in self.platform_cfg['usersAndGroups'].get('uidMap'):
            self.oci_config['linux']['uidMappings'].append(uidmap)

        for gidmap in self.platform_cfg['usersAndGroups'].get('gidMap'):
            self.oci_config['linux']['gidMappings'].append(gidmap)

    # ==========================================================================
    def _add_rdk_plugins(self):
        """Just adds the rdkplugins section ready to be populated

        Also adds a mount for the Dobby plugin directory so the startContainer
        hook can load them
        """
        self.oci_config['rdkPlugins'] = {}

        if self.platform_cfg.get('dobby') and self.platform_cfg['dobby'].get('pluginDir'):
            plugin_dir = self.platform_cfg['dobby']['pluginDir']
            self._add_bind_mount(plugin_dir, plugin_dir)

    # ==========================================================================
    def _process_network(self):
        # If app needs networking, add the plugin
        # The network settings in app metadata mirrors the plugin config
        # so can just set directly
        logger.debug("Processing network")
        network_settings = self.app_metadata.get('network')
        if network_settings:
            # Create the plugin definition
            self.oci_config['rdkPlugins']['networking'] = {}
            self.oci_config['rdkPlugins']['networking']['required'] = True
            self.oci_config['rdkPlugins']['networking']['data'] = network_settings

            # Networking plugin expects some files in the rootfs
            # Create them with basic contents that can be overridden later

            # /etc/nsswitch.conf
            nsswitch_contents = '''\
                hosts:     files mdns4_minimal [NOTFOUND=return] dns mdns4
                protocols: files\n'''
            self._createAndWriteFileInRootfs(
                'etc/nsswitch.conf', nsswitch_contents, 0o644)

            # /etc/hosts
            hosts_content = "127.0.0.1\tlocalhost\'"
            self._createAndWriteFileInRootfs('etc/hosts', hosts_content, 0o644)

    # ==========================================================================
    def _process_storage(self):
        """Adds the RDK storage plugin to the config and creates any tmpfs mounts
        """
        logger.debug("Processing storage")

        storage_settings = self.app_metadata.get('storage')
        if storage_settings:
            # Persistent storage uses the storage plugin
            if storage_settings.get('persistent'):
                loopback_plugin = {
                    "required": True,
                    "data": {
                        "loopback": []
                    }
                }

                # Can be multiple persistent storage options
                for persistent in storage_settings.get('persistent'):
                    # Get desired size/path from app metadata
                    size = persistent.get('size')
                    dest_path = persistent.get('path')

                    # Validate we are allowed a size this large
                    maxSize = self.platform_cfg.get(
                        'storage').get('persistent').get('maxSize')

                    if maxSize and humanfriendly.parse_size(size) > humanfriendly.parse_size(maxSize):
                        logger.warning(
                            f"Persistent storage requested by app exceeds platform limit ({size} > {maxSize}")

                    if not self.platform_cfg.get('storage').get('persistent'):
                        logger.error(
                            "Cannot create persistent storage - platform does not define options")
                        return

                    # Create a path for where the img file should be saved on the host
                    persistent_storage_dir = self.platform_cfg.get(
                        'storage').get('persistent').get('storageDir')

                    source_path = os.path.join(
                        persistent_storage_dir, self.app_metadata['id'], f"{Utils.get_random_string(8)}.img")

                    loopback_mnt_def = {
                        "destination": dest_path,
                        "flags": 14,
                        "fstype": "ext4",
                        "source": source_path,
                        "imgsize": humanfriendly.parse_size(size)
                    }

                    loopback_plugin['data']['loopback'].append(
                        loopback_mnt_def)

                    self._createEmptyDirInRootfs(dest_path)

                # Add plugin to config
                self.oci_config['rdkPlugins']['storage'] = loopback_plugin

            # Temp storage just uses a normal OCI mount set to tmpfs with the
            # size set accordingly
            if storage_settings.get('temp'):
                for tmp_mnnt in storage_settings.get('temp'):
                    size = humanfriendly.parse_size(tmp_mnnt.get('size'))

                    mnt_to_add = {
                        "destination": tmp_mnnt['path'],
                        "type": "tmpfs",
                        "source": "tmpfs",
                        "options": ["nosuid", "strictatime", "mode=755", f"size={size}"]
                    }

                    self.oci_config['mounts'].append(mnt_to_add)

                    self._createEmptyDirInRootfs(tmp_mnnt['path'])

    # ==========================================================================
    def _process_logging(self):
        """Adds the logging plugin to the config to set up container logs
        """
        logger.debug("Configuring logging")

        if not self.platform_cfg.get('logging'):
            logger.info(
                "Platform does not contain logging options - container will not produce any logs")
            return

        logging_plugin = {}

        # If logging to a file
        if self.platform_cfg['logging'].get('mode') == 'file':
            log_dir = self.platform_cfg['logging']['logDir']
            logfile = os.path.join(log_dir, f"{self.app_metadata['id']}.log")

            logging_plugin = {
                "required": True,
                "data": {
                    "sink": "file",
                    "fileOptions": {
                        "path": logfile
                    }
                }
            }
        elif self.platform_cfg['logging'].get('mode') == 'journald':
            logging_plugin = {
                "required": True,
                "data": {
                    "sink": "jourald"
                }
            }

        self.oci_config['rdkPlugins']['logging'] = logging_plugin
        return

    def _remove_from_rootfs(self, rootfs_filepath):
        """Remove from rootfs. If it is a link, also remove linked file.
        """
        link = os.path.realpath(rootfs_filepath)
        os.remove(rootfs_filepath)
        if (link != rootfs_filepath):
            os.remove(link)

    def _take_host_lib(self, srclib, dstlib, api_info):
        """ The lib version from the host was choosen. Log it, create mount bind
            and remove from image rootfs if present there.
            Also for any sublibs if present.
        """
        logger.debug(f"HOST version choosen: {dstlib}")
        self.handled_libs.add(dstlib)
        rootfs_filepath = os.path.join(self.rootfs_path, dstlib.lstrip('/'))
        self._add_bind_mount(srclib, dstlib)
        if os.path.exists(rootfs_filepath):
            logger.debug(f"Removing from rootfs: {dstlib}")
            self._remove_from_rootfs(rootfs_filepath)
        if api_info and api_info.get('sublibs'):
            for sublib in api_info['sublibs']:
                logger.debug(f"HOST version choosen: {sublib}")
                self.handled_libs.add(sublib)
                self._add_bind_mount(sublib, sublib)
                sublib_rootfs_filepath = os.path.join(self.rootfs_path, sublib.lstrip('/'))
                if os.path.exists(sublib_rootfs_filepath):
                    logger.debug(f"Removing from rootfs: {sublib}")
                    self._remove_from_rootfs(sublib_rootfs_filepath)
        if api_info and api_info.get('deps'):
            for neededlib in api_info['deps']:
                self._mount_or_use_rootfs(neededlib, neededlib)

    def _determine_sublibs(self):
        """
        Determine sublibs inside libs info.
        Specific processing for libc and its sublibs like libresolv.
        First it determines the actual libc lib by finding the one
        with the most GLIBC* versions inside its "Version definition section".
        It also looks for other libs that only contain GLIBC* entries on their
        "Version definition section". These are then assumed to be "sublibraries"
        of libc.so
        """
        if not self.platform_cfg.get('libs'):
            return

        libs = self.platform_cfg['libs']
        max = 0
        libc = None
        sublibs = []
        for lib in libs:
            m1 = re.match(r"^/lib/lib\S+\.so\.\d+$", lib['name'])
            m2 = re.match(r"^/lib/ld-linux\S+\.so\.\d+$", lib['name'])
            if not m1 and not m2:
                continue

            cnt = 0
            for apiversion in lib['apiversions']:
                if (apiversion.startswith('GLIBC_')):
                    cnt += 1
            if cnt == 0 or (cnt != len(lib['apiversions'])):
                continue

            sublibs.append(lib)
            if (cnt > max):
                libc = lib
                max = cnt

        if (libc is None):
            return

        logger.debug(f"Found libc: {libc['name']}")
        sublibs.remove(libc)
        libc['sublibs'] = []
        for sublib in sublibs:
            libc['sublibs'].append(sublib['name'])
            sublib['parentlib'] = libc['name']
            sublib['apiversions'] = []

    def _take_rootfs_lib(self, srclib, dstlib, api_info):
        """ The lib version from image rootfs was choosen. Basically log here that it was choosen.
            Also for any sublibs if present.
        """
        logger.debug(f"IMAGE version choosen: {dstlib}")
        self.handled_libs.add(dstlib)
        if api_info and api_info.get('sublibs'):
            for sublib in api_info['sublibs']:
                logger.debug(f"IMAGE version choosen: {sublib}")
                self.handled_libs.add(sublib)

    # ==========================================================================
    def _mount_or_use_rootfs(self, srclib, dstlib):
        """Determine to mount lib from host OR use the one inside bundle rootfs.
           If lib exists in rootfs and apiversions info exists for it inside *_libs.json config
           then we try to use that version of the lib that has most API versions defined inside.
           If lib does not exist inside image rootfs then create mount bind.
           If no API versions info exists then create mount bind.
           If decision cannot be made because API versions disjunct, choose image rootfs version.

        Args:
            lib (string): lib name like /lib/libc.so.6
            mount_if_not_on_rootfs (bool): if lib doesn't exist inside rootfs
                                           add a mount
        """
        if dstlib in self.handled_libs:
            #logger.debug(f"Already handled: {dstlib}")
            return

        api_info = None
        if self.platform_cfg.get('libs'):
            api_info = [x for x in self.platform_cfg['libs'] if x['name'] == dstlib]
        if not api_info:
            logger.debug(f"No api info found for {dstlib}")
            self._take_host_lib(srclib, dstlib, None)
            return

        api_info = api_info[0]

        # if this is a sublib then switch to logic of parentlib instead
        if api_info.get('parentlib'):
            self._mount_or_use_rootfs(api_info['parentlib'], api_info['parentlib'])
            return

        rootfs_filepath = os.path.join(self.rootfs_path, dstlib.lstrip('/'))
        if not os.path.exists(rootfs_filepath):
            logger.debug(f"Lib not inside image rootfs {dstlib}")
            self._take_host_lib(srclib, dstlib, api_info)
            return

        if len(api_info['apiversions']) > 0:
            version_defs_by_host_lib = set(api_info['apiversions'])
            version_defs_by_rootfs_lib = set(ReadElf.retrieve_apiversions(rootfs_filepath))

            # remove from rootfs and mount lib from host if
            # host lib contains more or same version definitions
            if (version_defs_by_host_lib >= version_defs_by_rootfs_lib):
                ## Library on host has more or same API versions as the one from bundle rootfs. Removing from rootfs and adding mount bind.
                diff = version_defs_by_host_lib - version_defs_by_rootfs_lib
                if (len(diff) == 0):
                    logger.debug(f"Host {dstlib} has same set of apiversions")
                else:
                    logger.debug(f"Host {dstlib} more: {diff}")
                self._take_host_lib(srclib, dstlib, api_info)
            elif (version_defs_by_host_lib < version_defs_by_rootfs_lib):
                ## Library on host has less API versions than the one from bundle rootfs. Keeping the one from bundle rootfs.
                logger.debug(f"Image {dstlib} more: {version_defs_by_rootfs_lib - version_defs_by_host_lib}")
                self._take_rootfs_lib(srclib, dstlib, api_info)
            else:
                logger.error(f"Cannot decide which library to choose! {dstlib}... defaulting to image version.")
                logger.error(f"Image {dstlib} more: {version_defs_by_rootfs_lib - version_defs_by_host_lib}")
                logger.error(f"Host  {dstlib} more: {version_defs_by_host_lib - version_defs_by_rootfs_lib}")
                self._take_rootfs_lib(srclib, dstlib, api_info)
        else:
            logger.debug(f"No apiversions info found for {dstlib}")
            self._take_host_lib(srclib, dstlib, api_info)

    # ==========================================================================
    def _process_lib_matching(self):
        """
        Mounts any libraries needed from the host into the container

        GPU library mounts are handled in the GPU section
        """
        if self.platform_cfg.get('dobby') and self.platform_cfg['dobby'].get('pluginDependencies'):
            logger.debug("Adding library mounts for Dobby plugins")
            logger.debug("rootfs path is " + self.rootfs_path)
            for lib in self.platform_cfg['dobby']['pluginDependencies']:
                self._mount_or_use_rootfs(lib, lib)

    # ==========================================================================
    def _cleanup_umoci_leftovers(self):
        """Umoci creates a few extra files in the bundle we don't care about
        """
        logger.debug("Cleaning up umoici leftovers")
        os.remove(os.path.join(self.bundle_path, "umoci.json"))

        for f_path in Path(self.bundle_path).glob('sha256_*.mtree'):
            logger.debug(f"Deleting {f_path}")
            os.remove(f_path)

    # ==========================================================================
    def _createAndWriteFileInRootfs(self, path, contents, mode):
        """Creates a file in the container rootfs if it doesn't exist with the
        specified contents and linux mode
        """
        fullPath = os.path.join(self.rootfs_path, path.lstrip('/'))

        # Create the directory if doesn't exist
        directory = os.path.dirname(fullPath)
        if not os.path.exists(directory):
            os.makedirs(directory, 0o755)

        # Write the file
        with open(fullPath, 'w') as f:
            # Dedent to remove any leading spaces if using multiline strings
            f.write(textwrap.dedent(contents))

        os.chmod(fullPath, mode)

    # ==========================================================================
    def _createEmptyDirInRootfs(self, path):
        """Creates an empty directory in the container rootfs if it doesn't exist with the
        specified contents and linux mode
        """
        fullPath = os.path.join(self.rootfs_path, path.lstrip('/'))

        logger.debug(f"Creating directory {fullPath}")

        # Create the directory if doesn't exist
        if not os.path.exists(fullPath):
            os.makedirs(fullPath, 0o755)
