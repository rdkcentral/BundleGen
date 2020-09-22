# App Metadata Documentation
Each app requires a small metadata file which describes it's specific requirements.

Some application options are defined within the OCI Image, such as the entrypoint command, working directory and environment variables. See [here](https://github.com/opencontainers/image-spec/blob/master/config.md) for more info.

## Options
* `id` (string, REQUIRED). Unique ID for the app. Should be in reverse domain name notation format (e.g `com.rdk.mycoolapp`)
* `type` (string, REQUIRED). The mime-type of the application. **The exact MIME types are subject to change**. Currently, for native DAC apps, use `application/vnd.rdk-app.dac.native`
* `graphics` (boolean, REQUIRED). Set to true if the application requires graphics output
* `network` (object, REQUIRED). Network settings for the application. The object should match the `data` section of the Dobby Networking plugin as defined [here](https://github.com/rdkcentral/Dobby/tree/master/rdkPlugins/Networking/README.md)
* `storage` (object, REQUIRED). 
  * `persistent` (array of objects, REQUIRED). Configure persistent, read/write storage for the application. Each object should have the following options
    * `size` (string, REQUIRED). Amount of storage required
    * `path` (string, REQUIRED). Path where the storage should be mounted inside the container
  * `temp` (array of objects, REQUIRED). Configure temporary, `tmpfs` backed storage for the container. Data stored here will be lost when the container exits. Each object should have the following options
    * `size` (string, REQUIRED). Amount of storage required
    * `path` (string, REQUIRED). Path where the storage should be mounted inside the container
* `resources`
  * `ram` (string, REQUIRED). Amount of RAM required by the container
* `features` (array of strings, OPTIONAL). Any rdkservices/Thunder NanoServices required by the container. If the platform does not support the necessary feature, a bundle cannot be generated
* `mounts` (array of objects, OPTIONAL). Any additional mounts from the host the container requires. Note that these mounts must exist on the platform, otherwise the container will fail to start. Each object in the array should be an OCI `Mount` object as defined [here](https://github.com/opencontainers/runtime-spec/blob/master/config.md#mounts)