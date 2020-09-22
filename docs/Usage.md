# BundleGen Usage
## Intro
BundleGen is a command-line tool designed to convert OCI images into extended OCI bundles that can be run using the [Dobby](https://github.com/rdkcentral/Dobby) container manager in RDK. The tool is designed to on a cloud platform, off the STB. By using platform and application configurations, BundleGen manipulates the configuration to meet the requirements of a specific platform without needing to actually be run on that platform.

## Basic Usage
To get started with BundleGen, first make sure you have an environment setup as described in the repo README.

Before you can do anything with BundleGen, you need to have an OCI Image containing the application you want to run, uploaded to an OCI registry. The creation of the OCI image is outside the scope of this project. You will also need two JSON files:

* Platform template
  * This describes the platform you want to run the containers on.
  * Sample templates are included in this repo for various platforms including Comcast devices and the Raspberry Pi.
  * The information in this template is used when generating bundles for the platform. 
  * Platform templates should live in the `templates` directory, although an alternative search path for platform files can be set using the `--searchpath` option or `RDK_PLATFORM_SEARCHPATH` environment variable
* Application metadata
  * This describes any specific options an application requires, such as storage, ram and specific bind mounts
  * You should create a metadata file for each application you want to run, and re-use it across all platforms

For this example, we will use the "Hello-World" Docker image (https://hub.docker.com/_/hello-world) and generate a bundle for the Raspberry Pi.

To generate a bundle, use the `generate` command:

```
$ bundlegen generate --platform rpi3 --appmetadata sample_app_metadata/helloworld.json docker://hello-world ~/helloworld_bundle

2020-09-18 12:20:25.183 | SUCCESS  | bundlegen.cli.main:generate:130 - Successfully generated bundle at /home/vagrant/helloworld_bundle.tar.gz
```

Note how the image URL is `docker://hello-world`. Since the image lives on the docker hub, you do not need a full URL to find the image, only the name of the image. This is the same behavior as the `docker pull` command.

If your images reside in a different registry, pass the full URL. For example:
```
docker://us.icr.io/appcontainerstagingrdk/flutter
```

If there is no tag present, bundlegen will download the `latest` tag.


## Other Options
To see all the options available for the generate command, run `bundlegen generate --help`
```
$ bundlegen --help
Usage: bundlegen [OPTIONS] COMMAND [ARGS]...

  Command line tool to generate OCI Bundle*'s from OCI Images for use in RDK

Options:
  -v, --verbose  Set logging level
  --help         Show this message and exit.

Commands:
  generate  Generate an OCI Bundle for a specified platform


$ bundlegen generate --help
Usage: bundlegen generate [OPTIONS] IMAGE OUTPUTDIR

  Generate an OCI Bundle for a specified platform

Options:
  -p, --platform TEXT     Platform name to generate the bundle for  [required]
  -a, --appmetadata TEXT  Path to metadata json for the app (will be embedded
                          in the image itself in future)  [required]

  -s, --searchpath PATH   Where to search for platform templates
  -c, --creds TEXT        Credentials for the registry (username:password).
                          Can be set using RDK_OCI_REGISTRY_CREDS environment
                          variable for security

  --help                  Show this message and exit.
```
