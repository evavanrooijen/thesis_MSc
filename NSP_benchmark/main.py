from model import find_schedule, read_instance
import numpy as np
import matplotlib.pyplot as plt

runs = 100
total_dissat_runs = []
worst_off_excl = []
worst_off_incl = []
worst_off_runs = []
cover_runs = []
total_dissat_BMs = []
worst_off_BMs = []
coverage_BMs = []

stack_cover = []
stack_excl = []
stack_incl =[]

for inst in range(4, 7):
    for run in range(runs):
        print(run)
        instance = read_instance(inst)
        for nurse in instance.N:
            nurse.pref_alpha = round(np.random.uniform(0, 10, 1)[0])/10

        schedule, tot_dis, worst_off, coverage = find_schedule(instance, weight_over=10, weight_under=100, include_satisf = True)  # returns NSP and sol
        schedule, tot_dis_BM, worst_off_BM, coverage_BM = find_schedule(instance, weight_over=10,
                                                               weight_under=100, include_satisf = False)  # returns NSP and sol

        total_dissat_runs.append(tot_dis/len(instance.N))
        worst_off_incl.append(worst_off+coverage/100)
        worst_off_excl.append(worst_off_BM+coverage/100)
        cover_runs.append(coverage/100)
        total_dissat_BMs.append(tot_dis_BM/len(instance.N))
        worst_off_BMs.append(worst_off_BM+coverage_BM/100)
        coverage_BMs.append(coverage_BM/100)

        stack_cover.append(coverage/100)
        stack_excl.append(worst_off_BM)
        stack_incl.append(worst_off)
        # TODO: show also schedules with same coverage but lower satisfaction scores (obj = coverage only)

    # #plt.scatter(np.arange(runs), total_dissat_BMs,  color='red', label='BM dissatisfaction penalty (sum)')
    # plt.plot(np.arange(runs), worst_off_excl, color='red', label = 'worst-off (excl.)')
    # plt.plot(np.arange(runs), cover_runs, color='orange', label='coverage')
    # #plt.scatter(np.arange(runs), total_dissat_runs,  color='green', label='dissatisfaction penalty (sum)')
    # plt.plot(np.arange(runs), worst_off_incl,color='green', label = 'worst-off (incl.)')
    # plt.ylim(0, max(worst_off_excl)+3)


    plt.stackplot(np.arange(runs), stack_cover, stack_incl, stack_excl, colors=['green', 'orange', 'red'])
    #plt.scatter(np.arange(runs), worst_off_incl, color='red')

    #plt.plot(np.arange(runs), cover_runs, color='orange', label='')

    plt.title(f'Result for {runs} simulation runs')
    plt.xlabel('run')
    plt.ylabel('objective')
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4, fancybox=True, shadow=True)
    plt.savefig(f'simulation results/Simulation results for {runs} runs instance {inst}.png')
    plt.show()
