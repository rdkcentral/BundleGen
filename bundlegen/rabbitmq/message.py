from enum import Enum


class LibMatchMode(str, Enum):
    NORMAL = "normal"
    IMAGE = "image"
    HOST = "host"


class Message(object):
    """
    Message to be send/received over rabbitmq
    """

    def __init__(self,
                 uuid: str,
                 platform: str,
                 image_url: str,
                 app_metadata: dict,
                 lib_match_mode: LibMatchMode):
        self.uuid = uuid
        self.platform = platform
        self.image_url = image_url

        if app_metadata is None:
            self.app_metadata = {}
        else:
            self.app_metadata = app_metadata
        self.lib_match_mode = lib_match_mode