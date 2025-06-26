import json
import traceback
from json import JSONDecodeError, JSONEncoder
from typing import Optional, Any

from PyQt6_JsonTextEdit._formatter.abstract import BaseTypes, QAbstractJsonFormatter

_DEFAULT_INDENT = 2
_DEFAULT_EMPTY_POLICY = True


class JsonFormatterException(Exception):
    pass


class IndentationTypeException(JsonFormatterException, TypeError):
    pass


class JsonFormattingException(JsonFormatterException, ValueError):
    """
    Exception raised for errors during JSON formatting or validation.

    Attributes:
        message (str): Human-readable error message.
        text (str): The raw JSON input text.
        start_index (int, optional): Start index of the error in the text.
        end_index (int, optional): End index of the error in the text.
        erroneous_part (str, optional): Extracted invalid portion of the text.
        line (int, optional): Line number of the error.
        column (int, optional): Column number of the error.
    """

    def __init__(self, message: str, text: str, decode_error: json.JSONDecodeError):
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not isinstance(decode_error, json.JSONDecodeError):
            raise TypeError("decode_error must be a json.JSONDecodeError")

        self.message = message
        self.text = text
        self.line = decode_error.lineno
        self.column = decode_error.colno
        self.start_index = decode_error.pos
        self.end_index = self.start_index + 1 if self.start_index < len(text) else len(text)
        self.erroneous_part = self._extract_erroneous_part()

        detailed_message = self._build_detailed_message()
        super().__init__(detailed_message)

    def _extract_erroneous_part(self) -> Optional[str]:
        try:
            return self.text[self.start_index:self.end_index]
        except IndexError:
            return "<invalid index range>"

    def _build_detailed_message(self) -> str:
        context = f"\nLine: {self.line}, Column: {self.column}, Index: {self.start_index}"
        if self.erroneous_part:
            context += f"\nErroneous part: {repr(self.erroneous_part)}"
        return f"{self.message}{context}"

    def __str__(self) -> str:
        return self.args[0]



class QJsonFormatter(QAbstractJsonFormatter):
    def __init__(self, parent=None):
        super(QJsonFormatter, self).__init__(parent)
        self._indentation = _DEFAULT_INDENT
        self._empty_policy = _DEFAULT_EMPTY_POLICY

    @property
    def indentation(self):
        return self._indentation

    def isValid(self, value: str) -> bool:
        if value is None or value == "":
            return self._empty_policy

        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            json.loads(value)
            return True
        except ValueError:
            return False

    def format(self, value: Any, **kwargs) -> Optional[str]:
        try:
            if self.isValid(value):
                if "indent" not in kwargs:
                    kwargs["indent"] = self._indentation
                if isinstance(value, str):
                    value = json.loads(value)
                return json.dumps(value, **kwargs)
        except JSONDecodeError as e:
            raise JsonFormattingException(
                "Invalid JSON input",
                value,
                e
            ) from e
        except Exception as e:
            raise JsonFormatterException("Failed to format input: "+str(e)) from e
        return None

    def jsonEncoderClass(self):
        return JSONEncoder

    def emptyPolicy(self) -> bool:
        return self._empty_policy

    def setEmptyPolicy(self, empty_policy: bool) -> None:
        if not isinstance(empty_policy, bool):
            raise JsonFormatterException("empty_policy must be a boolean")
        self._empty_policy = empty_policy

    def setIndentation(self, indentation: int) -> None:
        if not isinstance(indentation, int):
            raise IndentationTypeException("indentation must be a number")

        self._indentation = indentation

    def setJsonEncoderClass(self, cls) -> None:
        if not issubclass(cls, JSONEncoder):
            raise JsonFormatterException(f"Invalid JSONEncoder class: {cls}")