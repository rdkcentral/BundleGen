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

import pika
import sys
import os
import msgpack
import uuid
import pprint

from loguru import logger

from bundlegen.rabbitmq import message


def msg_received(ch, method, properties, body):
    # We've received a message back from BundleGen

    msg = msgpack.unpackb(body)
    id = msg["uuid"]
    if msg["success"]:
        # Where did BundleGen save the bundle?
        bundle = msg["bundle_path"]
        logger.success(
            f"Request {id} has been completed successfully. Bundle stored in {bundle}")
        sys.exit(0)
    else:
        logger.error(f"Request {id} has failed")
        sys.exit(1)


def main():
    # Setup logger
    logger.info("Starting. . .")

    # Connect to rabbitmq
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # will only create if queue doesn't exist
    channel.queue_declare(queue="bundlegen-requests", durable=True)

    # "magic" queue that means bundlegen can reply when it's finished with the
    # path to the bundle (or an error message). The queue is automatically
    # destroyed
    channel.basic_consume(queue='amq.rabbitmq.reply-to',
                          on_message_callback=msg_received,
                          auto_ack=True)

    # Hello-world image doesn't contain any metadata, so we'll pass it to BundleGen
    # ourselves
    metadata = {
        "id": "com.docker.helloworld",
        "type": "application/vnd.rdk-app.dac.native",
        "graphics": False,
        "network": {
            "type": "open"
        },
        "storage": {
            "persistent": [],
            "temp": []
        },
        "resources": {
            "ram": "50M"
        },
        "features": [],
        "mounts": []
    }

    # Each request to BundleGen should have a UUID so that the sender can match
    # up requests/responses
    uuid_str = str(uuid.uuid4())

    msg = message.Message(uuid_str, "rpi3_reference",
                          "docker://hello-world", metadata, message.LibMatchMode.NORMAL,
                          "","", "", True, "")

    logger.debug(f"Request: \n{pprint.pformat(msg.__dict__)}")
    logger.info("Sending request to BundleGen")
    channel.basic_publish(exchange='',
                          routing_key='bundlegen-requests',
                          body=msgpack.packb(msg.__dict__),
                          properties=pika.BasicProperties(
                              delivery_mode=2,  # make message persistent
                              reply_to='amq.rabbitmq.reply-to'
                          ))

    logger.info("Sent request to BundleGen. Waiting for response. . .")

    try:
        # Consume the reply-to queue to wait for BundleGen's response
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Received interupt. Shutting down. . .")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == "__main__":
    main()
