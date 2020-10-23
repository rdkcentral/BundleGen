## Docker
This directory contains a simple Dockerfile for BundleGen, designed to make it quicker to use for app development.

### Usage
1. From inside this directory, build the docker image by running
```console
$ docker-compose build
```
2. Build a DAC OCI image using the meta-dac-sdk. It will produce a `.tar` file of the OCI image
3. Create an app metadata file for your application. See `sample_app_metadata` for examples.
4. Create a template file for your platform. See the `platform` directory for examples
5. Run the following command:
```console
$ ./start.sh <path-to-image> <path-to-platform-template> <path-to-metadata-file>
```

Example:
```console
$ ./start.sh ~/dac-image-wayland-egl-test.tar ./rpi3.json ./wayland-egl-test.json

Starting docker_web_1 ... done
2020-10-23 15:04:33.702 | SUCCESS  | bundlegen.core.image_downloader:download_image:122 - Downloaded image from oci:/image:latest successfully to /tmp/bundlegen/20201023-150433_f161bec6b82546db9ad0710eac211dee
2020-10-23 15:04:34.407 | SUCCESS  | bundlegen.cli.main:generate:132 - Successfully generated bundle at /bundles/dac-image-wayland-egl-test.tar.gz
Done!
Download the OCI bundle at http://localhost:8080/dac-image-wayland-egl-test.tar.gz
```

6. Your image will be available to download from the URL displayed (you will need to change `localhost` to your PCs IP addresses accessible from the STB). You can then install this with Packager and run it with RDKShell by running the following commands:
```console
$ wscat -c ws://$STB_IP_ADDRESS:9998/jsonrpc -s notification -x '{"jsonrpc":"2.0","id":1,"method":"Packager.1.install", "params":{ "pkgId": "mypkgid", "type": "DAC", "url": "<download-url>" } }'
```
```console
$ wscat -c ws://$STB_IP_ADDRESS:9998/jsonrpc -s notification -x '{"jsonrpc":"2.0","id":1,"method":"org.rdk.RDKShell.1.launchApplication", "params":{ "client": "test", "mimeType": "application/dac.native", "uri": "mypkgid" } }'
```

#### Note
To stop the web server, run
```
docker-compose down
```