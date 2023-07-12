from model import find_schedule, read_instance, get_solution_statistics

for inst in range(1, 5):
    instance = read_instance(inst)
    NSP, sol = find_schedule(instance) # returns NSP and sol