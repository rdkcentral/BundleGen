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



import os
import sys
import unittest
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from get_L1_test_results import add_test_results
from bundlegen.core.image_downloader import ImageDownloader
from bundlegen.core.image_unpacker import ImageUnpackager
from loguru import logger

#This class will test the functionality of API's in stbplatform.py file.
class TestImageDownloader(unittest.TestCase):
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

    def test_oci_image_download(self):
        logger.debug("-->checking the image is been downloaded ")
        img_downloader = ImageDownloader()
        image = "oci:./oci_images/dac-image-wayland-egl-test-oci:latest"
        creds = None
        outputdir = "./BundleGen/dac-image-wayland-egl-test-bundle"
        isDir = os.path.isdir(outputdir)
        if (isDir):
            logger.warning("-->bundlegen folder is present so deleting the folder ")
            shutil.rmtree("BundleGen")
        img_downloader.platform_cfg = {
            "platformName": "rpi3_reference",
            "os": "linux",
            "arch": {
                "arch": "arm",
                "variant": "v7"
            },
            "dobby":{
                "generateCompliantConfig": False,
                "dobbyInitPath":"/usr/libexec/DobbyInit",
                "hookLauncherExecutablePath": "/usr/bin/DobbyPluginLauncher",
                "hookLauncherParametersPath": "/opt/dac_apps/data/{id}/dac/"
            },
            "hardware": {
                "graphics": True,
                "maxRam": "120M"
            },
            "storage": {
                "persistent": {
                    "storageDir": "/opt/dac_apps/data/0/dac",
                    "maxSize": "100M",
                    "size": "23",
                    "path": "/var/log/",
                    "fstype": "ext4"
                }
            }
        }
        img_path = img_downloader.download_image(image, creds, img_downloader.platform_cfg)
        tag = img_downloader.get_image_tag(image)
        img_unpacker = ImageUnpackager(img_path, outputdir)
        unpack_success = img_unpacker.unpack_image(tag, delete=True)
        if unpack_success:
            shutil.rmtree("BundleGen")
        self.assertEqual(unpack_success, True)

    def test_oci_image_download_arch_field_missing_case(self):
        logger.debug("-->checking the arch field is missed from the platform ")
        img_downloader = ImageDownloader()
        image = "oci:./oci_images/dac-image-wayland-egl-test-oci:latest"
        creds = None
        img_downloader.platform_cfg = {
            "platformName": "rpi3_reference",
            "os": "linux"
        }
        img_path = img_downloader.download_image(image, creds, img_downloader.platform_cfg)
        self.assertEqual("", img_path)

    def test_oci_image_download_os_field_missing_case(self):
        logger.debug("-->checking the os field is missed from the platfom config ")
        img_downloader = ImageDownloader()
        image = "oci:./oci_images/dac-image-wayland-egl-test-oci:latest"
        creds = None
        img_downloader.platform_cfg = {
            "platformName": "rpi3_reference",
            "arch": {
                "arch": "arm",
                "variant": "v7"
            }
        }
        img_path = img_downloader.download_image(image, creds, img_downloader.platform_cfg)
        self.assertEqual("", img_path)

    def test_negative_case_for_skopeo_not_found_error(self):
        img_downloader = ImageDownloader()
        img_downloader.skopeo_found = False
        image = "oci:./oci_images/dac-image-wayland-egl-test-oci:latest"
        creds = None
        img_downloader.platform_cfg = {
        }
        img_path = img_downloader.download_image(image, creds, img_downloader.platform_cfg)
        self.assertEqual(None, img_path)

    def test_missing_creds_case(self):
        img_downloader = ImageDownloader()
        image = "oci:./oci_images/dac-image-wayland-egl-test-oci:latest"
        creds = "dumpy_value"
        img_downloader.platform_cfg = {
            "platformName": "rpi3_reference",
            "os": "linux",
            "arch": {
                "arch": "arm",
                "variant": "v7"
            }
        }
        img_path = img_downloader.download_image(image, creds, img_downloader.platform_cfg)
        self.assertEqual(None, img_path)


if __name__ == "__main__":
    unittest.main()
