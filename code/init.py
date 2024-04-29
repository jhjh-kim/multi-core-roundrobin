import simulator

if __name__ == '__main__':
    process_num = 16
    burst_time_range = [1, 15]
    core_num = 4
    schedulers = [0 for i in range(core_num)]
    simulation = simulator.SimulationOS(process_num, burst_time_range, core_num, schedulers)
    simulation.run()
    simulation.summary()
    simulation.plot_chart()
