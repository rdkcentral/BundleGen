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
import time

from loguru import logger
from bundlegen.core.utils import Utils


class ImageDownloader():
    def __init__(self):
        # Optimism
        self.skopeo_found = True

        skopeo_path = shutil.which('skopeo')
        if skopeo_path:
            logger.debug(f"Using skopeo: {skopeo_path}")
        else:
            logger.error(
                "Failed to find skopeo binary to download images", err=True)
            self.skopeo_found = False

    # ==========================================================================
    @staticmethod
    def get_image_tag(url):
        """Gets the tag from a given image url

        Args:
            url (string): URL to the image

        Returns:
            string: Image tag
        """
        # Attempt to get the tag
        tag = url.rsplit(':', 1)[-1]

        # If we found //, there probably wasn't a tag on the end and we just found
        # the protocol section. Return latest
        if "//" in tag:
            return "latest"
        return tag

    # ==========================================================================
    def download_image(self, url, creds, platform_cfg):
        """Attempt to download the specified image using skopeo

        Will download and extract the image to /tmp

        Args:
            url (string): URL to download the image from (e.g. docker://hello-world:latest)
            creds (string): Credentials for the OCI registry in the form username:password
            platform_cfg (dict): Platform template

        Returns:
            string: Path to downloaded image
        """
        # If skopeo isn't installed, can't download
        if not self.skopeo_found:
            logger.error("Cannot download image as cannot find skopeo")
            return

        image_tag = self.get_image_tag(url)

        # Get arch from config
        if 'arch' not in platform_cfg:
            logger.error("Platform architecture is not defined", err=True)
            return ""
        else:
            arch = platform_cfg['arch'].get('arch')
            variant = platform_cfg['arch'].get('variant')

        if 'os' not in platform_cfg:
            logger.error("Platform OS is not defined", err=True)
            return ""
        else:
            platform_os = platform_cfg.get('os')

        # Save the image to a temp dir. Use uuid to generate a unique name
        if not os.path.exists('/tmp/bundlegen'):
            os.makedirs('/tmp/bundlegen')

        now = time.strftime("%Y%m%d-%H%M%S")
        destination = f'/tmp/bundlegen/{now}_{Utils.get_random_string()}'
        logger.info(f"Downloading image to {destination}...")

        # Build the command to skopeo
        skopeo_command = f'skopeo '

        if creds:
            skopeo_command += f'--src-creds {creds} '

        if variant:
            skopeo_command += f'--override-os {platform_os} --override-arch {arch} --override-variant {variant} '
        else:
            skopeo_command += f'--override-os {platform_os} --override-arch {arch} '

        skopeo_command += f'copy {url} oci:{destination}:{image_tag}'

        logger.debug(skopeo_command)

        # Run skopeo, and stream the output to the console
        success = Utils.run_process(skopeo_command)
        if success == 0:
            logger.success(
                f"Downloaded image from {url} successfully to {destination}")
            return destination
        else:
            logger.warning("Skopeo failed to download the image")
            return None
