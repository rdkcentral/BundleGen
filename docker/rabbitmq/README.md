# RabbitMQ
## Usage
The docker-compose.yml file will start 3 docker containers by default

* BundleGen - an instance of the RabbitMQ variant of BundleGen
* RabbitMQ broker
* nginx - allows downloading of created bundles

### Build BundleGen RabbitMQ docker image
```console
$ ./build.sh
```

### Start Containers
```console
$ docker-compose up --detach
```

It may take a minute to startup as BundleGen must wait until the RabbitMQ daemon is running
and accepting requests.

RabbitMQ's management web UI is available on `http://localhost:15672/`
* username: `guest`
* password: `guest`

### View BundleGen log
```console
$ docker-compose logs -f bundlegen
Attaching to rabbitmq_bundlegen_1
bundlegen_1  | 2021-07-06 11:27:30.846 | INFO     | bundlegen.rabbitmq.main:start:70 - Starting RabbitMQ BundleGen consumer. . .
bundlegen_1  | 2021-07-06 11:27:30.924 | INFO     | bundlegen.rabbitmq.main:start:91 - Connected to RabbitMQ broker. Waiting for messages. . .
```

### Test
A test script is included with BundleGen that can be used to create a bundle for the hello-world image.

First, start the containers with docker-compose, then run the test script
```console
$ cd <repo-root>/bundlegen/rabbitmq/test
$ python3 test.py
2021-07-06 11:49:44.982 | INFO     | __main__:main:28 - Starting. . .
2021-07-06 11:49:44.998 | DEBUG    | __main__:main:66 - Request:
{'app_metadata': {'features': [],
                  'graphics': False,
                  'id': 'com.docker.helloworld',
                  'mounts': [],
                  'network': {'type': 'open'},
                  'resources': {'ram': '50M'},
                  'storage': {'persistent': [], 'temp': []},
                  'type': 'application/vnd.rdk-app.dac.native'},
 'image_url': 'docker://hello-world',
 'lib_match_mode': <LibMatchMode.NORMAL: 'normal'>,
 'platform': 'rpi3_reference',
 'uuid': '1ce7c335-98ea-49bf-af26-b6e6c9fea214'}
2021-07-06 11:49:44.999 | INFO     | __main__:main:67 - Sending request to BundleGen
2021-07-06 11:49:44.999 | INFO     | __main__:main:76 - Sent request to BundleGen. Waiting for response. . .
2021-07-06 11:49:49.498 | SUCCESS  | __main__:msg_received:18 - Request 1ce7c335-98ea-49bf-af26-b6e6c9fea214 has been completed successfully. Bundle stored in /bundles/com.docker.helloworld5fbfb3.tar.gz
```

### Start multiple instances of BundleGen
Since BundleGen runs as a RabbitMQ consumer, it is possible to run many instances of BundleGen. RabbitMQ will then distribute requests to each BundleGen instance in a round-robin fashion
```console
$ docker-compose up --detach --scale bundlegen=3
```
This will run 3 instances of bundlegen and 1 instance of rabbitmq
```
CONTAINER ID   IMAGE                     COMMAND                  CREATED             STATUS                        PORTS                                                                                                                                                 NAMES
1b1ba42508bf   bundlegen-rabbit:latest   "bundlegen-rabbitmq …"   52 seconds ago      Up 46 seconds                                                                                                                                                                       rabbitmq_bundlegen_2
2ed1e7db819d   bundlegen-rabbit:latest   "bundlegen-rabbitmq …"   52 seconds ago      Up 46 seconds                                                                                                                                                                       rabbitmq_bundlegen_3
021b49cdc9e0   bundlegen-rabbit:latest   "bundlegen-rabbitmq …"   About an hour ago   Up 51 seconds                                                                                                                                                                       rabbitmq_bundlegen_1
206f8dac9dda   rabbitmq:3-management     "docker-entrypoint.s…"   About an hour ago   Up About a minute (healthy)   4369/tcp, 5671/tcp, 0.0.0.0:5672->5672/tcp, :::5672->5672/tcp, 15671/tcp, 15691-15692/tcp, 25672/tcp, 0.0.0.0:15672->15672/tcp, :::15672->15672/tcp   rabbitmq_rabbitmq_1
```