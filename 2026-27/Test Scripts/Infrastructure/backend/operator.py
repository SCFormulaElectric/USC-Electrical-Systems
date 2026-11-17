"""Console observations with bounded waits and caller-supplied bench monitoring."""
import queue
import threading
import time
from typing import Callable

from .measurements import reading


def monitored_input(question: str, *, check: Callable[[], None], timeout_s: float = 300) -> str:
    """Read text while check() runs on the main thread. Exceptions/timeouts abort the prompt."""
    timeout = reading(timeout_s)
    if timeout <= 0:
        raise ValueError('Operator timeout must be positive')
    responses = queue.Queue()

    def read_input():
        try:
            responses.put(input(question))
        except BaseException as error:
            responses.put(error)

    # shortcut: console input cannot be canceled portably; abort the run after a timeout.
    threading.Thread(target=read_input, daemon=True).start()
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        check()
        try:
            result = responses.get(timeout=min(.5, max(0, deadline-time.monotonic())))
        except queue.Empty:
            continue
        if isinstance(result, BaseException):
            raise result
        return result
    raise TimeoutError('Operator response timed out; aborting procedure')
