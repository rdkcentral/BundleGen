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

from loguru import logger
os.chdir("..")
result = open("L1_test_results.txt", "w")
result.write("SNo\tTest Name (Results)\t\tReason\n")
result.write("---\t-------------------\t\t------")
result.close()

passed=0
total=0

class add_test_results:
    def add_tests(self):
        logger.debug("Adding new Test to the list...")
        logger.debug("Test Name: %s" %(self._testMethodName))
        global total
        total = total+1
        global result
        result = open("L1_test_results.txt", "a")
        result.write("\n\n%d\t" %total)
        result.write("%s" %(self._testMethodName))
        result.close()

    def test_passed(self):
        logger.debug("Test is Passed...")
        global result
        result = open("L1_test_results.txt", "a")
        result.write("(PASSED)\t")
        result.close()
        global passed
        passed=passed+1

    def test_failed(self, msg):
        logger.debug("Test is Failed...")
        global result
        result = open("L1_test_results.txt", "a")
        if msg:
            result.write("(FAILED) %s" %(msg.split(":")[0]))
        result.close()

    def end_results(self):
       global passed
       global total
       logger.debug("Total Tests Ran= %s" %total)
       logger.debug("Passed = %s" %passed)
       logger.debug("Failed = %s" %(total-passed))
       global result
       result = open("L1_test_results.txt", "r")
       content = result.read()
       result.close()
       result = open("L1_test_results.txt", "w")
       result.write("TEST RESULTS\n")
       result.write("============")
       result.write("\nTOTAL TESTS: %d\n" %(total))
       result.write("PASSED: %d\n" %(passed))
       result.write("FAILED: %d\n" %(total-passed))
       result.write("\nTEST DETAILS")
       result.write("\n============\n")
       result.write(content)
       result.close()
