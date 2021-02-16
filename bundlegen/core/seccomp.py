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
    def __init__(self, platform_cfg, oci_config):
        self.platform_cfg = platform_cfg
        self.oci_config = oci_config

        # Load seccomp profile from default.json (hardcoded for now)
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

    def parse_kernel(self, kernel_version):
        parts = kernel_version.split(".", maxsplit=2)
        if len(parts) < 2:
            logger.error(
                f"AInvalid kernel version: {kernel_version}, expected '<kernel>.<major>'")
            return False

        if not parts[0].isdigit() or not parts[1].isdigit():
            logger.error(
                f"BInvalid kernel version: {kernel_version}, expected '<kernel>.<major>'")
            return False

        return (parts[0], parts[1])

    def _kernel_version_greater_or_equal(self, min_version, kernel_version):
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
        # First, we need to know the kernel version of the platform
        # Ignore minor revisions or host-specific suffixes
        platform_kernel = self.platform_cfg.get("kernel")
        if platform_kernel is None:
            logger.error("Cannot enable seccomp - unknown kernel version")
            return False

        kernel_version = self.parse_kernel(platform_kernel)
        logger.info(
            f"Kernel version is {kernel_version[0]}.{kernel_version[1]}")

        # validate the seccomp profile
        cfg = self.seccomp_profile
        if cfg.get("defaultAction") is None and len(cfg.get("syscalls")) == 0:
            logger.info("No default action or syscalls - cannot setup seccomp")

        platform_arch = self.platform_cfg["arch"]["arch"]

        # Construct the seccomp section of the OCI runtime config
        spec_cfg = {}
        spec_cfg["defaultAction"] = cfg["defaultAction"]
        spec_cfg["architectures"] = []
        spec_cfg["architectures"].append(
            self.libseccomp_map.get(platform_arch))
        spec_cfg["syscalls"] = []

        logger.info(spec_cfg)

        for syscall in cfg["syscalls"]:
            if syscall["excludes"].get("arches"):
                if platform_arch in syscall["excludes"]["arches"]:
                    continue

            if syscall["excludes"].get("caps"):
                if any(cap in self.oci_config["process"]["capabilities"]["bounding"] for cap in syscall["excludes"]["caps"]):
                    continue

            if syscall["excludes"].get("minKernel"):
                if self._kernel_version_greater_or_equal(self.parse_kernel(syscall["excludes"].get("minKernel")), kernel_version):
                    continue

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
            spec_cfg["syscalls"].append({
                "names": syscall["names"],
                "action": syscall["action"],
                "args": syscall["args"]
            })

        # Done, append this to the OCI config
        logger.info("Created seccomp rules")
        self.oci_config["linux"]["seccomp"] = spec_cfg
