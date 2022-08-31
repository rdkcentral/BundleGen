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
import json
import humanfriendly
import textwrap
from hashlib import sha256
from loguru import logger
from pathlib import Path
from bundlegen.core.utils import Utils
from bundlegen.core.library_matching import LibraryMatching
from bundlegen.core.capabilities import *


class BundleProcessor:
    def __init__(self, platform_cfg, bundle_path, app_metadata, nodepwalking, libmatchingmode, createmountpoints):
        self.platform_cfg: dict = platform_cfg
        self.bundle_path = bundle_path
        self.rootfs_path = os.path.join(self.bundle_path, "rootfs")
        self.app_metadata = app_metadata
        self.handled_libs = set()
        self.createmountpoints = createmountpoints

        self.oci_config: dict = self.load_config()
        self.libmatcher = LibraryMatching(
            self.platform_cfg, self.bundle_path, self._add_bind_mount, nodepwalking, libmatchingmode, createmountpoints)

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
        if self.createmountpoints:
            self._create_mount_points_umoci()
        self._process_oci_version()
        self._process_process()
        self._process_root()
        self._process_mounts()
        self._process_resources()
        self._process_gpu()
        self._process_dobby_plugin_dependencies()
        self._process_users_and_groups()
        self._process_capabilities()
        self._process_hostname()

        # RDK Plugins section
        self._add_rdk_plugins()
        self._process_network()
        self._process_storage()
        self._process_logging()
        self._process_dynamic_devices()

        ## After all plugins are processed
        self._process_hooks()

        self.write_config_json()
        self._cleanup_umoci_leftovers()

        return True

    # ==========================================================================
    def _compatibility_check(self):
        logger.debug("Checking app compatibility")

        # If the app requires graphics but the hardware does not (e.g dev VM)
        if self.app_metadata['graphics'] and not self.platform_cfg.get('hardware').get('graphics'):
            logger.error("Platform does not support graphics output")
            return False

        # Does platform support necessary features?
        if self.platform_cfg['rdk'].get('supportedFeatures'):
            missing_features = [f for f in self.app_metadata['features'] if f not in set(
                self.platform_cfg['rdk'].get('supportedFeatures'))]

            if missing_features:
                logger.error(
                    'App requires the following features which are not supported by the platform: ' + ', '.join(missing_features))
                return False

        # Does platform support required network mode
        if self.app_metadata.get('network'):
            app_network_type = self.app_metadata['network'].get('type')
            if not app_network_type in self.platform_cfg['network']['options']:
                logger.error(
                    f"App requires {app_network_type} networking, which is not supported by the platform")
                return False

        # Does platform support required storages
        storage_settings = self.app_metadata.get('storage')
        persistent_storages_required = storage_settings.get('persistent') if storage_settings else None
        if persistent_storages_required and len(persistent_storages_required) > 0:
            if not self.platform_cfg.get('storage').get('persistent'):
                logger.error(
                    "Cannot create persistent storage - platform does not define options")
                return False
            # Can be multiple persistent storage options
            total_size = 0
            # Validate we are allowed a size this large
            maxSize = self.platform_cfg.get(
                'storage').get('persistent').get('maxSize')
            minSize = self.platform_cfg.get(
                'storage').get('persistent').get('minSize')
            maxTotalSize = self.platform_cfg.get(
                'storage').get('persistent').get('maxTotalSize')
            for persistent in persistent_storages_required:
                # Get desired size from app metadata
                size = persistent.get('size')

                if maxSize and humanfriendly.parse_size(size, binary=True) > humanfriendly.parse_size(maxSize, binary=True):
                    logger.error(
                        f"Persistent storage requested by app exceeds platform limit ({size} > {maxSize})")
                    return False

                if minSize and humanfriendly.parse_size(size, binary=True) < humanfriendly.parse_size(minSize, binary=True):
                    logger.warning(
                        f"Persistent storage requested by app is less than minimum required by platform ({size} < {minSize})")
                    logger.warning(f"Auto adjusting to {minSize} !")
                    size = minSize
                    persistent['size'] = size
                total_size += humanfriendly.parse_size(size, binary=True)

            if maxTotalSize and total_size > humanfriendly.parse_size(maxTotalSize, binary=True):
                logger.error(
                        f"Total persistent storage requested by app exceeds platform limit ({humanfriendly.format_size(total_size, binary=True)} > {maxTotalSize})")
                return False

        temporary_storages_required = storage_settings.get('temp') if storage_settings else None
        if temporary_storages_required and len(temporary_storages_required) > 0:
            if not self.platform_cfg.get('storage').get('temp'):
                logger.warning(
                    "Allowing all temporary storages - platform does not define restrictions")
            else:
                # Can be multiple temp storage options
                total_size = 0
                # Validate we are allowed a size this large
                maxSize = self.platform_cfg.get(
                    'storage').get('temp').get('maxSize')
                minSize = self.platform_cfg.get(
                    'storage').get('temp').get('minSize')
                maxTotalSize = self.platform_cfg.get(
                    'storage').get('temp').get('maxTotalSize')
                for temp in temporary_storages_required:
                    # Get desired size from app metadata
                    size = temp.get('size')

                    if maxSize and humanfriendly.parse_size(size, binary=True) > humanfriendly.parse_size(maxSize, binary=True):
                        logger.error(
                            f"Temporary storage requested by app exceeds platform limit ({size} > {maxSize})")
                        return False

                    if minSize and humanfriendly.parse_size(size, binary=True) < humanfriendly.parse_size(minSize, binary=True):
                        logger.warning(
                            f"Temporary storage requested by app is less than minimum required by platform ({size} < {minSize})")
                        logger.warning(f"Auto adjusting to {minSize} !")
                        size = minSize
                        persistent['size'] = size
                    total_size += humanfriendly.parse_size(size, binary=True)

                if maxTotalSize and total_size > humanfriendly.parse_size(maxTotalSize, binary=True):
                    logger.error(
                            f"Total temporary storage requested by app exceeds platform limit ({humanfriendly.format_size(total_size, binary=True)} > {maxTotalSize})")
                    return False

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
    def get_real_uid_gid(self):
        """
        When the container has user namespacing enabled, the uid/gid set in the process
        options will not match the actual uid/gid on the host. Work out what the real values
        will be if necessary

        Returns:
            tuple: (uid, gid)
        """
        user = self.oci_config['process'].get('user')
        uid = user.get('uid') if user else None
        gid = user.get('gid') if user else None

        if self.platform_cfg.get('disableUserNamespacing'):
            # No user namespacing, return the user/group the process will run as
            return (uid, gid)
        
        # User namespacing enabled, find the actual UID
        user_mapping = self.platform_cfg.get('usersAndGroups').get('uidMap')
        group_mapping = self.platform_cfg.get('usersAndGroups').get('gidMap')

        real_uid = next((x['hostID'] for x in user_mapping if x['containerID'] == uid), None)
        real_gid = next((x['hostID'] for x in group_mapping if x['containerID'] == gid), None)

        if real_uid and real_gid:
            logger.debug(f"User namespacing enabled - resolved host uid/gid to {real_uid}:{real_gid}")
            return (real_uid, real_gid)
        
        logger.warning("User namespacing enabled but could not resolve host uid/gid")
        return (uid, gid)
        

    # ==========================================================================
    def _add_bind_mount(self, src, dst, createmountpoint=False, options=None):
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

        # Crun automatically creates the entries in the rootfs (except RO filesystems) if the permissions are correct
        # on the bundle (e.g. match the mapped in user)

        if createmountpoint:
            self._createAndWriteFileInRootfs(dst, '', 0o644)

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
    def _should_generate_compliant_config(self):
        generate_compliant_config = False
        if self.platform_cfg.get('dobby') and self.platform_cfg['dobby'].get('generateCompliantConfig'):
            generate_compliant_config = True
        return generate_compliant_config

    # ==========================================================================
    def _create_mount_points_umoci(self):
        """Create mount points from file generated by umoci
        """
        for mount in self.oci_config.get('mounts'):
            if (mount.get('destination') != '/etc/resolv.conf'):
                self._createEmptyDirInRootfs(mount.get('destination'))

    # ==========================================================================
    def _process_oci_version(self):
        """Sets the config OCI version to 1.0.2-dobby
        """
        logger.debug("Setting OCI version")
        if not self._should_generate_compliant_config():
            self.oci_config['ociVersion'] = "1.0.2-dobby"
        else:
            self.oci_config['ociVersion'] = "1.0.2"

    # ==========================================================================
    def _process_hooks(self):
        if not self._should_generate_compliant_config():
            return
        if len(self.oci_config['rdkPlugins']) == 0:
            return

        logger.debug("Generating hooks")

        hookLauncherExecutablePath = self.platform_cfg['dobby'].get('hookLauncherExecutablePath')
        if not hookLauncherExecutablePath:
            hookLauncherExecutablePath = "/usr/bin/DobbyPluginLauncher"

        hookLauncherParametersPath = self.platform_cfg['dobby'].get('hookLauncherParametersPath')
        if not hookLauncherParametersPath:
            logger.error(
                    "Config dobby.hookLauncherParametersPath is required when dobby.generateCompliantConfig is true")
            return

        hookLauncherParametersPath = hookLauncherParametersPath.format(id = self.app_metadata['id'])
        if os.path.basename(hookLauncherParametersPath) != "config.json":
            hookLauncherParametersPath = os.path.join(hookLauncherParametersPath, "config.json")

        self.oci_config['hooks'] = {
         "createRuntime": [
            {
                "path": hookLauncherExecutablePath,
                "args": [
                    "DobbyPluginLauncher",
                    "-h",
                    "createRuntime",
                    "-c",
                    hookLauncherParametersPath
                ]
            }
         ],
         "createContainer": [
            {
                "path": hookLauncherExecutablePath,
                "args": [
                    "DobbyPluginLauncher",
                    "-h",
                    "createContainer",
                    "-c",
                    hookLauncherParametersPath
                ]
            }
         ],
         "poststart": [
            {
                "path": hookLauncherExecutablePath,
                "args": [
                    "DobbyPluginLauncher",
                    "-h",
                    "poststart",
                    "-c",
                    hookLauncherParametersPath
                ]
            }
         ],
         "poststop": [
            {
                "path": hookLauncherExecutablePath,
                "args": [
                    "DobbyPluginLauncher",
                    "-h",
                    "poststop",
                    "-c",
                    hookLauncherParametersPath
                ]
            }
         ]
        }

    # ==========================================================================
    def _process_process(self):
        logger.debug("Processing process section")

        # uid/gid set automatically from image by umoci

        # Args will be set to entrypoint from the image

        if self.platform_cfg.get('dobby') and self.platform_cfg['dobby'].get('dobbyInitPath'):
            dobbyinitpath = self.platform_cfg['dobby']['dobbyInitPath']
        else:
            dobbyinitpath = '/usr/libexec/DobbyInit'

        # Add DobbyInit to start of arguments
        self.oci_config['process']['args'].insert(0, dobbyinitpath)

        # We'll need to mount DobbyInit into the container so we can actually use it
        self._add_bind_mount(
            dobbyinitpath, dobbyinitpath, self.createmountpoints)

        # Add platform envvars
        for envvar in self.platform_cfg.get('envvar'):
            self.oci_config['process']['env'].append(envvar)

        # Set resource limits on the process
        resource_limits = self.platform_cfg.get('resourceLimits')
        if resource_limits:
            for limit in resource_limits:
                self.oci_config['process']['rlimits'].append(limit)

    # ==========================================================================
    def _process_root(self):
        logger.debug("Processing root section")

        root = self.platform_cfg.get('root')
        if not root:
            return

        readonly = root.get('readonly')
        if readonly:
            self.oci_config['root']['readonly'] = readonly

        path = root.get('path')
        if path:
            path = path.format(id = self.app_metadata['id'])
            self.oci_config['root']['path'] = path

    # ==========================================================================
    def _process_hostname(self):
        logger.debug("Processing hostname section")

        hostname = self.platform_cfg.get('hostname')
        if hostname:
            hostname = hostname.format(id = self.app_metadata['id'])
            self.oci_config['hostname'] = hostname

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
                if self.createmountpoints:
                    if 'X-mount.mkdir' in mount['options']:
                        self._createEmptyDirInRootfs(mount['destination'])
                    else:
                        self._createAndWriteFileInRootfs(mount['destination'], '', 0o644)

            # Add envvars
            for envvar in self.platform_cfg.get('gpu').get('envvar'):
                self.oci_config['process']['env'].append(envvar)

            # Now mount in any GPU libraries - these will just have a src/dst
            for lib in self.platform_cfg.get('gpu').get('gfxLibs'):
                self.libmatcher.mount(lib['src'], lib['dst'])

            # Add a mount for the westeros socket and set envvar in container
            # This is optional as can be set at container startup
            if self.platform_cfg.get('gpu').get('westeros'):
                socket = self.platform_cfg['gpu']['westeros'].get('hostSocket')
                if socket:
                    self._add_bind_mount(
                        socket, "/tmp/westeros", False, ["rbind", "nosuid", "nodev"])

            if self.platform_cfg.get('gpu').get('waylandDisplay'):
                waylandDisplay = self.platform_cfg['gpu']['waylandDisplay']
            else:
                waylandDisplay = 'westeros'

            self.oci_config['process']['env'].append(
                f"WAYLAND_DISPLAY={waylandDisplay}")

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
            app_ram_bytes = humanfriendly.parse_size(app_ram_requirement, binary=True)
            platform_ram_bytes = humanfriendly.parse_size(hw_max_ram, binary=True)

            self.oci_config['linux']['resources']['memory'] = {}

            if app_ram_bytes > platform_ram_bytes:
                logger.warning(
                    f"App memory requirements too large for platform ({app_ram_requirement}>{hw_max_ram}). Setting RAM to platform limit")
                self.oci_config['linux']['resources']['memory']['limit'] = platform_ram_bytes
            else:
                self.oci_config['linux']['resources']['memory']['limit'] = app_ram_bytes

    # ==========================================================================
    def _is_mapped(self, id, mappings):
        if id is None:
            return True
        if mappings is None:
            return False
        for entry in mappings:
            containerID = entry['containerID']
            size = entry['size']
            if id >= containerID and id < containerID + size:
                return True
        return False

    # ==========================================================================
    def _check_uid_gid_mappings(self):
        user = self.oci_config['process'].get('user')
        uid = user.get('uid') if user else None
        gid = user.get('gid') if user else None
        gids = user.get('additionalGids') if user else None
        uidMappings = self.oci_config['linux'].get('uidMappings')
        gidMappings = self.oci_config['linux'].get('gidMappings')

        if not self._is_mapped(uid, uidMappings):
            logger.warning(f"No mapping found for UID {uid}")
        if not self._is_mapped(gid, gidMappings):
            logger.warning(f"No mapping found for GID {gid}")

        if gids:
            for id in gids:
                if not self._is_mapped(id, gidMappings):
                    logger.warning(f"No mapping found for additional GID {id}")

    # ==========================================================================
    def _process_users_and_groups(self):
        """If a specific user/group mapping has been added to the platform config
        then we need to add that.
        """
        logger.debug("Adding user/group mappings")

        if self.platform_cfg.get('usersAndGroups'):
            user = self.platform_cfg['usersAndGroups'].get('user')
            uid = user.get('uid') if user else None
            gid = user.get('gid') if user else None
            gids = user.get('additionalGids') if user else None
            if uid:
                self.oci_config['process']['user']['uid'] = uid
            if gid:
                self.oci_config['process']['user']['gid'] = gid
            if gids:
                self.oci_config['process']['user']['additionalGids'] = gids

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
            self._check_uid_gid_mappings()

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
        self._check_uid_gid_mappings()

    # ==========================================================================
    def _process_capabilities(self):
        """Adds a default set of capabilities to the config
        """
        logger.debug("Adding capabilities")

        # If the platform defines a baseline set of caps, use that
        app_capabilities = set()
        if not self.platform_cfg.get('capabilities') is None:
            app_capabilities.update(self.platform_cfg['capabilities'])
        else:
            app_capabilities.update(get_default_caps())

        # If the app adds or drops capabilities, add then
        if self.app_metadata.get('capabilities'):
            if self.app_metadata.get('capabilities').get('add'):
                app_capabilities.update(self.app_metadata['capabilities']['add'])

            if self.app_metadata.get('capabilities').get('drop'):
                app_capabilities = app_capabilities.difference(self.app_metadata['capabilities']['drop'])

        # Replace default caps generated by umoci with our caps
        cfg_caps = self.oci_config.get('process').get('capabilities')

        # TODO:: We set the same caps for all types (this is how Docker/Podman works)
        # but we may want to be more granular
        cfg_caps['bounding'] = list(app_capabilities)
        cfg_caps['permitted'] = list(app_capabilities)
        cfg_caps['effective'] = list(app_capabilities)
        cfg_caps['inheritable'] = list(app_capabilities)
        cfg_caps['ambient'] = list(app_capabilities)

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

            # /etc/resolv.conf
            if self.createmountpoints:
                self._createAndWriteFileInRootfs('etc/resolv.conf', '', 0o644)

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

                    fstype = self.platform_cfg.get(
                        'storage').get('persistent').get('fstype')
                    if fstype is None:
                        fstype = "ext4"

                    # Create a path for where the img file should be saved on the host
                    persistent_storage_dir = self.platform_cfg.get(
                        'storage').get('persistent').get('storageDir')

                    # We want to ensure that the same image is used if we upgrade to a new bundle version to persist
                    # app data across upgrades. This will ensure the filename is always the same providing the destination
                    # path (path inside the container) do not change.
                    hash_key = dest_path.encode('ascii')
                    img_name = sha256(hash_key).hexdigest()

                    source_path = os.path.join(
                        persistent_storage_dir, self.app_metadata['id'], f"{img_name}.img")

                    loopback_mnt_def = {
                        "destination": dest_path,
                        "flags": 14,
                        "fstype": f"{fstype}",
                        "source": source_path,
                        "imgsize": humanfriendly.parse_size(size, binary=True)
                    }

                    loopback_plugin['data']['loopback'].append(
                        loopback_mnt_def)

                    self._createEmptyDirInRootfs(dest_path)
                    if self.createmountpoints:
                        tmp_path = dest_path + '.temp'
                        self._createEmptyDirInRootfs(tmp_path)


                # Add plugin to config
                self.oci_config['rdkPlugins']['storage'] = loopback_plugin

            # Temp storage just uses a normal OCI mount set to tmpfs with the
            # size set accordingly
            if storage_settings.get('temp'):
                user = self.oci_config['process'].get('user')
                uid = user.get('uid') if user else None
                gid = user.get('gid') if user else None

                for tmp_mnnt in storage_settings.get('temp'):
                    size = humanfriendly.parse_size(tmp_mnnt.get('size'), binary=True)
                    options = ["nosuid", "strictatime", f"mode=755", f"size={size}"]
                    if uid:
                        options.append(f"uid={uid}")
                    if gid:
                        options.append(f"gid={gid}")
                    mnt_to_add = {
                        "destination": tmp_mnnt['path'],
                        "type": "tmpfs",
                        "source": "tmpfs",
                        "options": options
                    }

                    self.oci_config['mounts'].append(mnt_to_add)

                    self._createEmptyDirInRootfs(tmp_mnnt['path'])

        # Optional mounts also use the storage plugin
        optional_mounts = []
        for mount in self.oci_config['mounts']:
            if mount.get('options') and 'X-dobby.optional' in mount['options']:
                optional_mounts.append(mount)
        for mount in optional_mounts:
            self.oci_config['mounts'].remove(mount)
            mount['options'].remove('X-dobby.optional')
        if len(optional_mounts)> 0:
            storage_plugin = self.oci_config['rdkPlugins'].get('storage')
            if not storage_plugin:
                storage_plugin = {
                    "required": True,
                    "data": {
                    }
                }
                self.oci_config['rdkPlugins']['storage'] = storage_plugin
            storage_plugin['data']['dynamic'] = []
            for mount in optional_mounts:
                storage_plugin['data']['dynamic'].append(mount)

    # ==========================================================================
    def _add_annotation(self, key, value):
        """Adds an annotation to the config
        """
        self.oci_config['annotations'][key] = value

    # ==========================================================================
    def _process_logging(self):
        """Adds the logging plugin to the config to set up container logs
        """
        logger.debug("Configuring logging")

        if not self.platform_cfg.get('logging'):
            logger.info(
                "Platform does not contain logging options - container will not produce any logs")
            return

        self.oci_config['process']['terminal'] = True
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
            self._add_annotation('run.oci.hooks.stderr','/dev/stderr')
            self._add_annotation('run.oci.hooks.stdout','/dev/stdout')
        elif self.platform_cfg['logging'].get('mode') == 'journald':
            logging_plugin = {
                "required": True,
                "data": {
                    "sink": "journald"
                }
            }

        self.oci_config['rdkPlugins']['logging'] = logging_plugin
        return

    # ==========================================================================
    def _process_dynamic_devices(self):
        """Adds the devicemapper plugin to the config to set up dynamic devices:
           devices that do not have a fixed major/minor after boot
        """
        logger.debug("Configuring devicemapper")

        dynamic_devices = []
        for dev in self.platform_cfg.get('gpu').get('devs'):
            if 'dynamic' in dev and dev['dynamic']:
                dynamic_devices.append(dev['path'])

        if len(dynamic_devices) == 0:
            return

        devicemapper_plugin = {
            'required': True,
            'data' : {
                'devices': dynamic_devices
            }
        }

        self.oci_config['rdkPlugins']['devicemapper'] = devicemapper_plugin
        return

    # ==========================================================================
    def _process_dobby_plugin_dependencies(self):
        """
        Mounts any libraries needed from the host into the container

        GPU library mounts are handled in the GPU section
        """
        if self.platform_cfg.get('dobby') and self.platform_cfg['dobby'].get('pluginDependencies'):
            logger.debug("Adding library mounts for Dobby plugins")
            logger.debug("rootfs path is " + self.rootfs_path)
            for lib in self.platform_cfg['dobby']['pluginDependencies']:
                self.libmatcher.mount_or_use_rootfs(lib, lib)

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
