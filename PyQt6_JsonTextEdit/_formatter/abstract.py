import abc
from typing import Union, List, Dict

from PyQt6.QtCore import QObject

BaseTypes = Union[str, int, float, bool, None, List, Dict]


class QAbstractJsonFormatter(QObject):
    """
    Abstract base class for JSON formatters.
    """
    @abc.abstractmethod
    def isValid(self, value: str) -> bool: ...
    @abc.abstractmethod
    def format(self, value: BaseTypes) -> str: ...
