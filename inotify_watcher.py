import logging
import threading
from typing import Callable
from typing import List
from typing import Optional
from typing import Union

logger = logging.getLogger(__name__)

__version__ = "0.0.0.dev0"

__all__ = ["InotifyWatcher"]

HandlerNoneType = Callable[[], None]
HandlerOneType = Callable[[str], None]
HandlerTwoType = Callable[[str, str], None]
HandlerType = Union[HandlerOneType, HandlerTwoType]


class InotifyWatcher:
    def __init__(self, *paths: str, **handlers: HandlerType) -> None:
        self.__threads: List[threading.Thread] = list()
        self.__terminated = threading.Event()

        self.__start()

    def __del__(self) -> None:
        self.terminate()

    def __start(self) -> None:
        self.__threads.append(
            threading.Thread(target=self.__wrapper, args=[self.__watcher])
        )
        self.__threads.append(
            threading.Thread(target=self.__wrapper, args=[self.__runner])
        )

        self.__terminated.clear()

        for thread in self.__threads:
            thread.start()

    def terminate(self) -> None:
        self.__terminated.set()

        for thread in self.__threads:
            thread.join()

        self.__threads.clear()

    def wait(self, timeout: Optional[float] = None) -> bool:
        return self.__terminated.wait(timeout)

    def __wrapper(self, function: HandlerNoneType) -> None:
        while not self.__terminated.is_set():
            try:
                function()

            except Exception as err:
                logger.error(err, exc_info=True)

    def __watcher(self) -> None:
        pass

    def __runner(self) -> None:
        pass
