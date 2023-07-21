from model import find_schedule, read_instance
import numpy as np
import matplotlib.pyplot as plt

runs = 100
total_dissat_runs = []
worst_off_runs = []
cover_runs = []
total_dissat_BMs = []
worst_off_BMs = []
coverage_BMs = []

for run in range(runs):
    instance = read_instance(1)
    for nurse in instance.N:
        nurse.pref_alpha = round(np.random.uniform(0, 10, 1)[0])/10  # st.sidebar.slider('alpha*', 0.0, 1.0, 0.5, step=0.1)

    schedule, tot_dis, worst_off, coverage = find_schedule(instance, weight_over=10, weight_under=100, include_satisf = True)  # returns NSP and sol
    schedule, tot_dis_BM, worst_off_BM, coverage_BM = find_schedule(instance, weight_over=10,
                                                           weight_under=100, include_satisf = False)  # returns NSP and sol

    total_dissat_runs.append(tot_dis)
    worst_off_runs.append(worst_off)
    cover_runs.append(coverage/100)
    total_dissat_BMs.append(tot_dis_BM)
    worst_off_BMs.append(worst_off_BM)
    coverage_BMs.append(coverage_BM/100)
    # TODO: show also schedules with same coverage but lower satisfaction scores (obj = coverage only)

plt.plot(np.arange(runs), total_dissat_BMs, color='red', label='BM dissatisfaction penalty (sum)')
plt.plot(np.arange(runs), worst_off_BMs, color='red', label = 'BM worst off (dissatisfaction)')
plt.plot(np.arange(runs), coverage_BMs, color='orange', label='BM (under)coverage penalty')

plt.plot(np.arange(runs), total_dissat_runs, color='green', label='dissatisfaction penalty (sum)')
plt.plot(np.arange(runs), worst_off_runs, color='green', label = 'worst off (dissatisfaction)')
plt.plot(np.arange(runs), cover_runs, color='orange', label='(under)coverage penalty')
plt.title(f'Result for {runs} simulation runs')
plt.xlabel('run')
plt.ylabel('objective')
#plt.legend(loc='upper right')
plt.savefig(f'simulation results/Simulation results for {runs} runs.png')
plt.show()
