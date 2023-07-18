from model import find_schedule, read_instance

for inst in range(1, 2):
    instance = read_instance(inst)
    schedule = find_schedule(instance, weight_over=10, weight_under=100) # returns NSP and sol
