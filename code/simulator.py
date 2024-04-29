from threading import Thread, Event, Condition
from process import *
from systime import SystemTime
import matplotlib.pyplot as plt
import time
import random
import queue


class SimulationOS:
    __MAX_CORE_NUM = 16
    __core_colors = ('orange', 'magenta', 'teal', 'gray', 'cyan', 'olive', 'brown', 'skyblue', 'pink', 'maroon','red', 'blue', 'green', 'black', 'yellow', 'purple')

    def __init__(self, initial_p_num:int, burst_time_range:list, core_num:int, schedulers:list, random_arrival:bool=False) -> None:
        if len(schedulers) != core_num:
            raise ValueError("The number of schedulers should match the number of cores")
        if core_num > SimulationOS.__MAX_CORE_NUM:
            raise ValueError(f"The number of cores cannot exceed {SimulationOS.__MAX_CORE_NUM}")
        self.__system_time = SystemTime()
        self.__end_signal = Event()
        self.__processes = []
        self.__core_num = core_num
        self.scheduling_chart = []
        self.__cores = [Core(self.scheduling_chart, schedulers[i], i) for i in range(core_num)]
        self.request_queue = []
        for i in range(1, initial_p_num + 1):
            burst_time = random.randint(burst_time_range[0], burst_time_range[1])
            if random_arrival:
                arrival_time = random.randint(0, initial_p_num * 5)
            else:
                arrival_time = i
            self.create_process(i, arrival_time, burst_time)

    @property
    def current_time(self) -> int:
        return self.__system_time.current_time

    def create_process(self, id:int, arrival_time:int, burst_time:int) -> None:
        new_process = Process(id, -1, arrival_time, burst_time)
        self.__processes.append(new_process)

    def request(self) -> None:
        self.__processes.sort(key=lambda p: p.arrival_time)
        while not self.__end_signal.is_set():
            for p in self.__processes:
                if p.assigned_core != -1:
                    continue
                if p.status == Status.CREATED:
                    with self.__system_time.condition:
                        self.__system_time.condition.wait_for(lambda: p.arrival_time == self.__system_time.current_time)
                elif p.status == Status.UNBLOCKED:
                    with self.__system_time.condition:
                        self.__system_time.condition.wait_for(lambda: p.next_active_time <= self.__system_time.current_time)
                else: 
                    continue
                self.request_message(p)
                self.request_queue.append(p)
                self.load_balancing(p)

    def request_message(self, new_process:Process) -> None:
        print(f"Process '{new_process.pid}' requested CPU allocation. \nBurst time: {new_process.burst_time_remaining}ms")

    def allocate_core(self, core_id:int, p:Process) -> None:
        allocated_core = self.__cores[core_id]
        p.assigned_core = core_id
        print(f"Process '{p.pid}' has been allocated to 'Core {core_id}'.\nAllocation time: {self.__system_time.current_time}ms")

    def load_balancing(self, p:Process) -> None:
        min_load = self.__cores[0].load
        min_core_id = 0
        for i in range(1, self.__core_num):
            core_load = self.__cores[i].load
            if core_load < min_load:
                min_load = core_load
                min_core_id = i
        self.allocate_core(min_core_id, p)

    def end_check(self) -> None:
        while not self.__end_signal.is_set():
            time.sleep(1)
            print("Status Check:", end=" ")
            process_stats = [p.status.value for p in self.__processes]
            complete_cnt = 0
            for ps in process_stats:
                print(ps, end=" ")
                if ps == 5:
                    complete_cnt += 1
            print()
            if complete_cnt == len(self.__processes):
                print("All processes have finished execution.")
                self.__end_signal.set()

    def run(self) -> None:
        print("< Start Scheduling Simulation! >")
        threads = []
        threads.append(Thread(target=self.__system_time.time_tick, args=(self.__end_signal,)))
        threads.append(Thread(target=self.request))
        for c in self.__cores:
            core_ready = Thread(target=c.run, args=(self.__end_signal, self.__system_time, self.__system_time.condition))
            core_pull = Thread(target=c.pull, args=(self.__end_signal, self.__processes, self.request_queue))
            threads.append(core_ready)
            threads.append(core_pull)

        for t in threads:
            t.start()
            #time.sleep(1)

        self.end_check()

        for rc in threads:
            rc.join()

    def summary(self) -> None:
        avg_waiting_time = 0
        avg_turnaround_time = 0
        for c in self.__cores:
            print(f"Core {c.core_id} Total Load: {c.total_load}")
        for p in self.__processes:
            print(f"Process {p.pid}: Arrival Time: {p.arrival_time}ms, Burst Time: {p.burst_time}, Completion Time: {p.completion_time}, Waiting Time: {p.waiting_time}ms, Turnaround Time: {p.turnaround_time}ms")
            avg_waiting_time += p.waiting_time
            avg_turnaround_time += p.turnaround_time
        print(f"Average Waiting Time: {avg_waiting_time / len(self.__processes):.2f}ms")
        print(f"Average Turnaround Time: {avg_turnaround_time / len(self.__processes):.2f}ms")

    def plot_chart(self) -> None:
        fig, ax = plt.subplots()
        legend_added = set()
        for cn, pid, start, end in self.scheduling_chart:
            core_color = self.__core_colors[cn]
            if cn not in legend_added:
                ax.broken_barh([(start, end-start)], (10*pid, 9), facecolors=(core_color), label=f'Core {cn}')
                legend_added.add(cn)  # Mark this core as added
            else:
                ax.broken_barh([(start, end-start)], (10*pid, 9), facecolors=(core_color))
        ax.set_xlabel('Time')
        ax.set_yticks([10*p.pid + 5 for p in self.__processes])
        ax.set_yticklabels([f'Process {p.pid}' for p in self.__processes])
        ax.set_title('Scheduling Simulation Chart')
        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), borderaxespad=0.)
        plt.show()
