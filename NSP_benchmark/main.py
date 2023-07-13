from model import find_schedule, read_instance

open('benchmark_all_instances.txt', 'w').close() # empty file

with open('benchmark_all_instances.txt', 'a') as f:
    f.write(f'Instance ID, under, over, validated requests, total objective  \n')

for inst in range(5, 6):
    instance = read_instance(inst)
    NSP, sol = find_schedule(instance, time_limit = 1530) # returns NSP and sol