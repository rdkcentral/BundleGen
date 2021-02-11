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
from loguru import logger
from bundlegen.core.utils import Utils

class ReadElf:

    # ==========================================================================
    @staticmethod
    def retrieve_apiversions(libfullpath):
        """Retrieve version definitions from .so library
           using readelf binary

        Args:
            libfullpath (string): fullpath to .so library

        Returns:
            array[String]: version definitions
        """
        if not os.path.exists(libfullpath):
            return []

        apiversions = []
        command = f"readelf -V {libfullpath}"
        ## logger.debug(f"Executing command: {command}")
        success, output = Utils.run_process_and_return_output(command)
        if success == 0:
            ## parses something like below to get out 'GLIBC_2.6' :
            ## 0x005c: Rev: 1  Flags: none  Index: 4  Cnt: 2  Name: GLIBC_2.6
            in_version_definition_section = False
            for line in output.splitlines():
                if (in_version_definition_section):
                    if ("Version needs section" in line):
                        in_version_definition_section = False
                    TAG = "Name: "
                    idx = line.find(TAG)
                    if (line.startswith("  0x") and (idx > 0)):
                        apiversions.append(line[idx+len(TAG):])
                elif ("Version definition section" in line):
                    in_version_definition_section = True
        return apiversions
