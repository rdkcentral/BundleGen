# OCI Bundle Generator
RDK Component to generate extended OCI bundle*'s from OCI Images, ready to be run by Dobby

## Environment Setup
You will need Python >=3.7 installed and configured. You will also require some project specific dependencies and OCI tools.

A Fedora 32 `Vagrantfile` is included to provide a ready-to-use environment. Otherwise follow the steps later in this document
to set up your own Fedora/Ubuntu environment.

Once you have an environment setup, follow the below Quick Start instructions

## Quick Start
```
git clone git@github.com:rdkcentral/BundleGen.git
cd bundlegen
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install --editable .
bundlegen generate --platform <platform-name> --appmetadata <path-to-app-metadata> <img-url> <output-dir>
```
Note the image URL should be in the form `docker://image-url`. If the image is on the Docker Hub, the full URL can be omitted - e.g `docker://hello-world`.

See the `docs` directory for more detailed documentation

## Development
*These steps only apply if you're not using the included Vagrantfile*

For development, you will need Python >=3.7 installed and configured. Once installed, then install project specific dependencies.

### Fedora 32
It's easier to work in Fedora as the OCI tooling is already available
```bash
# Install dependencies
$ sudo dnf upgrade -y
$ sudo dnf install -y make git skopeo go go-md2man
# Install Go
$ mkdir -p $HOME/go
$ echo 'export GOPATH=$HOME/go' >> $HOME/.bashrc
$ source $HOME/.bashrc
# Build/install umoci
$ go get -d github.com/opencontainers/umoci
$ cd $GOPATH/src/github.com/opencontainers/umoci/
$ make
$ sudo make install
```

### Ubuntu >=18.04
It's also possible to build on Ubuntu.
Note Skopeo only publishes packages for Ubuntu 18.04 or newer. It may be possible to build skopeo from source on older distributions, see https://github.com/containers/skopeo/blob/master/install.md

```bash
# Install dependencies
$ sudo apt update
$ sudo apt upgrade
$ sudo apt install -y make git go-md2man
# Install Go 1.13
$ wget https://dl.google.com/go/go1.13.12.linux-amd64.tar.gz
$ tar -xvf go1.13.12.linux-amd64.tar.gz
$ sudo mv go /usr/local
$ mkdir -p $HOME/go
$ echo 'export GOPATH=$HOME/go' >> $HOME/.bashrc
$ echo 'export GOROOT=/usr/local/go' >> $HOME/.bashrc
$ echo 'export PATH=$GOPATH/bin:$GOROOT/bin:$PATH' >> $HOME/.bashrc
$ source $HOME/.bashrc
# Build/install umoci
$ go get -d github.com/opencontainers/umoci
$ cd $GOPATH/src/github.com/opencontainers/umoci/
$ make
$ sudo make install
# Install skopeo
$ . /etc/os-release
$ sudo sh -c "echo 'deb http://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/x${NAME}_${VERSION_ID}/ /' > /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list"
$ wget -nv https://download.opensuse.org/repositories/devel:kubic:libcontainers:stable/x${NAME}_${VERSION_ID}/Release.key -O- | sudo apt-key add -
$ sudo apt update && sudo apt install skopeo
```

---
# Copyright and license
If not stated otherwise in this file or this component's LICENSE file the following copyright and licenses apply:

Copyright 2020 Consult Red

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.