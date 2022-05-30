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
  * `graphics` (boolean, REQUIRED). Whether the platform supports graphics output or not (e.g. on a headless development VM)
  * `maxRAM` (string, REQUIRED). The maximum amount of RAM an application can use. If an application requires more RAM, a warning will be shown during bundle generation.
* `storage`
  * `persistent` (object, OPTIONAL) Dobby supports persistent storage using loopback mounts. If the platform should not support loopback mounts, do not define this section
    * `storageDir` (string, REQUIRED). Where to store the `img` files that are mounted into the container
    * `maxSize` (string, OPTIONAL). Maximum allowed size of the image files
    * `minSize` (string, OPTIONAL). Minimum required size of the image files. Some filesystem types need a minimum size. When set, the size of a storage will be auto increased to match this minium. This is logged as a warning.
    * `fstype` (string, OPTIONAL). Filesystem type to use like ext4 or xfs. Defaults to ext4.
    * `maxTotalSize` (string, OPTIONAL). Maximum allowed **total** size of the image files
  * `temp` (object, OPTIONAL) Dobby supports temporary storages using tmpfs.
    * `maxSize` (string, OPTIONAL). Maximum allowed size of the temporary storage
    * `minSize` (string, OPTIONAL). Minimum required size of the temporary storage. When set, the size of a storage will be auto increased to match this minium. This is logged as a warning.
    * `maxTotalSize` (string, OPTIONAL). Maximum allowed **total** size of the temporary storages
* `gpu`
  * `westeros` (object, OPTIONAL). If the platform uses a hard-coded path to a westeros socket, then set it here. If RDKShell is used to create displays, then a westeros socket path can be provided to Dobby dynamically when starting the container and this option can be excluded
    * `hostSocket` (string, OPTIONAL). Path to the hard-coded westeros socket on the host
  * `extraMounts` (array, OPTIONAL) Array of *mount* objects that will be added to the config to allow mounting specific graphics sockets or other files into a container. Each mount object should be an OCI `Mount` object as defined [here](https://github.com/opencontainers/runtime-spec/blob/master/config.md#mounts). Use `X-dobby.optional` to make the mount optional.
  * `envvar` (array of strings, OPTIONAL). Any environment variables needed for graphics to work correctly on the platform
  * `devs` (array of objects, OPTIONAL). Any devices to whitelist and make available within the container. Each item in the array should be an OCI `Device` object as defined [here](https://github.com/opencontainers/runtime-spec/blob/master/config-linux.md#devices). Additionally you can set a device to be `dynamic` (boolan, OPTIONAL). When this boolean is true, the devicemapper plugin will be added to the generated config. It will trigger Dobby to assign the correct major/minor numbers when starting the container. This is handy for devices with dynamically assigned major/minor numbers on boot.
  * `gfxLibs` (array of objects, REQUIRED). Array of graphics libraries that are platform-specific and should be bind-mounted into the container.
    * Note that any libraries listed here will override any that ship inside the container image. Applications should use wayland for graphics output, and should include the version of `wayland-client` they require.
    * It is possible to bind mount the same library multiple times into a container with different names.
    * Each item in the array should have two properties:
      * `src` (string, REQUIRED). Path to the library on the host
      * `dst` (string, REQUIRED). Mount destination inside the container
  * `waylandDisplay` (string, OPTIONAL). Wayland compositor, by default set to 'westeros'.
* `root` (OPTIONAL)
  * `path` (string, OPTIONAL). If set override the default rootfs path. In addition this path can include the {id} parameter which will be replaced by the id of the app as indicated in the app metadata. This allows BundleGen to generate the full rootfs path as it will exist on the target platform. For example: /somewhere/run/rootfs/{id}
  * `readonly` (boolean, OPTIONAL). Set to true to mark the rootfs readonly.
* `hostname` (string, OPTIONAL). If set, override the default hostname. In addition this hostname can include the {id} parameter which will be replaced by the id of the app as indicated in the app metadata.
* `mounts` (array of mount objects, OPTIONAL). Any extra mounts that should be added to the config. Can be left empty if no mounts needed. Each item in the array should be an OCI `Mount` object as defined [here](https://github.com/opencontainers/runtime-spec/blob/master/config.md#mounts). Use `X-dobby.optional` to make the mount optional.
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
  * `user` (object, OPTIONAL). Here you can specify what user to run the container under. You can also specify its gid and additional gids.
    * `uid` (uint32, OPTIONAL). Override the uid and thus the user the container should run under.
    * `gid` (uint32, OPTIONAL). Override the gid and thus the user's group the container should run under.
    * `additionalGids` (array of uint32, OPTIONAL). Set the additional groups that should be assigned to the user running the container.
* `logging`
  * `mode` (string, REQUIRED). Sets the logging sink for containers. Dobby by default supports the following logging modes:
    * `file` - log to a file
    * `journald` - log to journald
    * `devnull` - log to /dev/null (i.e. don't store container logs)
  * `logDir` (string, REQUIRED if `mode` is set to `file`). Directory to store container logs if logging to file
* `dobby`
  * `pluginDir` (string, REQUIRED). Location where Dobby plugins are found on the platform. Dobby plugins are by default found in `/usr/lib/plugins/dobby`
  * `pluginDependencies` (array of strings, REQUIRED. Libraries that the Dobby plugins depend on.
    * Dobby plugins are shared objects and have dependencies that must exist in the container. The exact dependencies needed will depend on which plugins are being used on the platform. To find dependencies, run `/lib/ld-linux-armhf.so.3 --list /usr/lib/plugins/dobby/ <plugin-name>` on the platform for each plugin
  * `dobbyInitPath` (string, OPTIONAL). Location where DobbyInit is found on the platform. DobbyInit is by default found in `/usr/libexec/DobbyInit`
  * `generateCompliantConfig` (boolean, OPTIONAL). When set BundleGen will generate the DobbyPluginLauncher hooks (if any plugins are used). This will also set "ociVersion" to "1.0.2" and not "1.0.2-dobby" so that Dobby does not generate these hooks.
  * `hookLauncherExecutablePath` (string, OPTIONAL, only used when generateCompliantConfig is true). Path to the DobbyPluginLauncher binary on the target host. Defaults to "/usr/bin/DobbyPluginLauncher"
  * `hookLauncherParametersPath` (string, REQUIRED if generateCompliantConfig is true). Path in the host that will contain the config.json of the container. It can include the {id} parameter which will be replaced by the id of the app as indicated in the app metadata. For example "/somewhere/{id}"
* `tarball` (OPTIONAL)
  * `fileOwnershipSameAsUser` (boolean, OPTIONAL). If true then file ownership will be set to match uid/gid of the user that will run inside the container. This uid/gid is set while creating the tarball (inside the tarball only).
  * `fileMask` (string, OPTIONAL). If set, this mask will be applied on the file permissions of every file and dir inside the tarball. This happens while creating the tarball (inside the tarball only). This mask string will be parsed as an octal number. For example "770" will remove all 'rwx' rights for 'other' users.