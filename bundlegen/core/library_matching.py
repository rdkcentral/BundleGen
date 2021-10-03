# If not stated otherwise in this file or this component's license file the
# following copyright and licenses apply:
#
# Copyright 2020 Liberty Global B.V.
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
from loguru import logger
from bundlegen.core.readelf import ReadElf


class LibraryMatching:
    def __init__(self, platform_cfg, bundle_path, add_mount_func, nodepwalking, libmatchingmode, createmountpoints):
        self.platform_cfg = platform_cfg
        self.bundle_path = bundle_path
        self.rootfs_path = os.path.join(self.bundle_path, "rootfs")
        self.libmatchingmode = libmatchingmode
        self.nodepwalking = nodepwalking
        self.createmountpoints = createmountpoints
        self.handled_libs = set()
        self.add_mount_func = add_mount_func
        self._determine_sublibs()
        if self.nodepwalking:
            logger.info("Library dependency walking is DISABLED!")
        elif not self.platform_cfg.get('libs'):
            logger.warning("Library dependency walking DISABLED because no _libs.json file available!")
        logger.debug(f"Libmatching mode: {libmatchingmode}")

    # ==========================================================================
    def _add_bind_mount(self, src, dst):
        self.add_mount_func(src, dst)

    # ==========================================================================
    def _remove_from_rootfs(self, rootfs_filepath):
        """Remove from rootfs. If it is a link, also remove linked file.
        """
        link = os.path.realpath(rootfs_filepath)
        os.remove(rootfs_filepath)
        if (link != rootfs_filepath):
            os.remove(link)
    # ==========================================================================
    def _create_mount_point(self, fullPath):
        """Create mount point (empty file) in provided path.
        """
        # Create the directory if doesn't exist
        directory = os.path.dirname(fullPath)
        if not os.path.exists(directory):
            os.makedirs(directory, 0o755)
        open(fullPath, mode = 'x')
        os.chmod(fullPath, 0o777)
    # ==========================================================================
    def _take_host_lib(self, srclib, dstlib, api_info):
        """ The lib version from the host was choosen. Log it, create mount bind
            and remove from OCI image rootfs if present there.
            Also for any sublibs if present.
        """
        logger.trace(f"HOST version choosen: {srclib}")
        self.handled_libs.add(dstlib)
        rootfs_filepath = os.path.join(self.rootfs_path, dstlib.lstrip('/'))
        self._add_bind_mount(srclib, dstlib)
        if os.path.exists(rootfs_filepath):
            logger.trace(f"Removing from rootfs: {dstlib}")
            self._remove_from_rootfs(rootfs_filepath)
        if self.createmountpoints:
            self._create_mount_point(rootfs_filepath)
        if api_info and api_info.get('sublibs'):
            for sublib in api_info['sublibs']:
                logger.trace(f"HOST version choosen: {sublib}")
                self.handled_libs.add(sublib)
                self._add_bind_mount(sublib, sublib)
                sublib_rootfs_filepath = os.path.join(self.rootfs_path, sublib.lstrip('/'))
                if os.path.exists(sublib_rootfs_filepath):
                    logger.trace(f"Removing from rootfs: {sublib}")
                    self._remove_from_rootfs(sublib_rootfs_filepath)
                    if self.createmountpoints:
                        self._create_mount_point(rootfs_filepath)
        if api_info and api_info.get('deps'):
            for neededlib in api_info['deps']:
                self._mount_or_use_rootfs(neededlib, neededlib)

    # ==========================================================================
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
        if self.nodepwalking or not self.platform_cfg.get('libs'):
            return

        libs = self.platform_cfg['libs']
        maxcnt = 0
        libc = None
        sublibs = []
        for lib in libs:
            m1 = re.match(r"^/(?:usr/)?lib/lib\S+\.so\.\d+$", lib['name'])
            m2 = re.match(r"^/(?:usr/)?lib/ld-linux\S*\.so\.\d+$", lib['name'])
            if not m1 and not m2:
                continue

            cnt = 0
            for apiversion in lib['apiversions']:
                if (apiversion.startswith('GLIBC_')):
                    cnt += 1
            if cnt == 0 or (cnt != len(lib['apiversions'])):
                continue

            sublibs.append(lib)
            if (cnt > maxcnt):
                libc = lib
                maxcnt = cnt

        if (libc is None):
            return

        logger.trace(f"Found libc: {libc['name']}")
        sublibs.remove(libc)
        libc['sublibs'] = []
        for sublib in sublibs:
            libc['sublibs'].append(sublib['name'])
            sublib['parentlib'] = libc['name']
            sublib['apiversions'] = []

    def _take_rootfs_lib(self, dstlib, api_info):
        """ The lib version from OCI image rootfs was choosen. Basically log here that it was choosen.
            Also for any sublibs if present.
        """
        logger.trace(f"OCI IMAGE version choosen: {dstlib}")
        self.handled_libs.add(dstlib)
        if api_info and api_info.get('sublibs'):
            for sublib in api_info['sublibs']:
                logger.trace(f"OCI IMAGE version choosen: {sublib}")
                self.handled_libs.add(sublib)

    # ==========================================================================
    def _mount_or_use_rootfs(self, srclib, dstlib):
        """Determine to mount lib from host OR use the one inside bundle/OCI rootfs.
           If lib exists in rootfs and apiversions info exists for it inside *_libs.json config
           then we try to use that version of the lib that has most API versions defined inside.
           If lib does not exist inside image rootfs then create mount bind.
           If no API versions info exists then create mount bind.
           If decision cannot be made because API versions disjunct, choose image rootfs version.

        Args:
            srclib (string): libpath on host. For this lib, the api info will be looked up
                             inside *_libs.json.
            dstlib (string): libpath in rootfs image. In most cases the same as srclib. For this lib
                             the api info will be read directly from the lib file via readelf.
        """
        if dstlib in self.handled_libs:
            #logger.trace(f"Already handled: {dstlib}")
            return

        api_info = None
        if not self.nodepwalking:
            if self.platform_cfg.get('libs'):
                api_info = [x for x in self.platform_cfg['libs'] if x['name'] == srclib]
                if not api_info:
                    logger.trace(f"No api info found for {dstlib}")

        if not api_info:
            if (self.libmatchingmode == 'image'):
                rootfs_filepath = os.path.join(self.rootfs_path, dstlib.lstrip('/'))
                if not os.path.exists(rootfs_filepath):
                    logger.trace(f"Lib not inside OCI image rootfs {dstlib}")
                    self._take_host_lib(srclib, dstlib, None)
                else:
                    logger.trace(f"OCI Image {dstlib} forcibly choosen.")
                    self._take_rootfs_lib(dstlib, None)
            else: # normal and host modes
                self._take_host_lib(srclib, dstlib, None)
            return

        api_info = api_info[0]

        # if this is a sublib then switch to logic of parentlib instead
        if self.libmatchingmode == 'normal' and api_info.get('parentlib'):
            self._mount_or_use_rootfs(api_info['parentlib'], api_info['parentlib'])
            return

        rootfs_filepath = os.path.join(self.rootfs_path, dstlib.lstrip('/'))
        if not os.path.exists(rootfs_filepath):
            logger.trace(f"Lib not inside OCI image rootfs {dstlib}")
            self._take_host_lib(srclib, dstlib, api_info)
            return

        if (self.libmatchingmode == 'image'):
            logger.trace(f"OCI Image {dstlib} forcibly choosen.")
            self._take_rootfs_lib(dstlib, api_info)
            return
        elif (self.libmatchingmode == 'host'):
            logger.trace(f"Host {dstlib} forcibly choosen.")
            self._take_host_lib(srclib, dstlib, api_info)
            return
        ## else normal mode below

        if len(api_info['apiversions']) > 0:
            version_defs_by_host_lib = set(api_info['apiversions'])
            version_defs_by_rootfs_lib = set(ReadElf.retrieve_apiversions(rootfs_filepath))

            # remove from rootfs and mount lib from host if
            # host lib contains more or same version definitions
            if (version_defs_by_host_lib >= version_defs_by_rootfs_lib):
                ## Library on host has more or same API versions as the one from bundle rootfs. Removing from rootfs and adding mount bind.
                diff = version_defs_by_host_lib - version_defs_by_rootfs_lib
                if (len(diff) == 0):
                    logger.trace(f"Host {dstlib} has same set of apiversions")
                else:
                    logger.trace(f"Host {dstlib} more: {diff}")
                self._take_host_lib(srclib, dstlib, api_info)
            elif (version_defs_by_host_lib < version_defs_by_rootfs_lib):
                ## Library on host has less API versions than the one from bundle rootfs. Keeping the one from bundle rootfs.
                logger.trace(f"OCI Image {dstlib} more: {version_defs_by_rootfs_lib - version_defs_by_host_lib}")
                self._take_rootfs_lib(dstlib, api_info)
            else:
                logger.error(f"Cannot decide which library to choose! {dstlib}... defaulting to OCI image version.")
                logger.error(f"OCI Image {dstlib} more: {version_defs_by_rootfs_lib - version_defs_by_host_lib}")
                logger.error(f"Host      {dstlib} more: {version_defs_by_host_lib - version_defs_by_rootfs_lib}")
                self._take_rootfs_lib(dstlib, api_info)
        else:
                self._take_host_lib(srclib, dstlib, api_info)

    # ==========================================================================
    def mount(self, srclib, dstlib):
        """Mount lib from host. Its dependencies will be added automatically, mounted from
           host or taken from OCI image. See _mount_or_use_rootfs().

        Args:
            srclib (string): libpath on host. For this lib, the api info will be looked up
                             inside *_libs.json.
            dstlib (string): libpath in rootfs image. In most cases the same as srclib.
        """
        logger.trace(f"Explicitely adding for host mount: {dstlib}")
        if dstlib in self.handled_libs:
            logger.trace(f"No need to add explicitely: {dstlib}")
        api_info = None
        if not self.nodepwalking:
            if self.platform_cfg.get('libs'):
                api_info = [x for x in self.platform_cfg['libs'] if x['name'] == srclib]
                if not api_info:
                    logger.trace(f"No api info found for {dstlib}")
                else:
                    api_info = api_info[0]
        self._take_host_lib(srclib, dstlib, api_info)

    # ==========================================================================
    def mount_or_use_rootfs(self, srclib, dstlib):
        """ See _mount_or_use_rootfs().

        Args:
            srclib (string): libpath on host. For this lib, the api info will be looked up
                             inside *_libs.json.
            dstlib (string): libpath in rootfs image. In most cases the same as srclib.
        """
        logger.trace(f"Explicitely adding for host mount or from OCI: {dstlib}")
        if dstlib in self.handled_libs:
            logger.trace(f"No need to add explicitely: {dstlib}")
        self._mount_or_use_rootfs(srclib, dstlib)



