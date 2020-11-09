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
import json
import click
from loguru import logger


class STBPlatform:
    def __init__(self, name, search_path=None):
        self.name = name

        # Default to looking in the source code templates directory
        if not search_path:
            self.search_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), os.pardir, os.pardir, 'templates'))
        else:
            self.search_path = search_path

        # Find config files for the platform
        self.search_config()

        # Parse the configs we just found
        if self.found_config():
            self.parse_config()

    # ==========================================================================
    def search_config(self):
        """Search for a config file for the specified platform

        Config files should live in the templates directory or a custom directory
        """
        # Loop through all the dirs, looking for a <platformname>.json and
        # <platformname>_libs.json file
        config_files = []

        for subdir, dirs, files in os.walk(self.search_path):
            for file in files:
                if (self.name + ".json" in file) or (self.name + "_libs.json" in file):
                    # Found a suitable config file
                    config_path = os.path.join(subdir, file)
                    config_files.append(config_path)

                    logger.debug(f"Found platform config {config_path}")

        self.config_files = config_files

    # ==========================================================================
    def parse_config(self):
        """Parse the platform config files into a python dictionary
        """
        dictionary_list = []

        # Load all the config files
        for file in self.config_files:
            with open(file) as jsonFile:
                data = json.load(jsonFile)
                dictionary_list.append(data)

        # Merge all the config files into one dictionary
        self.config = {}
        for dict in dictionary_list:
            self.config.update(dict)

    # ==========================================================================
    def found_config(self):
        """Returns true if at least one config file was found for the platform

        Returns:
            bool: True if at least one config found
        """
        return len(self.config_files) > 0

    def get_config(self):
        """Returns the config dictionary for the platform

        Returns:
            dictionary: the config dictionary for the platform
        """
        return self.config
