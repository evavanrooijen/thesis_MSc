from model import find_schedule, read_instance

if False:
    open('benchmark_all_instances.txt', 'w').close() # run to empty file
    with open('benchmark_all_instances.txt', 'a') as f:
        f.write(f'Instance ID, under, over, validated requests, total objective  \n')

for inst in range(11, 15):
    instance = read_instance(inst)
    NSP, sol = find_schedule(instance, vis_schedule=True, time_limit = 3000)