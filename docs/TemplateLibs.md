# Platform Template Libs Documentation
Platform templates define specific information about a platform that is used when generating the container configuration. Next to each template json file a {templatename}_libs.json file can also exist and is parsed when loading the platform template.

This extra json file contains all the dependencies of each .so library. It also contains "apiversion" tags. For example:

    {
        "libs": [
            {
                "apiversions": [
                    "UUID_1.0",
                    "UUID_2.20",
                    "UUIDD_PRIVATE"
                ],
                "name": "lib/libuuid.so.1"
                "deps": [
                    "libc.so.6",
                    "ld-linux-armhf.so.3"
                ]
            },
            {
                "apiversions": [
                    "GLIBC_2.4",
                    "GLIBC_2.5",
                    "GLIBC_2.6",
                    "GLIBC_2.7",
                    .....
                    "GLIBC_2.24",
                    "GLIBC_PRIVATE"
                ],
                "name": "lib/libc.so.6"
                "deps": [
                    "ld-linux-armhf.so.3"
                ]
            }
        ]
    }

## Generating a libs json file

The libs.json file should be auto-generated during the build of the target host/platform. There is a bbclass for this here:
https://code.rdkcentral.com/r/plugins/gitiles/rdk/components/generic/rdk-oe/meta-cmf/+/refs/heads/rdk-next/classes/generate_libs_json.bbclass

The bbclass uses readelf to generate this information. You can enable this generation by adding the following to your image target recipe:
`inherit generate_libs_json`. The result can be found in file $MACHINE_libs.json inside your tmp/deploy dir.

## Uses

The libs.json file serves two main purposes:
1. it is used by BundleGenerator to determine the dependencies of libraries which should be mount bound to the host. All libs inside `gfxLibs` are considered as the "graphics contract" with the host or target platform. They are always mount bound since their implementation is host specific. However, the dependencies of these libraries can be either mount bound to the host or taken from the OCI image. All libraries listed under `pluginDependencies` are not considered "contract" and can be mount bound to the host or taken from the OCI image.
2. the second purpose is to help decide which (host or OCI image) library to take. For this the BundleGenerator looks at the API tags under apiversions. Sadly only a limited amount of libraries provide a proper set of such tags. In case of libc it can be used to find the newest version i.e. the version implementing the most API tags.

## Options

The automatic dependency walking and adding of libs can be disabled by passing argument `-n, --nodepwalking`. So by default it is enabled. The feature is also disabled when no such libs.json file is available. In such a case you should probably make sure that:
1. either you add such dependencies manually to `gfxLibs` or `pluginDependencies`
2. or you make sure these dependencies are already inside the OCI image

You can also influence the choice that BundleGenerator makes to take host or OCI image libraries by passing parameter `-m, --libmatchingmode [normal|image|host]`. This does not incluence the libs directly listed under `gfxLibs`, because they are always mount bound to host.
1. normal: take most recent library i.e. with most api tags like 'GLIBC_2.4'.
2. image: always take lib from OCI image rootfs, if available in there.
3. host: always take host lib and create mount bind. Skips the library from OCI image rootfs if it was there.
Default mode is 'normal'. When apiversion info is not available the effect is the same as mode 'host'