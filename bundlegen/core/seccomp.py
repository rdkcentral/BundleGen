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
from loguru import logger

# By default, we include the default seccomp profile by Docker/Moby
# https://github.com/moby/moby/tree/master/profiles/seccomp
#
# This is designed to offer a reasonable compatability/security tradeoff
# The rationale behind blocked syscalls is documented here:
# https://docs.docker.com/engine/security/seccomp/


class Seccomp:
    def __init__(self, platform_cfg, app_metadata, oci_config):
        self.platform_cfg = platform_cfg
        self.app_metadata = app_metadata
        self.oci_config = oci_config
        self.valid = True

        # Load seccomp profile
        if app_metadata.get('seccomp') and app_metadata['seccomp'].get('allow'):
            # If app has a specific whitelist, use that to build a profie
            self.seccomp_profile = self.build_app_profile()
        elif platform_cfg.get('seccomp') and platform_cfg['seccomp'].get('profile'):
            # Use platform-specific seccomp profie
            custom_profile = platform_cfg['seccomp']['profile']

            if not os.path.exists(custom_profile):
                logger.error(
                    f"Could not find seccomp profile @ '{custom_profile}'")
                valid = False

            logger.info(
                f"Loading custom seccomp profile for platform from {custom_profile}")
            with open(custom_profile) as profile:
                self.seccomp_profile = json.load(profile)
        else:
            # Use default profile
            dirname = os.path.dirname(__file__)
            self.seccomp_profile = {}
            with open(os.path.join(dirname, '../profiles/seccomp/default.json')) as default_profile:
                self.seccomp_profile = json.load(default_profile)

        # map architecture string to seccomp arch used in runtime spec
        self.libseccomp_map = {
            "x86":         "SCMP_ARCH_X86",
            "amd64":       "SCMP_ARCH_X86_64",
            "arm":         "SCMP_ARCH_ARM",
            "arm64":       "SCMP_ARCH_AARCH64",
            "mips64":      	"SCMP_ARCH_MIPS64",
            "mips64n32":   	"SCMP_ARCH_MIPS64N32",
            "mipsel64":    "SCMP_ARCH_MIPSEL64",
            "mips3l64n32": "SCMP_ARCH_MIPSEL64N32",
            "mipsle":      "SCMP_ARCH_MIPSEL",
            "ppc":         "SCMP_ARCH_PPC",
            "ppc64":       "SCMP_ARCH_PPC64",
            "ppc64le":     "SCMP_ARCH_PPC64LE",
            "s390":        "SCMP_ARCH_S390",
            "s390x":       "SCMP_ARCH_S390X"
        }

    def build_app_profile(self):
        """
        Creates a simple seccomp profile based on a list of allowed syscalls in the app metadata"""
        logger.info("Creating custom seccomp profile for application")

        allowed_syscalls = self.app_metadata['seccomp']['allow']

        dirname = os.path.dirname(__file__)
        base_profile = {}
        with open(os.path.join(dirname, '../profiles/seccomp/base.json')) as base_profile:
            base_profile = json.load(base_profile)

        base_profile['syscalls'][0]['names'] = allowed_syscalls

        return base_profile

    def parse_kernel(self, kernel_version):
        """
        Return the major/minor kernel version numbers as ints"""
        parts = kernel_version.split(".", maxsplit=2)
        if len(parts) < 2:
            logger.error(
                f"Invalid kernel version: {kernel_version}, expected '<kernel>.<major>'")
            return False

        if not parts[0].isdigit() or not parts[1].isdigit():
            logger.error(
                f"Invalid kernel version: {kernel_version}, expected '<kernel>.<major>'")
            return False

        return (parts[0], parts[1])

    def _kernel_version_greater_or_equal(self, min_version, kernel_version):
        """
        Checks if the provided kernel version is >= a minimum version"""
        if kernel_version[0] > min_version[0]:
            return True
        if kernel_version[0] == min_version[0] and kernel_version[1] >= min_version[1]:
            return True

        return False

    def enable_seccomp(self):
        """
        Enables seccomp for a container. Uses the loaded profile to block
        specific system calls
        """
        if not self.valid:
            logger.error("Cannot enable seccomp - not in a valid state")
            return False

        # First, we need to know the kernel version of the platform
        # Ignore minor revisions or host-specific suffixes
        platform_kernel = self.platform_cfg.get("kernel")
        if platform_kernel is None:
            logger.warning(
                "Cannot enable seccomp - kernel version not set in platform template")
            return False

        kernel_version = self.parse_kernel(platform_kernel)
        logger.debug(
            f"Kernel version is {kernel_version[0]}.{kernel_version[1]}")

        # validate the seccomp profile
        cfg = self.seccomp_profile
        if cfg.get("defaultAction") is None and len(cfg.get("syscalls")) == 0:
            logger.info("No default action or syscalls - cannot setup seccomp")
            return False

        platform_arch = self.platform_cfg["arch"]["arch"]

        # Construct the seccomp section of the OCI runtime config
        spec_cfg = {}
        spec_cfg["defaultAction"] = cfg["defaultAction"]
        spec_cfg["defaultErrnoRet"] = cfg["defaultErrnoRet"]
        spec_cfg["architectures"] = []
        spec_cfg["architectures"].append(
            self.libseccomp_map.get(platform_arch))
        spec_cfg["syscalls"] = []

        for syscall in cfg["syscalls"]:
            if syscall.get('excludes'):
                if syscall["excludes"].get("arches"):
                    if platform_arch in syscall["excludes"]["arches"]:
                        continue

                if syscall["excludes"].get("caps"):
                    if any(cap in self.oci_config["process"]["capabilities"]["bounding"] for cap in syscall["excludes"]["caps"]):
                        continue

                if syscall["excludes"].get("minKernel"):
                    if self._kernel_version_greater_or_equal(self.parse_kernel(syscall["excludes"].get("minKernel")), kernel_version):
                        continue

            if syscall.get('includes'):
                if syscall["includes"].get("arches"):
                    if not platform_arch in syscall["includes"]["arches"]:
                        continue

                if syscall["includes"].get("caps"):
                    if not any(cap in self.oci_config["process"]["capabilities"]["bounding"] for cap in syscall["includes"]["caps"]):
                        continue

                if syscall["includes"].get("minKernel"):
                    if not self._kernel_version_greater_or_equal(self.parse_kernel(syscall["includes"].get("minKernel")), kernel_version):
                        continue

            # Finally, a valid rule!
            rule = {
                "names": syscall["names"],
                "action": syscall["action"]
            }

            if syscall.get('args'):
                rule["args"] = syscall["args"]

            # Some seccomp blocks can return custom errors. Defaults to EPERM if not specified
            if syscall.get('errnoRet'):
                rule['errnoRet'] = syscall['errnoRet']

            spec_cfg["syscalls"].append(rule)

        # All rules processed, append this to the OCI config
        logger.info("Created seccomp rules")
        self.oci_config["linux"]["seccomp"] = spec_cfg
