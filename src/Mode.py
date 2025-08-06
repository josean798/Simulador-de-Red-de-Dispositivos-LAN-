from enum import Enum, auto


class Mode(Enum):
    """Enumeración de modos de operación del CLI"""
    USER = auto()
    PRIVILEGED = auto()
    CONFIG = auto()
    CONFIG_IF = auto()