import pandas as pd
from dataclasses import dataclass, field
from docplex.mp.model import Model
import streamlit as st

# instance has ID, nurses, shifts, days and time horizon
@dataclass
class Instance:
    instance_ID: int
    horizon: int
    S: set # set of shits (list or set? set cause unique set, no duplicate nurses)
    N: set # set of nurses
    D: set = field(init = False) # days
    W: list = field(init = False) # weekends

    # all of these can be features of either nurse i, shift type t or day d
    # shifts_cannot_follow_this: dict
    # days_off: dict
    # length_shift: dict


    def __str__(self):
        return f"Instance {self.instance_ID} ({self.horizon} days)"

    def __post_init__(self):
        self.D = set(range(1, self.horizon+1))
        self.W = list(range(1, int(self.horizon/7+1)))

    def __hash__(self):
        return hash(self.instance_ID)

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.instance_ID == other.instance_ID

    # find schedule

print(Instance(1, 14, {}, {}))

# nurse has personal characteristics and preference parameters
@dataclass
class Nurse:
    numerical_ID: int
    nurse_ID: str
    days_off: set
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

    def show_schedule(self, solution):
        # for given solution (3D), show assigned shifts to nurse (2D) in df with
        for v in NSP.iter_binary_vars():
            print(v)#outcome.append(int(v.solution_value))

        return schedule

    def __str__(self):
        return f"Nurse {self.nurse_ID} ({self.max_total_minutes/60} hrs)"

    def __hash__(self):
        return hash(self.nurse_ID)

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.nurse_ID == other.nurse_ID

@dataclass
class Request:
    request_ID: int
    nurse_ID: str
    shift_ID: str
    weight: int
    day: int

    def __str__(self):
        return f"Request {self.request_ID}: shift {self.shift_ID} on day {self.day} from nurse {self.nurse_ID} with weight {self.weight}"

    def __hash__(self):
        return hash(self.request_ID)

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.request_ID == other.request_ID

#print(Request(1, 'A', 'D', 2, 2))

@dataclass
class Shift:
    numerical_ID: int
    shift_ID: str
    length_in_min: int
    cover_req: dict
    shifts_cannot_follow_this: list

    def __str__(self):
        return f"Shift {self.shift_ID} ({self.length_in_min / 60} hrs)"

    def __hash__(self):
        return hash(self.shift_ID)

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.shift_ID == other.shift_ID

def import_instance(file, inst_ID):
    # returns an instance of the instance class
    with open(file) as f:
        lines = f.readlines()
        idx = 0
        for line in lines:
            idx = idx + 1
            if line == 'SECTION_HORIZON\n':
                horizon_length = lines[idx + 2].strip('\n')

            elif line == 'SECTION_SHIFTS\n':

                shift_ID = lines[idx + 1].split(',')[0]
                shift_length = lines[idx + 1].split(',')[1]

            elif line == 'SECTION_STAFF\n':
                nurse_ID = lines[idx + 1].split(',')[0]
                print(nurse_ID)
                None

    f.close()
    return Instance(inst_ID, horizon_length, {}, {})

def get_weight_over(shift, day):
    df = shift.cover_req
    weight_over = int(df.loc[(df['Day'] == day-1) & (df['ShiftID'] == shift.shift_ID)].weight_over)
    return weight_over

def get_weight_under(shift, day):
    df = shift.cover_req
    weight_under = int(df.loc[(df['Day'] == day-1) & (df['ShiftID'] == shift.shift_ID)].weight_under)
    return weight_under

