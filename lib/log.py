# stdlib
import sys
from pprint import PrettyPrinter
from typing import Any

# =============================================================================
#
# functions
#
# =============================================================================

# =============================================================================
# log
# =============================================================================


def log(message: str, **kwargs) -> None:
    print(message, file=sys.stderr, **kwargs)  # noqa: T201


# =============================================================================
# NoStringWrappingPrettyPrinter
# c\o: https://stackoverflow.com/questions/31485402/
#       can-i-make-pprint-in-python3-not-split-strings-like-in-python2
# =============================================================================
class NoStringWrappingPrettyPrinter(PrettyPrinter):
    _width: int

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _format(self, message, *args) -> None:
        if isinstance(message, str):
            width = self._width
            self._width = sys.maxsize
            try:
                super()._format(message, *args)  # type: ignore
            finally:
                self._width = width
        else:
            super()._format(message, *args)  # type: ignore


# =============================================================================
# log_pretty
# =============================================================================
def log_pretty(value: Any) -> None:
    pp = NoStringWrappingPrettyPrinter(stream=sys.stderr)
    pp.pprint(value)
