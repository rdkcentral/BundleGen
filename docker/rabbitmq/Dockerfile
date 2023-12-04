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

FROM fedora:latest

# Install dependencies
RUN dnf upgrade -y && \
    dnf install -y sudo make vim jq git skopeo go go-md2man python3-pip

# Add a user
RUN adduser bundlegenuser && \
    echo "bundlegenuser ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/user && \
    chmod 0440 /etc/sudoers.d/user

# This should be backed by a volume...
RUN mkdir /bundles && chown bundlegenuser:bundlegenuser /bundles
VOLUME /bundles

USER bundlegenuser
WORKDIR /home/bundlegenuser

# Configure Go and setup Umoci
RUN mkdir -p $HOME/go && \
    echo 'export GOPATH=$HOME/go' >> $HOME/.bashrc && \
    echo 'export GO111MODULE=off' >> $HOME/.bashrc && \
    source $HOME/.bashrc && \
    go get -d github.com/opencontainers/umoci && \
    cd $GOPATH/src/github.com/opencontainers/umoci && \
    make && \
    sudo make install

# Install BundleGen from source
ADD . ./bundlegen
RUN cd ./bundlegen && \
    sudo pip3 install -r requirements.txt && \
    sudo pip3 install --editable .


WORKDIR /home/bundlegenuser/bundlegen

# Start BundleGen consumer
ENTRYPOINT [ "./entrypoint.sh" ]