# find_schedule: given instance and model solve NSP
def find_schedule(instance):
    N = instance.N
    W = instance.W
    time_horizon = instance.horizon
    D = instance.D

    # define MIP
    # demo: have shifts to cover and set of nurses with different weekend preferences (check CAO!)
    # by changing their weekend tolerance, show differences in schedule
    # some like weekends: pay others do not: personal life

    NSP = Model('NSP')
    #NSP.context.cplex_parameters.mip.tolerances.mipgap = 0 # check if gap is always 0 ensured
    NSP.set_time_limit(1*60) # seconds

    # decision variables
    x = NSP.binary_var_dict((i, d, s) for i in range(len(N)) for d in range(1, time_horizon+1) for s in range(len(S)))
    k = NSP.binary_var_matrix(len(N), len(W), name = "w")
    y = NSP.integer_var_matrix(range(1, time_horizon+1), len(S), name = "y")
    z = NSP.integer_var_matrix(range(1, time_horizon+1), len(S), name="z")

    obj_fn = NSP.sum([y[day, shift.numerical_ID]*get_weight_under(shift, day) + z[day, shift.numerical_ID]*get_weight_over(shift, day) for shift in S for day in D])
    #
    # def obj_fn():
    #     obj_cover = 0
    #     obj_assigned = 0
    #     obj_unassigned = 0
    #     for day in D:
    #         for shift in S:
    #             # df = shift.cover_req
    #             # weight_over = int(df.loc[(df['Day'] == day) & (df['ShiftID'] == shift.shift_ID)].weight_over)
    #             # weight_under = int(df.loc[(df['Day'] == day) & (df['ShiftID'] == shift.shift_ID)].weight_under)
    #             obj_cover = obj_cover + y[day, shift.numerical_ID]*get_weight_under(shift, day) + z[day, shift.numerical_ID]*get_weight_over(shift, day)
    #
    #     for nurse in N:
    #         for day in D:
    #             for shift in S:
    #                 obj_unassigned = obj_unassigned + (1-x[nurse.numerical_ID, day, shift.numerical_ID]) # TODO: add penalty score
    #                 obj_assigned = obj_assigned + x[nurse.numerical_ID, day, shift.numerical_ID] # TODO: add preference score
    #
    #     obj_requests = obj_assigned + obj_unassigned
    #
    #     #obj_fn = sum(x[nurse,day,shift] for nurse in range(len(N)) for shift in range(len(S)))
    #     return obj_cover + obj_requests

    NSP.set_objective('min', obj_fn)

    # constraint 1, max one shift per day per nurse
    for day in D:
        for nurse in N:
            NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) <= 1)

    # constraint 2, shift rotation (not in instance 1)

    # constraint 3
    for shift in S:
        for nurse in N:
            NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for day in D]) <= nurse.max_shifts.get(shift.shift_ID))

    # constraint 4
    for nurse in N:
        # replace nurse by nurse and shift by t to test
        NSP.add_constraint(nurse.min_total_minutes <= sum([sum([x[nurse.numerical_ID, day, shift.numerical_ID]*shift.length_in_min for shift in S]) for day in D]))
        NSP.add_constraint(sum([sum([x[nurse.numerical_ID, day, shift.numerical_ID]*shift.length_in_min for shift in S]) for day in D]) <= nurse.max_total_minutes)

    # constraint 5: max consecutive shifts
    for nurse in N:
        for day in range(1, time_horizon-nurse.max_consecutive_shifts + 1):
            NSP.add_constraint(sum([x[nurse.numerical_ID, j, shift.numerical_ID] for shift in S for j in range(day, day+nurse.max_consecutive_shifts+1)]) <= nurse.max_consecutive_shifts)

    # constraint 6

    # constraint 7

    # constraint 8
    for nurse in N:
        for w in W:
            continue

    # constraint 9
    for nurse in N:
        for day in nurse.days_off:
            for shift in S:
                NSP.add_constraint(x[nurse.numerical_ID, day+1, shift.numerical_ID] == 0)

    # constraint 10
    for day in D:
        for shift in S:
            df = shift.cover_req
            shift_day_required = int(df.loc[(df['Day'] == day-1) & (df['ShiftID'] == shift.shift_ID)].Requirement)

            NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for nurse in N]) - z[day, shift.numerical_ID] + y[day, shift.numerical_ID] == shift_day_required)

    # for shift in range(len(S)):
    #     # every shift should be covered by exactly one nurse (or at least? depends on definition of a shift)
    #     NSP.add_constraint(sum(x[nurse,day,shift] for nurse in range(len(N))) == 1)
    #
    # for nurse in range(len(N)):
    #     # TODO: every nurse has a contract with FTE
    #     NSP.add_constraint(i.min_total_minutes < sum(j.length_in_min*x.get(i, j) for shift in S) < i.max_total_minutes)
    #
    #     # TODO: max weekends: count assigned shifts on day 5, 6, 12, 13, ... horizon
    #
    #     # TODO: consecutiveness
    #
    #     # TODO: max nr shifts
    #
    #
    #     #NSP.add_constraint(0 < i.max_weekends)
    sol = NSP.solve()

    gap = NSP.solve_details.mip_relative_gap

    print(f"Optimal objective value z = {NSP.objective_value}")

    # visualize schedule, who works when
    schedule = pd.read_csv('data\schedule_to_fill.csv')
    schedule.set_index('nurse', inplace= True)
    for nurse in N:
        for shift in S:
            for day in D:
                if sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]) == 1.0:
                    schedule.iloc[nurse.numerical_ID, day-1] = shift.shift_ID
                else:
                    schedule.iloc[nurse.numerical_ID, day-1] = '_'

    print(schedule) # to app
    st.dataframe(schedule)


    return NSP, sol

    # satisfaction is dan assigned_weekends/preference_weekends en maxmin

    # objective: maxmin satisfaction + penalty unassigned shifts

    # constraints: copied from benchmark

    # max one shift per day

    # min full day rest between shifts (forward rotation)

    # cover requirements

    # solve

