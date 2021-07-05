from enum import Enum

class Result(int, Enum):
    SUCCESS = 0
    TRANSIENT_ERROR = 1,
    FATAL_ERROR = 2