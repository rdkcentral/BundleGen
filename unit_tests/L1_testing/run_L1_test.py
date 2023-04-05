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

import argparse
import glob
import os
import sys
import logging

count = 0
test_pass_count = 0
os.chdir('test_files')
parse = argparse.ArgumentParser()
parse.add_argument("-s")
parse.add_argument("-c")
args = parse.parse_args()
if args.s:
    if args.c:
        if args.c != 'coverage_report':
            return_value = 256
            logging.error("--> Given arugument is not matching with 'coverage_report' ")
            logging.debug(" ex: python run_L1_test.py -c 'coverage_report' ")
        else:
            return_value = os.system('python -m coverage erase && python -m coverage run -a --source bundlegen.core test_'+args.s+'_ut.py ')
            os.system('python -m coverage report && python -m coverage html ')
    else:
        return_value = os.system('python test_'+args.s+'_ut.py')

    if ( (return_value >> 8) != 0):
        sys.exit(1)
else:
    files = glob.glob('*.py')
    if args.c:
        #Erasing all the previously stored coverage report
        return_value=os.system('python -m coverage erase')

    for i in files:
        count = count + 1
        if args.c:
            if args.c != 'coverage_report':
                logging.error("--> Given arugument is not matching with 'coverage_report' ")
                logging.debug(" ex: python run_L1_test.py -c 'coverage_report' ")
                sys.exit(1)
            else:
                return_value=os.system('python -m coverage run -a --source bundlegen.core '+i )
                os.system('python -m coverage report && python -m coverage html')
                if return_value == 0:
                    test_pass_count = test_pass_count + 1
        else:
            return_value=os.system('python '+i )
            if return_value == 0:
                test_pass_count = test_pass_count + 1

    if count != test_pass_count:
        sys.exit(1)
