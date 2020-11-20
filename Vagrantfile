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

# Vagrantfile to configure a VirtualBox VM that can be used for BundleGen Development

Vagrant.configure("2") do |config|
    # Fedora
    config.vm.box = "fedora/32-cloud-base"

    config.vm.hostname = "bundlegen"
    config.vm.define "bundlegen"

    config.vm.network :forwarded_port, guest: 22, host: 2200, id: "ssh"

    config.vagrant.plugins = "vagrant-vbguest"

    config.vm.provider "virtualbox" do |vb|
        vb.memory = "2048" # Change this to reduce the amount of RAM assigned to the VM
        vb.cpus = "4"   # Change this to reduce the amount of cores assigned to the VM
        vb.customize ["modifyvm", :id, "--ioapic", "on", "--vram", "100", "--graphicscontroller", "vmsvga", "--audio", "none"]
    end

    # Forward SSH keys from host
    config.ssh.forward_agent = true

    # Copy host gitconfig
    config.vm.provision "file", source: "~/.gitconfig", destination: ".gitconfig"
    config.vm.provision "file", source: "~/.ssh", destination: "$HOME/.ssh"

    # Root tasks
    config.vm.provision "shell", inline: <<-SHELL
        dnf upgrade -y
        dnf install -y make vim jq git skopeo go go-md2man
    SHELL

    config.vm.provision "shell", privileged: false, inline: <<-SHELL
        # Configure Go
        mkdir -p $HOME/go
        echo 'export GOPATH=$HOME/go' >> $HOME/.bashrc
        source $HOME/.bashrc

        # Install umoci
        go get -d github.com/opencontainers/umoci
        cd $GOPATH/src/github.com/opencontainers/umoci/
        make
        sudo make install

        # Clone BundleGen repo and install bundlegen
        cd ~
        git clone git@github.com:rdkcentral/BundleGen.git bundlegen
        cd bundlegen
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        pip install --editable .
    SHELL

end
