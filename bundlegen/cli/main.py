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

import click
import sys
import json
import os
import shutil

from loguru import logger
from bundlegen.core.stb_platform import STBPlatform
from bundlegen.core.image_downloader import ImageDownloader
from bundlegen.core.image_unpacker import ImageUnpackager
from bundlegen.core.bundle_processor import BundleProcessor
from bundlegen.core.utils import Utils


@click.group()
@click.option('-v', '--verbose', count=True, help='Set logging level')
def cli(verbose):
    """Command line tool to generate OCI Bundle*'s from OCI Images for use in RDK
    """
    # Set up logging
    logger.remove()

    if verbose > 3:
        verbose = 3

    log_levels = {
        0: 'SUCCESS',
        1: 'INFO',
        2: 'DEBUG',
        3: 'TRACE'
    }

    logger.add(sys.stderr, level=log_levels.get(verbose))


@click.command()
@click.argument('image')
@click.argument('outputdir', type=click.Path())
@click.option('-p', '--platform', required=True, help='Platform name to generate the bundle for', envvar='RDK_PLATFORM')
@click.option('-s', '--searchpath', required=False, help='Where to search for platform templates', envvar="RDK_PLATFORM_SEARCHPATH", type=click.Path())
@click.option('-c', '--creds', required=False, help='Credentials for the registry (username:password). Can be set using RDK_OCI_REGISTRY_CREDS environment variable for security', envvar="RDK_OCI_REGISTRY_CREDS")
@click.option('-i', '--ipk', required=False, help='If set result file will be "*.ipk" instead of "*.tar.gz"', envvar="FILE_FORMAT_IPK", is_flag=True)
@click.option('-a', '--appmetadata', required=False, help='Path to metadata json for the app (if not embedded inside OCI image)')
@click.option('-y', '--yes', help='Automatic yes to prompt', is_flag=True)
@click.option('-n', '--nodepwalking',
              help="""Dependency walking and library matching is active by default. Use this flag to disable it.
                                When enabled, the dependencies of all libs indicated in gfxLibs and pluginDependencies config,
                                will automatically also be added to the bundle. Host or OCI image version of library is decided by libmatchingmode
                                parameter below. This logic can only work if a _libs.json file is present with libs and apiversions info.""", is_flag=True)
@click.option('-m', '--libmatchingmode', type=click.Choice(['normal', 'image', 'host'], case_sensitive=True), default='normal',
              help=""" normal: take most recent library i.e. with most api tags like 'GLIBC_2.4'.\n
                                  image: always take lib from OCI image rootfs, if available in there.\n
                                  host: always take host lib and create mount bind. Skips the library from OCI image rootfs if it was there.\n
                                  Default mode is 'normal'. When apiversion info not available the effect is the same as mode 'host'""")
@click.option('-r', '--createmountpoints', required=False, help='Create mount points in rootfs. Main usage for platforms with RO filesystem.', is_flag=True)
@click.option('-x', '--appid', required=False, help='Optional. Application id. Can be used to override the id inside the metadata.')
@click.option('-u', '--crun', required=False, help='crun compatible bundle without Dobby', is_flag=True)
# @click.option('--disable-lib-mounts', required=False, help='Disable automatically bind mounting in libraries that exist on the STB. May increase bundle size', is_flag=True)
def generate(image, outputdir, platform, searchpath, creds, ipk, appmetadata, yes, nodepwalking, libmatchingmode, createmountpoints, appid, crun):
    """Generate an OCI Bundle for a specified platform
    """

    logger.info(f'Generating new OCI bundle* from {image} for {platform}')

    outputdir = os.path.abspath(outputdir)

    # Check if the output dir already exists
    if os.path.exists(outputdir):
        if not yes:
            click.confirm(
                f"The directory {outputdir} already exists. Are you sure you want to continue? The contents of this directory will be deleted", abort=True)

        # Delete existing directory
        shutil.rmtree(outputdir)

    # Load the config for the platform
    selected_platform = STBPlatform(platform, searchpath)

    if not selected_platform.found_config():
        logger.error(f"Could not find config for platform {platform}")
        sys.exit(1)

    # Validate platform config with JSON schema
    success = selected_platform.validate_platform_config()
    if not success:
        logger.error("Validation of platform config FAILED with schema")
        sys.exit(1)

    # Download the image to a temp directory
    img_downloader = ImageDownloader()
    img_path = img_downloader.download_image(
        image, creds, selected_platform.get_config())

    if not img_path:
        sys.exit(1)

    # Unpack the image with umoci
    tag = ImageDownloader().get_image_tag(image)
    img_unpacker = ImageUnpackager(src=img_path, dst=outputdir)
    unpack_success = img_unpacker.unpack_image(tag, delete=True)

    if not unpack_success:
        sys.exit(1)

    # Load app metadata
    metadata_from_image = img_unpacker.get_app_metadata_from_img()
    appmetadata = os.path.abspath(appmetadata) if appmetadata else None

    app_metadata_dict = {}
    if appmetadata:
        # If Appmetadata is specified in /unittest/L2_testing choosing that appmetadata.
        if not os.path.exists(appmetadata):
            logger.error(f'App metadata file {appmetadata} does not exist')
            sys.exit(1)
        else:
            with open(appmetadata) as metadata:
                logger.debug(f"Loading metadata from {appmetadata}")
                app_metadata_dict = json.load(metadata)
    elif metadata_from_image:
        # If Appmetadata is not specified, taking from oci image.
        app_metadata_dict = metadata_from_image
        img_unpacker.delete_img_app_metadata()
    else:
        # No metadata at all
        logger.error(
            f"Cannot find app metadata file in OCI image and none provided to BundleGen")
        sys.exit(1)

    if appid:
         app_metadata_dict['id'] = appid

    # Begin processing. Work in the output dir where the img was unpacked to
    processor = BundleProcessor(
        selected_platform.get_config(), outputdir, app_metadata_dict, nodepwalking, libmatchingmode, createmountpoints, crun)
    if processor == False:
        sys.exit(1)

    if not processor.check_compatibility():
        # Not compatible - delete any work done so far
        shutil.rmtree(outputdir)
        sys.exit(2)

    success = processor.validate_app_metadata_config()
    if not success:
        logger.error("Validation of app metadata FAILED with schema")
        sys.exit(1)

    success = processor.begin_processing()

    if not success:
        logger.warning("Failed to produce bundle")
        sys.exit(3)

    # Processing finished, now create a tarball/ipk of the output directory
    if ipk:
        # create control file
        Utils.create_control_file(
            selected_platform.get_config(), app_metadata_dict)
        Utils.create_ipk(outputdir, outputdir)
        logger.success(f"Successfully generated bundle at {outputdir}.ipk")
    else:
        tarball_settings = processor.platform_cfg.get('tarball')
        file_ownership_user = tarball_settings.get('fileOwnershipSameAsUser') if tarball_settings else None
        file_mask = tarball_settings.get('fileMask') if tarball_settings else None

        container_uid_gid = processor.get_real_uid_gid()

        uid = container_uid_gid[0] if container_uid_gid[0] and file_ownership_user else None
        gid = container_uid_gid[1] if container_uid_gid[1] and file_ownership_user else None

        Utils.create_tgz(outputdir, outputdir, uid, gid, file_mask)
        logger.success(f"Successfully generated bundle at {outputdir}.tar.gz")


cli.add_command(generate)
