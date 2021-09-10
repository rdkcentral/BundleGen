# If not stated otherwise in this file or this component's license file the
# following copyright and licenses apply:
#
# Copyright 2021 Consult Red
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

from enum import Enum


class LibMatchMode(str, Enum):
    """
    Defines which strategy to use for selecting which libraries to bind-mount
    into the container
    """
    NORMAL = "normal"
    IMAGE = "image"
    HOST = "host"


class Message():
    """
    Message to be send/received over rabbitmq
    """

    def __init__(self,
                 uuid: str,
                 platform: str,
                 image_url: str,
                 app_metadata: dict,
                 lib_match_mode: LibMatchMode,
                 output_filename: str,
                 searchpath: str,
                 outputdir: str,
                 createmountpoints: bool):
        self.uuid = uuid
        self.platform = platform
        self.image_url = image_url
        self.output_filename = output_filename
        self.searchpath = searchpath
        self.outputdir = outputdir
        self.createmountpoints = createmountpoints

        if app_metadata is None:
            self.app_metadata = {}
        else:
            self.app_metadata = app_metadata
        self.lib_match_mode = lib_match_mode
