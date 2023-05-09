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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from get_L1_test_results import add_test_results
from bundlegen.core.image_unpacker import ImageUnpackager
from loguru import logger

#This class will test the functionality of API's in stbplatform.py file.
class TestImageUnpackager(unittest.TestCase):
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

    def test_imageunpacker_image_app_metadata_missing(self):
        logger.debug("-->checking the image app metadata is missing ")
        outputdir = "./BundleGen/dac-image-wayland-egl-test-bundle"
        img_path = "/tmp/bundlegen/20230329-120614_2e094abd57974c0895813f5c893b24ca"
        img_unpacker = ImageUnpackager(img_path, outputdir)
        img_appmetdata_path = img_unpacker.image_contains_metadata()
        self.assertEqual(img_appmetdata_path, False)

    def test_imageunpacker_image_app_metadata_in_given_path(self):
        logger.debug("-->checking the image appmetadata is present in the given path ")
        outputdir = "./BundleGen/dac-image-wayland-egl-test-bundle"
        img_path = "/tmp/bundlegen/20230329-120614_2e094abd57974c0895813f5c893b24ca"
        img_unpacker = ImageUnpackager(img_path, outputdir)
        img_unpacker.app_metadata_image_path = "./test_data_files/test-appmetadata.json"
        img_unpacker.image_contains_metadata()
        app_metadata = img_unpacker.get_app_metadata_from_img()
        final_app_metadata = {
            "id": "com.rdk.wayland-egl-test",
            "type": "application/vnd.rdk-app.dac.native",
            "version": "1.0.0",
            "description": "Simple wayland egl demo, showing green rectangle",
            "priority": "optional",
            "graphics": True
        }
        self.assertEqual(final_app_metadata, app_metadata)

    def test_imageunpacker_app_metadata_missing(self):
        logger.debug("-->checking the image app metadata not specified ")
        outputdir = "./BundleGen/dac-image-wayland-egl-test-bundle"
        img_path = "/tmp/bundlegen/20230329-120614_2e094abd57974c0895813f5c893b24ca"
        img_unpacker = ImageUnpackager(img_path, outputdir)
        app_metadata = img_unpacker.get_app_metadata_from_img()
        self.assertEqual(app_metadata, None)


if __name__ == "__main__":
    unittest.main()