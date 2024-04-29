from threading import Thread, Event, Condition, Semaphore
from enum import Enum
from systime import SystemTime
import time
import random
import queue


class Status(Enum):
    CREATED = 1
    READY = 2
    RUNNING = 3
    BLOCKED = 4
    COMPLETED = 5
    UNBLOCKED = 6


class Process:
    def __init__(self, id:int, core_id:int, arrival_time:int, burst_time:int) -> None:
        self.pid = id
        self.assigned_core = core_id
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.burst_time_remaining = burst_time
        self.status = Status.CREATED
        self.completion_time = -1
        self.turnaround_time = -1
        self.waiting_time = 0
        self.next_active_time = 0

    def calc_times(self, system_time:SystemTime) -> None:
        self.completion_time = system_time.current_time + self.burst_time_remaining
        self.waiting_time += self.completion_time - self.arrival_time - self.burst_time
        if self.waiting_time < 0:
            self.waiting_time = 0
        self.turnaround_time = self.waiting_time + self.burst_time
        self.burst_time_remaining = 0

    def completion_message(self) -> None:
        print(f"Process '{self.pid}' is terminated normally in Core '{self.assigned_core}' at {self.completion_time}ms after {self.turnaround_time}ms")

    def set_completed(self) -> None:
        self.status = Status.COMPLETED

    def set_ready(self) -> None:
        self.status = Status.READY

    def run(self) -> None:
        self.status = Status.RUNNING

    def block(self, next_active_time:int) -> None:
        self.status = Status.BLOCKED
        self.assigned_core = -1
        self.next_active_time = next_active_time

    def unblock(self) -> None:
        self.status = Status.UNBLOCKED

class Core:
    __sem = Semaphore(1)

    def __init__(self, scheduling_chart:list, scheduler_num:int, core_id:int = 0) -> None:
        self.__scheduling_chart = scheduling_chart
        self.__scheduler = scheduler_num
        self.__core_id = core_id
        self.__ready_q = queue.Queue()
        self.__current_load = 0
        self.__total_processed = 0

    @property
    def core_id(self) -> int:
        return self.__core_id

    @property
    def scheduler(self) -> int:
        return self.__scheduler

    @property
    def load(self) -> int:
        return self.__current_load

    @property
    def total_load(self) -> int:
        return self.__total_processed

    def record_in_chart(self, p:Process, current_time:int, after_run_time:int) -> None:
        Core.__sem.acquire()
        self.__scheduling_chart.append((self.__core_id, p.pid, current_time, after_run_time))
        Core.__sem.release()

    def place_in_readyq(self, p:Process) -> None:
        Core.__sem.acquire()
        self.__ready_q.put(p)
        if p.status.value == 1:
            self.__current_load += 1
        p.set_ready()
        Core.__sem.release()

    def rm_from_requestq(self, request_q:list, p:Process) -> None:
        Core.__sem.acquire()
        request_q.remove(p)
        Core.__sem.release()

    def pull(self, end_signal:Event, processes:list, request_q:list) -> None:
        while not end_signal.is_set():
            stats = [p.status for p in processes]
            for p in request_q:
                if p.assigned_core == self.__core_id and p.status in (Status.CREATED, Status.UNBLOCKED):
                    print(f"'Core {self.__core_id}' pulled 'Process {p.pid}'")
                    self.place_in_readyq(p)
                    self.rm_from_requestq(request_q, p)
        print(f"'Core {self.__core_id}' has stopped pulling")

    def random_block(self, p:Process, system_time:SystemTime, condition) -> bool:
        block_choice = random.randint(1, p.burst_time)
        if p.burst_time_remaining == block_choice:
            block_time = random.randint(1, p.burst_time_remaining)
            next_active_time = system_time.current_time + block_time
            p.block(next_active_time)
            p.waiting_time += block_time
            print(f"Process {p.pid} has been blocked until {next_active_time}")
            thread = Thread(target=self.wait, args=(p, system_time, block_time, condition))
            thread.start()
            return True
        else:
            return False

    def wait(self, p:Process, system_time:SystemTime, block_time:int, condition:Condition) -> None:
        with condition:
            current_time = system_time.current_time
            condition.wait_for(lambda: current_time + block_time <= system_time.current_time)
            print(f"Process {p.pid} has been unblocked")
            p.unblock()

    def round_robin(self, end_signal:Event, system_time:SystemTime, condition:Condition) -> None:
        time_quantum = 5
        while not end_signal.is_set():
            if not self.__ready_q.empty():
                with condition:
                    p = self.__ready_q.get()
                    print(f"Core {self.__core_id} - RR: got process: {p.pid}") #for log
                    p.run()
                    if p.next_active_time != 0:
                        condition.wait_for(lambda: p.arrival_time <= system_time.current_time)
                    else:
                        condition.wait_for(lambda: p.next_active_time <= system_time.current_time)
                    if p.burst_time_remaining <= time_quantum:
                        self.record_in_chart(p, system_time.current_time, system_time.current_time + p.burst_time_remaining) # record in chart
                        print(f"Core {self.__core_id} - RR: Process '{p.pid}' has been finished") #for log
                        self.__current_load -= 1
                        self.__total_processed += 1
                        p.calc_times(system_time) #calculate the time records for process p
                        condition.wait_for(lambda: system_time.current_time == p.completion_time)
                        p.set_completed()
                        p.completion_message()
                    else:
                        print(f"Core {self.__core_id} - RR: Process '{p.pid}' has not been finished") #for log
                        p.burst_time_remaining -= time_quantum
                        print(f"Core {self.__core_id} - RR: Process '{p.pid}'s remaining time: {p.burst_time_remaining}ms") #for log
                        after_run_time = system_time.current_time + time_quantum
                        self.record_in_chart(p, system_time.current_time, after_run_time) #record in chart
                        condition.wait_for(lambda: system_time.current_time == after_run_time)
                        if self.random_block(p, system_time, condition):
                            continue
                        self.place_in_readyq(p)
                        print(f"Core {self.__core_id} - RR: Process '{p.pid}' is back in ready queue") #for log

    def run(self, end_signal:Event, system_time:SystemTime, condition:Condition) -> None:
        print(f"Core '{self.__core_id}' is running") #for log
        if self.__scheduler == 0:
            self.round_robin(end_signal, system_time, condition)
            print(f"Core '{self.__core_id}' has finished all of its tasks")
