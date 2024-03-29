FROM fedora:latest

# Install dependencies
RUN dnf upgrade -y && \
    dnf install -y sudo make vim jq git skopeo go go-md2man python3-pip

# Add a user
RUN adduser bundlegenuser && \
    echo "bundlegenuser ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/user && \
    chmod 0440 /etc/sudoers.d/user

RUN mkdir /bundles && chmod 777 /bundles

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

# Install BundleGen
RUN git clone https://github.com/rdkcentral/BundleGen.git && \
    cd ./BundleGen && \
    sudo pip3 install -r requirements.txt && \
    sudo pip3 install --editable .


WORKDIR /home/bundlegenuser/BundleGen

ENTRYPOINT [ "bundlegen" ]
