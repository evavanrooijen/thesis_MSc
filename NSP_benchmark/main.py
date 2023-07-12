from model import find_schedule, read_instance

for inst in range(1, 2):
    instance = read_instance(inst)
    NSP, sol = find_schedule(instance) # returns NSP and sol