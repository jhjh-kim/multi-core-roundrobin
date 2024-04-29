from threading import Condition, Event
import time

class SystemTime:
    def __init__(self) -> None:
        self.__current_time = 0
        self.__condition = Condition()

    @property
    def current_time(self) -> int:
        return self.__current_time

    @property
    def condition(self) -> Condition:
        return self.__condition

    def time_tick(self, end_signal:Event) -> None:
        print("SystemTime: time starts ticking") # for log
        time.sleep(1)
        while not end_signal.is_set():
            with self.__condition:
                print(f"current_time: {self.__current_time}ms")
                self.__current_time += 1
                self.__condition.notify_all()
            time.sleep(1)
