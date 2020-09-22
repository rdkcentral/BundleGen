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
import click
import uuid
from loguru import logger
from bundlegen.core.utils import Utils


class ImageUnpackager():
    def __init__(self):
        # Optimism
        self.umoci_found = True

        if os.path.isfile('/usr/bin/umoci'):
            self.umoci_path = '/usr/bin/umoci'
        elif os.path.isfile('/bin/umoci'):
            self.umoci_path = '/bin/umoci'
        else:
            logger.error(
                "Failed to find umoci binary to unpack images", err=True)
            self.umoci_found = False

    # ==========================================================================
    def unpack_image(self, src, tag, dest):
        """Attempt to unpack an OCI image in a given directory to an OCI bundle
        without any modifications

        Calls out to umoci to handle the base conversion
        """
        # If umoci isn't installed, can't unpack
        if not self.umoci_found:
            logger.error("Cannot unpack image as cannot find umoci")
            return

        umoci_command = f'{self.umoci_path} unpack --rootless --image {src}:{tag} {dest}'

        logger.debug(umoci_command)

        success = Utils().run_process(umoci_command)
        if success == 0:
            logger.info(f"Unpacked image successfully to {dest}")
            return True
        else:
            logger.warning("Umoci failed to unpack the image")
            return False
