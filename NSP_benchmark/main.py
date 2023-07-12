from model import find_schedule, read_instance

for inst in range(1, 3):
    instance = read_instance(inst)
    schedule = find_schedule(instance) # returns NSP and sol
