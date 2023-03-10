# find_schedule, update_preferences
# functions to import, preprocess and visualize data
import pandas as pd
from dataclasses import dataclass

# classes: instance, nurse, schedule

# instance has nurses, shifts, ..
@dataclass
class Instance:
    instance_ID: int
    horizon: int
    S: set # set of shits (list or set? set cause unique set, no duplicate nurses)
    N: set # set of nurses

    # find schedule
    def __str__(self):
        return f"Instance {self.instance_ID} ({self.horizon} days)"

print(Instance(1, 14, {}, {}))

# nurse has personal characteristics and preference parameters
@dataclass
class Nurse:
    nurse_ID: str
    days_off: list
    max_shifts: dict
    max_total_minutes: int
    min_total_minutes: int
    max_consecutive_shifts: int
    min_consecutive_shifts: int
    min_consecutive_days_off: int
    max_weekends: int
    shifts_on_req: set # set of requests
    shifts_off_req: set # set of requests

    def __post_init__(self):
        self.satisfaction = 0

    def calc_satisfaction(self, sat_param):
        load = 8
        rest = 2
        self.satisfaction = load + rest

    def __str__(self):
        return f"Nurse {self.nurse_ID} ({self.max_total_minutes/60} hrs)"

print(Nurse('A', [0], {'D':14}, 4320, 3360, 5, 2, 2, 1, {}, {}))

@dataclass
class Request:
    nurse_ID: str
    shift_ID: str
    weight: int
    day: int

    def __str__(self):
        return f"Request for shift {self.shift_ID} on day {self.day} from nurse {self.nurse_ID} with weight {self.weight}"

print(Request('A', 'D', 2, 2))

# shift has characteristics (time, activities, nurse)
@dataclass
class Shift:
    shift_ID: str
    length_in_min: int
    cover_req: dict # hier nog iets mee doen
    # shifts_cannot_follow_this: list

    def __str__(self):
        return f"Shift {self.shift_ID} ({self.length_in_min / 60} hrs)"

cover = pd.read_csv(r'D:\OneDrive - Ortec B.V\Thesis\Code\Code\NSP_benchmark\shift_cover_req.csv')
print(cover.head())
print(Shift('D', 480, cover.to_dict()))

# schedule is assignment of shifts to nurses (maybe not needed)
# for this instance, horizon, shifts, nurses, assignment who what when

def import_instance(file, inst_ID):
    # returns an instance of the instance class

    with open(file) as f:
        lines = f.readlines()
        print(lines)
        idx = 0
        for line in lines:
            idx = idx + 1
            if line == 'SECTION_HORIZON\n':
                horizon_length = lines[idx + 2].strip('\n')
                print(f'horizon length {horizon_length}')
            elif line == 'SECTION_SHIFTS\n':
                print(idx)
                shift_ID = lines[idx + 1].split(',')[0]
                shift_length = lines[idx + 1].split(',')[1]
                print(shift_ID)
                print(shift_length)

            elif line == 'SECTION_STAFF\n':
                nurse_ID = lines[idx + 1].split(',')[0]
                print(nurse_ID)
                None

    f.close()

    instance = Instance(inst_ID, horizon_length, {}, {})
    return instance

# tests
file = r'D:\OneDrive - Ortec B.V\Thesis\Code\Code\NSP_benchmark\instances1_24\Instance1.txt'
print(import_instance(file, 1))
# print(read_instance('NSP_benchmark\instances1_24\Instance1.txt'))
#
# file = r"Code/NSP_benchmark/instances1_24/Instance1.txt"
with open(file) as f:
    lines = f.readlines()
    print(lines)
    idx = 0
    for line in lines:
        idx = idx + 1
        if line == 'SECTION_HORIZON\n':
            horizon_length = lines[idx+2]
            print(f'horizon length {horizon_length}')
        elif line == 'SECTION_SHIFTS\n':
            print(idx)
            shift_ID = lines[idx+1].split(',')[0]
            shift_length = lines[idx+1].split(',')[1]
            print(shift_ID)
            print(shift_length)

        elif line == 'SECTION_STAFF\n':
            nurse_ID =  lines[idx+1].split(',')[0]
            print(nurse_ID)
            None

# find_schedule: given instance and model solve NSP
def find_schedule(instance):
    # define MIP
    # demo: have shifts to cover and set of nurses with different weekend preferences (check CAO!)
    # by changing their weekend tolerance, show differences in schedule
    # some like weekends: pay others do not: personal life

    NSP = Model('NSP')
    #NSP.context.cplex_parameters.mip.tolerances.mipgap = 0 # check if gap is always 0 ensured
    NSP.set_time_limit(1*60) # in seconds CHECK
    x = NSP.binary_var_matrix(len(N), len(S), name = "x")

    obj_fn = sum(x.get((i, j)) for i in range(len(N)) for j in range(len(S)))
    NSP.set_objective('max', obj_fn)

    for j in range(len(S)):
        # every shift should be covered by exactly one nurse (or at least? depends on definition of a shift)
        NSP.add_constraint(sum(x.get((i, j)) for i in range(len(N))) == 1)
        
    for i in range(len(N)):
        # TODO: every nurse has a contract with FTE
        NSP.add_constraint(i.min_total_minutes < sum(j.length_in_min*x.get(i, j) for j in S) < i.max_total_minutes)
        
        # TODO: max weekends: count assigned shifts on day 5, 6, 12, 13, ... horizon
        
        # TODO: consecutiveness
        
        # TODO: max nr shifts
        
        
        #NSP.add_constraint(0 < i.max_weekends) 
    NSP.solve()
    return NSP 

file = r'D:\OneDrive - Ortec B.V\Thesis\Code\Code\NSP_benchmark\instances1_24\Instance1.txt'
instance_1 = import_instance(file, 1)
print(find_schedule(instance_1))
    # gap = NSP.solve_details.mip_relative_gap
    # #print(f"Optimal objective value z = {NSP.objective_value}")
    #
    # # visualize schedule, who works when
    #
    # # functions take solution as input and transform to readable schedule
    # # get schedule_per_nurse(i)
    # # get all shifts with nurse i
    # outcome = []
    # for v in NSP.iter_binary_vars():
    #     outcome.append(int(v.solution_value))
    #     #print(outcome)
    # return NSP.objective_value, gap


    # satisfaction is dan assigned_weekends/preference_weekends en maxmin

    # objective: maxmin satisfaction + penalty unassigned shifts

    # constraints: copied from benchmark

    # max one shift per day

    # min full day rest between shifts (forward rotation)

    # cover requirements

    # solve

# def simulate_trades(Instance.S, Instance.N):
#     # selling, buying, shift_ID, day
#     return trades


# update_preferences: given changes and nurse objects, update their preference parameters/profile
def nurse_schedule_satisfaction(nurse, schedule):
    # from schedule get consecutiveness, workload etc.

    # flexibility, worklaod

    satisfaction = None
    return satisfaction

def dept_schedule_satisfaction(dept_satisfactions):
    return (min(dept_satisfactions)) # objective is maximization of min

# def update_preferences(changes):
#     for change in changes:
#
#     # create table with changes by nurse
#
#     for nurse in nurses_changed:
#         train_satisfaction(nurse, changes[nurse])
