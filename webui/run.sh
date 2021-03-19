#!/bin/bash
docker build -t bundlegen-webui . && \
docker run --network=host -v bundles:/bundlestore bundlegen-webui
