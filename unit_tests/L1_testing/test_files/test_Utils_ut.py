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
from bundlegen.core.utils import Utils
from loguru import logger

#This class will test the functionality of API's in stbplatform.py file.
class TestUtils(unittest.TestCase):
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

    def test_to_create_ipk_file(self):
        logger.debug("-->checking to create the ipk file ")
        source = "./test_data_files/dac-image-wayland-egl-test-bundle"
        final_app_metadata = {
            "id": "com.rdk.wayland-egl-test",
            "type": "application/vnd.rdk-app.dac.native",
            "version": "1.0.0",
            "description": "Simple wayland egl demo, showing green rectangle",
            "priority": "optional",
            "graphics": True
        }
        platform_cfg = {
            "platformName": "rpi3_reference",
            "os": "linux",
            "arch": {
                "arch": "arm",
                "variant": "v7"
            }
        }
        Utils.create_control_file(platform_cfg, final_app_metadata)
        expected = Utils.create_ipk(source, source)
        self.assertEqual(True, expected)

    def test_failed_to_create_tar_source_file(self):
        logger.debug("-->checking to create the ipk file ")
        source = "./dac-image-wayland-egl-test-bundle"
        DATA_NAME = "data.tar.gz"
        expected = Utils.create_tgz(source, DATA_NAME)
        self.assertEqual(False, expected)

    def test_failed_to_run_process_and_return_output(self):
        logger.debug("-->checking to run the command ")
        command = "umoci unpack --rootless --image /tmp/bundlegen/20230331-112041_ae6ca9eeab67494e9cec8b206bcef66b:latest ./BundleGen/dac-image-wayland-egl-test-bundle"
        expected = Utils.run_process_and_return_output(command)
        self.assertEqual((1, ''), expected)

    def test_utils_add_tarinfo_case(self):
        logger.debug("-->checking new api tarinfo of utils file ")
        source = "./test_data_files/dac-image-wayland-egl-test-bundle"
        DATA_NAME = "data.tar.gz"
        expected = Utils.create_tgz(source, DATA_NAME, 1, 2, '770')
        self.assertEqual(True, expected)


if __name__ == "__main__":
    unittest.main()
