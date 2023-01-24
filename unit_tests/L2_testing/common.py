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

#Description : To retrieve the name of the directory and adding "cases" to the directory.

import sys
import unittest
import os

def setup_sys_path():
    directory = os.path.dirname(os.path.abspath(__file__))
class TestBase(unittest.TestCase):
    def setUp(self):
        directory = os.path.dirname(os.path.abspath(__file__))
        self.cases_path = os.path.join(directory, 'cases')
