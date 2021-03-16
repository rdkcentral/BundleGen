FROM fedora:latest

EXPOSE 5000/tcp

# Install dependencies
RUN dnf upgrade -y && \
    dnf install -y sudo make vim jq git skopeo go go-md2man python3-pip

# Add a user
RUN adduser bundlegenuser && \
    echo "bundlegenuser ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/user && \
    chmod 0440 /etc/sudoers.d/user

USER bundlegenuser
WORKDIR /home/bundlegenuser

# Configure Go and setup Umoci
RUN mkdir -p $HOME/go && \
    echo 'export GOPATH=$HOME/go' >> $HOME/.bashrc && \
    source $HOME/.bashrc && \
    go get -d github.com/opencontainers/umoci && \
    cd $GOPATH/src/github.com/opencontainers/umoci && \
    make && \
    sudo make install

# Install BundleGen
RUN git clone https://github.com/rdkcentral/BundleGen.git && \
    cd BundleGen/webui && \
    pip3 install --user -r requirements.txt && \
    cd .. && \
    pip3 install --user --editable .

COPY --chown=bundlegenuser:bundlegenuser ./entrypoint.sh /
RUN chmod +x /entrypoint.sh

WORKDIR /home/bundlegenuser/BundleGen/webui

ENTRYPOINT [ "/entrypoint.sh" ]
