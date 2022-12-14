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
from unit_tests.L1_testing import get_L1_test_results
from bundlegen.core.stb_platform import STBPlatform
from loguru import logger

#This class will test the functionality of API's in stbplatform.py file.
class TestStbPlatform(unittest.TestCase):
    def setUp(self):
         logger.debug("Setup")
         get_L1_test_results.add_test_results.add_tests(self)

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
            get_L1_test_results.add_test_results.test_passed(self)

        for typ, errors in (('ERROR', result.errors), ('FAIL', result.failures)):
            for test, text in errors:
                if test is self:
                    #  the full traceback is in the variable `text`
                    msg = [x for x in text.split('\n')[1:]
                           if not x.startswith(' ')][0]
                    logger.debug("\n\n%s: %s\n     %s" % (typ, self.id(), msg))
                    get_L1_test_results.add_test_results.test_failed(self, msg)

    @classmethod
    def tearDownClass(self):
        get_L1_test_results.add_test_results.end_results(self)

    def test_platform_config_schema(self):
        ''''this test is to check is jsonschema of tempete platform schema is proper.
        one more changes is been added chdir because test been running in folder /BundleGen/unit_tests/L1_testing
        to validate schema changing the directory to /BundleGen
        '''
        logger.debug("==> Validating the templete config schema%s \n "%(os.getcwd()))
        os.chdir('../../')
        search_path = os.path.abspath(os.path.join( os.path.dirname(__file__),'unit_tests','L1_testing', 'test_data_files'))
        validate = STBPlatform("rpi3_reference_vc4_dunfell",search_path)
        actual = validate.validate_platform_config()
        expected = True
        os.chdir('unit_tests/L1_testing')
        self.assertEqual(actual, expected)
        logger.debug("-->Test was Successfully verified")


    def test_wrong_platform_config_schema(self):
        ''''this test is to validate if jsonschema of tempete plateform is proper.
        here i have used vagrant file for testing because in rdk feild "supportedFeatures" is required that
        feild was not there so used.
        '''
        logger.debug("==> Validating the wrong templete config schema")
        os.chdir('../../')
        search_path = os.path.abspath(os.path.join( os.path.dirname(__file__),'unit_tests','L1_testing', 'test_data_files'))
        validate = STBPlatform("vagrant",search_path)
        actual = validate.validate_platform_config()
        expected = False
        self.assertEqual(actual, expected)
        os.chdir('unit_tests/L1_testing')
        logger.debug("-->Test was Successfully verified")


if __name__ == "__main__":
    unittest.main()