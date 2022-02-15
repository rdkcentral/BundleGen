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

import sys
import os
import signal
import click
import pika

from time import sleep
from dotenv import load_dotenv, find_dotenv
from loguru import logger
from bundlegen.rabbitmq.message_handler import msg_received


def signal_handler(s, frame):
    """
    Disconnect from rabbitmq and quit when we receive a signal
    """
    logger.debug(f"Received signal {s}")
    logger.info("Shutting down. . .")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)


@click.group()
@click.option('-v', '--verbose', count=True, help='Set logging level')
def cli(verbose):
    """RabbitMQ front-end for BundleGen
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


def create_directory_from_env_var(env_var_name):
    """
    Create any directories we need to work if they don't exist
    """
    dir_path = os.environ.get(env_var_name)

    if not dir_path:
        logger.error(f"Required setting {env_var_name} not set")
        return False

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    return True


@click.command()
def start():
    """
    Starts BundleGen RabbitMQ consumer
    """

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Read settings from a .env file for development
    load_dotenv(find_dotenv())

    # Set up our directories
    if not create_directory_from_env_var("BUNDLE_STORE_DIR"):
        sys.exit(1)
    if not create_directory_from_env_var("BUNDLEGEN_TMP_DIR"):
        sys.exit(1)

    logger.info("Starting RabbitMQ BundleGen consumer. . .")

    successful_connection = False
    max_retry_count = 5
    retry_count = 0

    # Connect to RabbitMQ
    while True:
        try:
            if os.environ.get('RABBITMQ_PORT'):
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST'),
                                              port=os.environ.get('RABBITMQ_PORT'),
                                              connection_attempts=3, retry_delay=1))
            else:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST'),
                                              connection_attempts=3, retry_delay=1))

            channel = connection.channel()

            # will only create if queue doesn't exist
            channel.queue_declare(queue="bundlegen-requests", durable=True)
            channel.basic_consume(queue='bundlegen-requests',
                                  on_message_callback=msg_received)

            successful_connection = True

            logger.success(
                "Connected to RabbitMQ broker. Waiting for messages. . .")

            channel.start_consuming()
        except pika.exceptions.ConnectionClosedByBroker:
            # Don't recover if connection was closed by broker
            logger.error("Connection was closed by broker")
            sys.exit(1)
        except pika.exceptions.AMQPChannelError:
            # Don't recover on channel errors
            logger.error("AMPQ Channel error, cannot recover")
            sys.exit(1)
        except pika.exceptions.AMQPConnectionError:
            # Recover on all other connection errors (assuming we've managed to connect at least once before)
            if successful_connection:
                if retry_count < max_retry_count:
                    logger.warning(
                        f"Lost connection to rabbitmq - attempting to reconnect... ({retry_count}/{max_retry_count})")
                    retry_count += 1
                    sleep(2)
                    continue
                else:
                    logger.error(
                        "Lost connection to rabbitmq - max retries hit, giving up")
                    sys.exit(1)
            else:
                logger.error(
                    f"Cannot connect to rabbitmq at {os.environ.get('RABBITMQ_HOST')}")
                sys.exit(1)


cli.add_command(start)
