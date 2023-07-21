from model import find_schedule, read_instance
import numpy as np
import matplotlib.pyplot as plt

runs = 2
total_dissat_runs = []
worst_off_runs = []
cover_runs = []

for run in range(runs):
    instance = read_instance(1)
    for nurse in instance.N:
        nurse.pref_alpha = round(np.random.uniform(0, 10, 1)[0])/10  # st.sidebar.slider('alpha*', 0.0, 1.0, 0.5, step=0.1)

    schedule, tot_dis, worst_off, coverage = find_schedule(instance, weight_over=10, weight_under=100)  # returns NSP and sol
    total_dissat_runs.append(tot_dis)
    worst_off_runs.append(worst_off)
    cover_runs.append(coverage/100)

plt.plot(np.arange(runs), total_dissat_runs, label='dissatisfaction penalty (sum)')
plt.plot(np.arange(runs), worst_off_runs, label = 'worst off (dissatisfaction)')
plt.plot(np.arange(runs), cover_runs, label='(under)coverage penalty')
plt.title(f'Result for {runs} simulation runs')
plt.xlabel('run')
plt.ylabel('objective')
plt.legend(loc='upper right')
plt.savefig(f'simulation results/Simulation results for {runs} runs.png')
plt.show()
