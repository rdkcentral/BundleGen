# If not stated otherwise in this file or this component's license file the
# following copyright and licenses apply:
#
# Copyright 2021 Consult Red
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

import os
import shutil
from typing import Tuple
import msgpack

from loguru import logger

from bundlegen.rabbitmq import message
from bundlegen.rabbitmq.result import Result

from bundlegen.core.utils import Utils
from bundlegen.core.bundle_processor import BundleProcessor
from bundlegen.core.image_unpacker import ImageUnpackager
from bundlegen.core.image_downloader import ImageDownloader
from bundlegen.core.stb_platform import STBPlatform


def message_decoder(obj):
    """
    Unpack the received message to a message object
    """
    unpacked_obj = msgpack.unpackb(obj)
    msg = message.Message(unpacked_obj["uuid"],
                          unpacked_obj["platform"],
                          unpacked_obj["image_url"],
                          unpacked_obj["app_metadata"],
                          message.LibMatchMode(unpacked_obj["lib_match_mode"]),
                          unpacked_obj["output_filename"],
                          unpacked_obj["searchpath"],
                          unpacked_obj["outputdir"],
                          unpacked_obj["createmountpoints"],
                          unpacked_obj["app_id"])
    return msg


def msg_received(ch, method, properties, body):
    """
    Callback when we receive a message from the broker. Messages are encoded
    in msgpack format
    """
    logger.debug(f"Received new message - {body}")
    msg = message_decoder(body)

    try:
        result = generate_bundle(msg)

        if result[0] == Result.SUCCESS:
            logger.success(f"Successfully generated bundle at {result[1]}")

            response = {
                'success': True,
                'uuid': msg.uuid,
                'bundle_path': result[1]
            }

            # Send a message on the reply-to exclusive queue to say we've successfully
            # generated a bundle
            ch.basic_publish('', routing_key=properties.reply_to,
                             body=msgpack.packb(response))

            logger.success(f"Request {msg.uuid} completed")

            # ack so rabbit clears it from the queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            response = {
                'success': False,
                'uuid': msg.uuid,
            }

            if method.redelivered:
                # If this is re-delivered message, don't bother requeuing it again and
                # just admit defeat
                logger.error(
                    "Could not generate bundle. Giving up as this was already redelivered")
                # Send a message on the reply-to exclusive queue to say we've failed
                ch.basic_publish('', routing_key=properties.reply_to,
                                 body=msgpack.packb(response))
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            elif result[0] == Result.TRANSIENT_ERROR:
                logger.error(
                    "Could not generate bundle with transient error. Requeuing to try again later")
                # Don't send anything on the reply-to queue here as it'll be retried again
                # by another bundlegen instance
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            elif result[0] == Result.FATAL_ERROR:
                logger.error(
                    "Could not generate bundle with fatal error. Not requeuing")
                ch.basic_publish('', routing_key=properties.reply_to,
                                 body=msgpack.packb(response))
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception:
        logger.exception(
            "Failed to generate Bundle - exception occured. Not requeuing")
        response = {
            'success': False,
            'uuid': msg.uuid,
        }
        ch.basic_publish('', routing_key=properties.reply_to,
                         body=msgpack.packb(response))
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def generate_bundle(options: message.Message) -> Tuple[Result, str]:
    """
    Actually do the work to generate the bundle
    """

    # Create a random dir to save the generated bundle, before copying to output directory
    outputdir = os.path.abspath(os.path.join(
        os.environ.get('BUNDLEGEN_TMP_DIR'), Utils.get_random_string(5)))

    selected_platform = STBPlatform(
        options.platform, options.searchpath or os.environ.get('RDK_PLATFORM_SEARCHPATH'))

    if not selected_platform.found_config():
        logger.error(f"Could not find config for platform {options.platform}")
        return (Result.FATAL_ERROR, "")

    if not options.image_url:
        logger.error("Image URL is not set - cannot generate bundle")
        return (Result.FATAL_ERROR, "")

    logger.success(
        f"Starting Bundle Generation from image '{options.image_url}' for platform {options.platform} (UUID: {options.uuid})")

    creds = os.environ.get("RDK_OCI_REGISTRY_CREDS")
    img_downloader = ImageDownloader()
    img_path = img_downloader.download_image(
        options.image_url, creds, selected_platform.get_config())

    if not img_path:
        logger.error("Failed to download image")
        return (Result.TRANSIENT_ERROR, "")

    # Unpack the image with umoci
    tag = ImageDownloader().get_image_tag(options.image_url)
    img_unpacker = ImageUnpackager(img_path, outputdir)
    img_unpacker.unpack_image(tag, delete=True)

    # Load app metadata
    metadata_from_image = img_unpacker.get_app_metadata_from_img()
    custom_app_metadata = options.app_metadata

    app_metadata_dict = {}
    if not metadata_from_image and not custom_app_metadata:
        # No metadata at all
        logger.error(
            f"Cannot find app metadata file in OCI image and none provided to BundleGen")
        return (Result.FATAL_ERROR, "")

    if not metadata_from_image and custom_app_metadata:
        # Use custom metadata
        app_metadata_dict = custom_app_metadata
    elif metadata_from_image and custom_app_metadata:
        logger.warning("Image contains app metadata and custom metadata provided. Using custom metadata")
        app_metadata_dict = custom_app_metadata
        img_unpacker.delete_img_app_metadata()
    else:
        app_metadata_dict = metadata_from_image
        img_unpacker.delete_img_app_metadata()

    if options.app_id:
        app_metadata_dict['id'] = options.app_id

    # Begin processing. Work in the output dir where the img was unpacked to
    processor = BundleProcessor(
        selected_platform.get_config(),
        outputdir,
        app_metadata_dict,
        False,
        options.lib_match_mode.value,
        options.createmountpoints,
    )

    if not processor.check_compatibility():
        # Not compatible - delete any work done so far
        shutil.rmtree(outputdir)
        logger.error(
            f"App is not compatible with platform {options.platform}, cannot generate bundle")
        return (Result.FATAL_ERROR, "")

    success = processor.begin_processing()
    if not success:
        logger.error("Failed to generate bundle")
        # This might have been some weird issue, so re-queue to try again later
        return (Result.TRANSIENT_ERROR, "")

    if options.output_filename:
        tarball_name = options.output_filename
    else:
        tarball_name = app_metadata_dict["id"] + Utils.get_random_string(6)

    tmp_path = os.path.join(
        os.environ.get('BUNDLEGEN_TMP_DIR'), f"{tarball_name}.tar.gz")
    persistent_path = os.path.join(
        options.outputdir or os.environ.get('BUNDLE_STORE_DIR'), f"{tarball_name}.tar.gz")

    tarball_settings = processor.platform_cfg.get('tarball')
    file_ownership_user = tarball_settings.get('fileOwnershipSameAsUser') if tarball_settings else None
    file_mask = tarball_settings.get('fileMask') if tarball_settings else None

    user = processor.oci_config['process'].get('user')
    uid = user.get('uid') if user and file_ownership_user else None
    gid = user.get('gid') if user and file_ownership_user else None

    Utils.create_tgz(outputdir, tmp_path, uid, gid, file_mask)

    # Move to persistent storage
    logger.debug(
        f"Moving '{tmp_path}' to {options.outputdir or os.environ.get('BUNDLE_STORE_DIR')}")
    shutil.move(tmp_path, options.outputdir or os.environ.get('BUNDLE_STORE_DIR'))

    return (Result.SUCCESS, persistent_path)
