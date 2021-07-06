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

def get_default_caps():
    """
    Returns a default set of capabilities that are applied by default. This
    is a very minimal set designed to allow most applications to work out of the
    box

    It is recommended that you override this list with a platform specific set
    of capabilities

    References:
    * https://www.redhat.com/en/blog/secure-your-containers-one-weird-trick
    * https://github.com/moby/moby/blob/46cdcd206c56172b95ba5c77b827a722dab426c5/oci/caps/defaults.go (Docker default set)
    """
    return [
        "CAP_CHOWN",
        "CAP_FSETID",
        "CAP_NET_RAW",
        "CAP_SETGID",
        "CAP_SETUID",
        "CAP_SETPCAP",
        "CAP_NET_BIND_SERVICE",
        "CAP_KILL",
        "CAP_AUDIT_WRITE"
    ]
