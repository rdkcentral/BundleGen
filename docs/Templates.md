# Platform Template Documentation
Platform templates define specific information about a platform that is used when generating the container configuration.

## Options
* `platformName` (string, REQUIRED). Specifies the name of the platform
* `os` (string, REQUIRED). Specifies the OS of the platform
  * Supported options include linux or windows
* `arch`
  * `arch` (string, REQUIRED). Specifies the CPU architecture.
    * OCI images can contain multiple variants of an application, compiled for different architectures
    * Supported values are listed in the Go language document for [`GOARCH`](https://golang.org/doc/install/source#environment):
  * `variant` (string, OPTIONAL). The variant of the CPU, if applicable. Supported architecture/variant combinations are:
    
    |    ISA/ABI     | architecture | variant |
    | :------------: | :----------: | :-----: |
    | ARM 32-bit, v6 |    `arm`     |  `v6`   |
    | ARM 32-bit, v7 |    `arm`     |  `v7`   |
    | ARM 32-bit, v8 |    `arm`     |  `v8`   |
    | ARM 64-bit, v8 |   `arm64`    |  `v8`   |
* `rdk`
  * `version` (string, REQUIRED). Version of RDK installed on the platform
  * `supportedFeatures` (array of strings, REQUIRED). Which RDK services/Thunder NanoServices are installed and available on the platform. Images that require features not present on the platform cannot be converted to OCI bundles
* `hardware`
  * `graphics` (boolean, REQUIRED). Whether the platform supports graphics output or not (e.g. on a headless developement VM)
  * `maxRAM` (string, REQUIRED). The maximum amount of RAM an application can use. If an application requires more RAM, a warning will be shown during bundle generation.
* `storage`
  * `persistent` (object, OPTIONAL) Dobby supports persistent storage using loopback mounts. If the platform should not support loopback mounts, do not define this section
    * `storageDir` (string, REQUIRED). Where to store the `img` files that are mounted into the container
    * `maxSize` (string, REQUIRED). Maximum allowed size of the image files
* `gpu`
  * `westeros` (object, OPTIONAL). If the platform uses a hard-coded path to a westeros socket, then set it here. If RDKShell is used to create displays, then a westeros socket path can be provided to Dobby dynamically when starting the container and this option can be excluded
    * `hostSocket` (string, OPTIONAL). Path to the hard-coded westeros socket on the host
  * `extraMounts` (array, OPTIONAL) Array of *mount* objects that will be added to the config to allow mounting specific graphics sockets or other files into a container. Each mount object should be an OCI `Mount` object as defined [here](https://github.com/opencontainers/runtime-spec/blob/master/config.md#mounts)
  * `envvar` (array of strings, OPTIONAL). Any environment variables needed for graphics to work correctly on the platform
  * `devs` (array of objects, OPTIONAL). Any devices to whitelist and make available within the container. Each item in the array should be an OCI `Device` object as defined [here](https://github.com/opencontainers/runtime-spec/blob/master/config-linux.md#devices)
  * `gfxLibs` (array of objects, REQUIRED). Array of graphics libraries that are platform-specific and should be bind-mounted into the container.
    * Note that any libraries listed here will override any that ship inside the container image. Applications should use wayland for graphics output, and should include the version of `wayland-client` they require.
    * It is possible to bind mount the same library multiple times into a container with different names.
    * Each item in the array should have two properties:
      * `src` (string, REQUIRED). Path to the library on the host
      * `dst` (string, REQUIRED). Mount destination inside the container
* `mounts` (array of mount objects, OPTIONAL). Any extra mounts that should be added to the config. Can be left empty if no mounts needed. Each item in the array should be an OCI `Mount` object as defined [here](https://github.com/opencontainers/runtime-spec/blob/master/config.md#mounts)
* `network` (array of string, REQUIRED). Which network modes the platform supports and an application could use. Dobby's Networking plugin offers `nat`, `private` and `open` network options by default.
* `envvar` (array of string, OPTIONAL). Any additional environment variables that should be set on all containers running on the platform
* `resourceLimits` (array of objects, OPTIONAL). Any specific resource limits that should be applied to the container. The sample templates have two recommended limits, but you can set them on a per-platform need. Each item in the array should have the following properties:
  * `type` (string, REQUIRED). The platform resource being limited. See [getrlimit(2)](https://man7.org/linux/man-pages/man2/getrlimit.2.html) for supported options
  * `soft` (uint64, REQUIRED) the value of the limit enforced for the corresponding resource
  * `hard` (uint64, REQUIRED) the ceiling for the soft limit that could be set by an unprivileged process
* `disableUserNamespacing` (boolean, OPTIONAL). Set to true to disable user namespace support on the platform. Containers will run as the same user that Dobby is running as (usually root)
* `usersAndGroups` (object, REQUIRED if `disableUserNamespacing` is set to `false`). When using user namespacing, you must map users from the host system into the container. See [`user_namespaces(7)`](https://www.man7.org/linux/man-pages/man7/user_namespaces.7.html) for more info on uid_map and gid_map
  * `uidMap` (array of objects, REQUIRED).
  * `gidMap` (array of objects, REQUIRED).
    * Both `uidMap` and `gidMap` are arrays of objects with the following properties:
      * `containerID` (uint32, REQUIRED) - is the starting uid/gid in the container.
      * `hostID` (uint32, REQUIRED) - is the starting uid/gid on the host to be mapped to containerID.
      * `size` (uint32, REQUIRED) - is the number of ids to be mapped.
* `logging`
  * `mode` (string, REQUIRED). Sets the logging sink for containers. Dobby by default supports the following logging modes:
    * `file` - log to a file
    * `journald` - log to journald
    * `devnull` - log to /dev/null (i.e. don't store container logs)
  * `logDir` (string, REQUIRED if `mode` is set to `file`). Directory to store container logs if logging to file
* `dobby`
  * `pluginDir` (string, REQUIRED). Location where Dobby plugins are found on the platform. Dobby plugins are by default found in `/usr/lib/plugins/dobby`
  * `pluginDependencies` (array of strings, REQUIRED. Libraries that the Dobby plugins depend on.
    * Dobby plugins are shared objects and have dependencies that must exist in the container. THe exact dependencies needed will depend on which plugins are being used on the platform. To find dependencies, run `/lib/ld-linux-armhf.so.3 --list /usr/lib/plugins/dobby/ <plugin-name>` on the platform for each plugin