# Instance 1 (ignoring all request in data and obj fn right now)
cover = pd.read_csv(r'data\shift_cover_req.csv')
nurse0 = Nurse(0, 'A', [0], {'D':14}, 4320, 3360, 5, 2, 2, 1, {}, {})
nurse1 = Nurse(1, 'B', [5], {'D':14}, 4320, 3360, 5, 2, 2, 1, {}, {})
nurse2 = Nurse(2, 'C', [8], {'D':14}, 4320, 3360, 5, 2, 2, 1, {}, {})
nurse3 = Nurse(3, 'D', [2], {'D':14}, 4320, 3360, 5, 2, 2, 1, {}, {})
nurse4 = Nurse(4, 'E', [9], {'D':14}, 4320, 3360, 5, 2, 2, 1, {}, {})
nurse5 = Nurse(5, 'F', [5], {'D':14}, 4320, 3360, 5, 2, 2, 1, {}, {})
nurse6 = Nurse(6, 'G', [1], {'D':14}, 4320, 3360, 5, 2, 2, 1, {}, {})
nurse7 = Nurse(7, 'H', [7], {'D':14}, 4320, 3360, 5, 2, 2, 1, {}, {})

S = {Shift(0, 'D', 480, cover, [])}
N = {nurse0, nurse1, nurse2, nurse3, nurse4, nurse5, nurse6, nurse7}
inst_1 = Instance(1, 14, S, N)

# Solve NSP for instance 1
find_schedule(inst_1)

# change consecutiveness preferences
nurse0.max_consecutive_shifts = 1 # st.slider('consec preference')
find_schedule(inst_1)

# # tests
# file = r'D:\OneDrive - Ortec B.V\Thesis\Code\Code\NSP_benchmark\instances1_24\Instance1.txt'
# print(import_instance(file, 1))
# print(read_instance('NSP_benchmark\instances1_24\Instance1.txt'))
#
# file = r"Code\NSP_benchmark\instances1_24\Instance1.txt"
# #file = r"Code/NSP_benchmark/instances1_24/Instance1.txt"
# with open(file) as f:
#     lines = f.readlines()
#     print(lines)
#     idx = 0
#     for line in lines:
#         idx = idx + 1
#         if line == 'SECTION_HORIZON\n':
#             horizon_length = lines[idx+2]
#             print(f'horizon length {horizon_length}')
#         elif line == 'SECTION_SHIFTS\n':
#             print(idx)
#             shift_ID = lines[idx+1].split(',')[0]
#             shift_length = lines[idx+1].split(',')[1]
#             print(shift_ID)
#             print(shift_length)
#
#         elif line == 'SECTION_STAFF\n':
#             nurse_ID =  lines[idx+1].split(',')[0]
#             print(nurse_ID)
#             None
#
# file = r"Code\NSP_benchmark\instances1_24\Instance1.txt"
# instance_1 = import_instance(file, 1)
# # print(find_schedule(instance_1))
#     # gap = NSP.solve_details.mip_relative_gap
#
#     # #print(f"Optimal objective value z = {NSP.objective_value}")
#     #
#     # # visualize schedule, who works when
#     #
#     # # functions take solution as input and transform to readable schedule
#     # # get schedule_per_nurse(i)
#     # # get all shifts with nurse i
#     # outcome = []
#     # for v in NSP.iter_binary_vars():
#     #     outcome.append(int(v.solution_value))
#     #     #print(outcome)
#     # return NSP.objective_value, gap
#
#
#     # satisfaction is dan assigned_weekends/preference_weekends en maxmin
#
#     # objective: maxmin satisfaction + penalty unassigned shifts
#
#     # constraints: copied from benchmark
#
#     # max one shift per day
#
#     # min full day rest between shifts (forward rotation)
#
#     # cover requirements
#
#     # solve
#
# # def simulate_trades(Instance.S, Instance.N):
# #     # selling, buying, shift_ID, day
# #     return trades
#
#
# # update_preferences: given changes and nurse objects, update their preference parameters/profile
# def nurse_schedule_satisfaction(nurse, schedule):
#     # from schedule get consecutiveness, workload etc.
#
#     # flexibility, worklaod
#
#     satisfaction = None
#     return satisfaction
#
# def dept_schedule_satisfaction(dept_satisfactions):
#     return (min(dept_satisfactions)) # objective is maximization of min
#
# # def update_preferences(changes):
# #     for change in changes:
# #
# #     # create table with changes by nurse
# #
# #     for nurse in nurses_changed:
# #         train_satisfaction(nurse, changes[nurse])
