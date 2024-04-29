# Multi-core Round Robin Scheduling Simulator

 ## ✅ Implemented Features
  1. Round Robin CPU Scheduling algorithm
  2. Process Class object
  3. Handling cases where a process is blocked due to I/O operations, etc.
  4. Lock for shared resources (Semaphore)
  5. Simulator OS that performs the scheduling algorithm
  6. Multitasking capabilities in a multicore environment
  7. System Time that serves as the operating standard for each core and system components
  8. Dynamic Load Balancing feature that considers the current Load of each core in a multicore environment
  9. Visualization feature for the simulation results
## 🔀 Logic
  1. Users set the number of processes, the range of burst times for the processes, the number of cores, the scheduler for each core, and whether the arrival of processes is random before executing the simulation.
  2. Each process is created based on the initially set values.
    - Each process's Burst Time is randomly set within the given range.
    - Random Arrival = True -> Processes' Arrival Times are randomly set.
    - Random Arrival = False (Default) -> Processes' Arrival Times are set to be the same as their pid.
    - pid is set between 1 and the number of processes.
  3. The program uses multithreading to execute the necessary tasks for the simulation in parallel. The tasks executed via multithreading include:
    1. Scheduling tasks for each core.
    2. Tasks for receiving requests from newly created or unblocked processes and assigning these processes to cores through Load Balancing.
    3. Tasks for pulling assigned processes into their Ready Queue by specific cores through Load Balancing.
    4. System Time Ticking tasks of the Simulation Operating System (synchronizes threads).
  4. Simulation OS initially sorts the processes by Arrival Time, handling requests in the order of earliest Arrival Time.
    1. If a process is not yet assigned a core and is making its first request after being created, it is assigned a core when the current System Time equals or exceeds its Arrival Time.
    2. If a process that has been assigned a core and is working gets blocked and then makes another request, it is assigned a core again when the current System Time equals or exceeds the time the process becomes unblocked. Depending on the current load of the cores, a different core may be assigned.
  5. Each core processes the processes in the Ready Queue according to the predefined scheduling algorithm (Round Robin), and the results are recorded.
  6. When all processes are in the COMPLETED state, an end signal is sent to the running threads, and the simulation results and visualization graphs are output before the program terminates.
    - The Status of a process can be checked by an integer value (1: CREATED, 2: READY, 3: RUNNING, 4: BLOCKED, 5: COMPLETED, 6: UNBLOCKED).

## 🏗 Project Structure
<systime module>
1-1. class SystemTime
 
  - A class that implements the system time of the OS.
  - Synchronizes the threads currently running in the program based on the system time.
  
<process module>
2-1. class Status
 
  - An Enum that holds the possible status information of a Process.
  
2-2. class Process

  - A Class that implements a Process.
  - Has functions to update status information and calculate final execution results.

2-3. class Core

  - A Class that implements a CPU Core.
  - Responsible for the actual Scheduling tasks.
  - Has a Ready Queue and is implemented to allow for different Scheduling algorithms for each core.

<simulator module>
3-1. class SimulationOS
 
  - A class that provides an environment where Scheduling Simulation can be performed.
  - Responsible for process creation/assignment, scheduling record storage, checking termination conditions, and monitoring each core's load.
