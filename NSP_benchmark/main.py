from model import find_schedule, read_instance

open('benchmark_all_instances.txt', 'w').close() # empty file

with open('benchmark_all_instances.txt', 'a') as f:
    f.write(f'Instance ID, under, over, validated requests, total objective  \n')

for inst in range(1, 9):
    instance = read_instance(inst)
    NSP, sol = find_schedule(instance) # returns NSP and sol