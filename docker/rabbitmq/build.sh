#!/bin/bash
IMAGE_NAME=bundlegen-rabbit:latest

(
    cd ../../;
    docker build -t $IMAGE_NAME -f docker/rabbitmq/Dockerfile .;
)