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
import shutil
import json
from loguru import logger
from bundlegen.core.utils import Utils


class ImageUnpackager():
    def __init__(self, src, dst):
        # Optimism
        self.umoci_found = True

        umoci_path = shutil.which('umoci')
        if umoci_path:
            logger.debug(f"Using umoci: {umoci_path}")
        else:
            logger.error(
                "Failed to find umoci binary to unpack images", err=True)
            self.umoci_found = False

        self.src = src
        self.dest = dst

        self.app_metadata_image_path = os.path.join(self.dest, "rootfs", "appmetadata.json")

    # ==========================================================================
    def unpack_image(self, tag, delete=False):
        """Attempt to unpack an OCI image in a given directory to an OCI bundle
        without any modifications

        Calls out to umoci to handle the base conversion
        """
        # If umoci isn't installed, can't unpack
        if not self.umoci_found:
            logger.error("Cannot unpack image as cannot find umoci")
            return

        umoci_command = f'umoci unpack --rootless --image {self.src}:{tag} {self.dest}'

        logger.debug(umoci_command)

        success = Utils().run_process(umoci_command)
        if success == 0:
            logger.info(f"Unpacked image successfully to {self.dest}")

            if delete:
                logger.debug("Deleting downloaded image")
                shutil.rmtree(self.src)

            return True
        else:
            logger.warning("Umoci failed to unpack the image")
            return False

    def image_contains_metadata(self):
        return os.path.exists(self.app_metadata_image_path)

    def delete_img_app_metadata(self):
        if self.image_contains_metadata():
            logger.debug("Deleting app metadata file from unpacked image")
            os.remove(self.app_metadata_image_path)

    def get_app_metadata_from_img(self):
        if self.image_contains_metadata():
            with open(self.app_metadata_image_path) as metadata:
                app_metadata_dict = json.load(metadata)

            return app_metadata_dict
        return None
