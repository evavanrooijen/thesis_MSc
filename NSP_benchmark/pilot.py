import pandas as pd
from dataclasses import dataclass, field
from docplex.mp.model import Model


# instance has ID, nurses, shifts, days and time horizon
@dataclass
class Instance:
    instance_ID: int
    horizon: int
    S: set
    N: set
    req_on: dict
    req_off: dict
    D: set = field(init=False)
    W: list = field(init=False)

    def __str__(self):
        return f"Instance {self.instance_ID} ({self.horizon} days)"

    def __post_init__(self):
        self.D = set(range(1, self.horizon + 1))  # days
        self.W = list(range(1, int(self.horizon / 7 + 1)))  # weekends

    def __hash__(self):
        return hash(self.instance_ID)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.instance_ID == other.instance_ID


# nurse has personal characteristics and preference parameters
@dataclass
class Nurse:
    numerical_ID: int
    nurse_ID: str
    days_off: list
    max_shifts: dict
    max_total_minutes: int
    min_total_minutes: int
    max_consecutive_shifts: int
    min_consecutive_shifts: int
    min_consecutive_days_off: int
    max_weekends: int

    def __post_init__(self):
        self.satisfaction = 0

    def calc_satisfaction(self, sat_param):
        load = 8
        rest = 2
        self.satisfaction = load + rest
        return load

    # def show_schedule(self, solution):
    #     # for given solution (3D), show assigned shifts to nurse (2D) in df with
    #     for v in NSP.iter_binary_vars():
    #         print(v) #outcome.append(int(v.solution_value))
    #
    #     return schedule

    def __str__(self):
        return f"Nurse {self.nurse_ID} ({self.max_total_minutes / 60} hrs)"

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


@dataclass
class Shift:
    numerical_ID: int
    shift_ID: str
    length_in_min: int
    cover_req: dict
    shifts_cannot_follow_this: list  # u must be the numerical shift ID of the shift that cannot follow shift t

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

    f.close()
    return Instance(inst_ID, horizon_length, {}, {})

# find_schedule: given instance and model solve NSP
def find_schedule(instance, beta = 0.5, alpha=0.5, weight_under = 1, weight_over =1):
    N = instance.N
    W = instance.W
    time_horizon = instance.horizon
    D = instance.D
    # requests 3D, to calculate obj_requests

    # define MIP
    # demo: have shifts to cover and set of nurses with different weekend preferences (check CAO!)
    # by changing their weekend tolerance, show differences in schedule
    # some like weekends: pay others do not: personal life

    # satisfaction is dan assigned_weekends/preference_weekends en maxmin
    # objective: maxmin satisfaction + penalty unassigned shifts

    NSP = Model('NSP')
    NSP.context.cplex_parameters.mip.tolerances.mipgap = 0  # check if gap is always 0 ensured
    NSP.set_time_limit(5 * 60)  # seconds

    # decision variables
    x = NSP.binary_var_dict((i, d, s) for i in range(len(N)) for d in range(1, time_horizon + 1) for s in range(len(S)))
    k = NSP.binary_var_matrix(len(N), range(1, len(W) + 1), name="w")
    y = NSP.integer_var_matrix(range(1, time_horizon + 1), len(S), name="y")
    z = NSP.integer_var_matrix(range(1, time_horizon + 1), len(S), name="z")

    # objective function
    obj_cover = NSP.sum([y[day, shift.numerical_ID] * weight_under + z[
        day, shift.numerical_ID] * weight_over for shift in S for day in D])
    #
    # # add requests % column
    # obj_requests = 0
    # # requests: sum of weights of violated requests per nurse, day, shift
    # df_on = instance.req_on
    # df_off = instance.req_off
    # for nurse in N:
    #     for shift in S:
    #         for day in D:
    #             # check if nurse has request for this shift, day
    #             if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (df_off['Day'] == day-1)].Weight.any():
    #                 # if yes, add to obj_requests if violated
    #                 obj_requests += obj_requests + ((x[nurse.numerical_ID, day, shift.numerical_ID]) * df_off.loc[
    #                     (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (df_off['Day'] == day-1)].Weight.item())
    #
    #             # check if nurse has request for this shift, day
    #             if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (df_on['Day'] == day-1)].Weight.any():
    #                 # if yes, add to obj_requests if violated
    #                 obj_requests += obj_requests + ((1-(x[nurse.numerical_ID, day, shift.numerical_ID])) * df_on.loc[
    #                     (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (df_on['Day'] == day-1)].Weight.item())


    obj_requests = 0
    # requests: sum of weights of violated requests per nurse, day, shift
    df_on = instance.req_on
    df_off = instance.req_off
    for nurse in N:
        for shift in S:
            for day in D:
                # check if nurse has request for this shift, day
                if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (df_off['Day'] == day-1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + ((x[nurse.numerical_ID, day, shift.numerical_ID]) * df_off.loc[
                        (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (df_off['Day'] == day-1)].Weight.item())

                # check if nurse has request for this shift, day
                if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (df_on['Day'] == day-1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + ((1-x[nurse.numerical_ID, day, shift.numerical_ID]) * df_on.loc[
                        (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (df_on['Day'] == day-1)].Weight.item())

    # TODO: satisfaction score (consecutiveness)
    NSP.set_objective('min', 2*beta*obj_cover + 2* (1-beta) * obj_requests)

    # constraint 1, max one shift per day per nurse
    for day in D:
        for nurse in N:
            NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) <= 1)

    # constraint 2, shift rotation (not in instance 1 so still needs to be tested)
    for nurse in N:
        for day in range(1, time_horizon):
            for shift in S:
                for u in shift.shifts_cannot_follow_this:  # u must be the numerical shift ID of the shift that cannot follow shift t
                    x[nurse.numerical_ID, day, shift.numerical_ID] + x[nurse.numerical_ID, day + 1, u] <= 1

    # constraint 3: personal shift limitations
    for shift in S:
        for nurse in N:
            NSP.add_constraint(
                sum([x[nurse.numerical_ID, day, shift.numerical_ID] for day in D]) <= nurse.max_shifts.get(
                    shift.shift_ID))

    # constraint 4: FTE
    for nurse in N:
        NSP.add_constraint(nurse.min_total_minutes <= sum(
            [sum([x[nurse.numerical_ID, day, shift.numerical_ID] * shift.length_in_min for shift in S]) for day in D]))
        NSP.add_constraint(
            sum([sum([x[nurse.numerical_ID, day, shift.numerical_ID] * shift.length_in_min for shift in S]) for day in
                 D]) <= nurse.max_total_minutes)

    # constraint 5: max consecutive shifts
    for nurse in N:
        for day in range(1, time_horizon - nurse.max_consecutive_shifts + 1):
            NSP.add_constraint(sum([x[nurse.numerical_ID, j, shift.numerical_ID] for shift in S for j in range(day,
                                                                                                               day + nurse.max_consecutive_shifts + 1)]) <= nurse.max_consecutive_shifts)
    # constraint 6: min consecutiveness
    for nurse in N:
        for s in range(1, nurse.min_consecutive_shifts):
            for day in range(1, time_horizon - (s + 1)):
                NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) + (s - sum(
                    [x[nurse.numerical_ID, j, shift.numerical_ID] for shift in S for j in
                     range(day + 1, day + s + 1)])) + sum(
                    [x[nurse.numerical_ID, day + s + 1, shift.numerical_ID] for shift in S]) >= 0.01)

    # constraint 7: min consecutiveness days off
    for nurse in N:
        for s in range(1, nurse.min_consecutive_days_off):
            for day in range(1, time_horizon - (s + 1)):
                NSP.add_constraint(1-sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) + (sum(
                    [x[nurse.numerical_ID, j, shift.numerical_ID] for shift in S for j in
                     range(day + 1, day + s + 1)])) + 1 - sum(
                    [x[nurse.numerical_ID, day + s + 1, shift.numerical_ID] for shift in S]) >= 0.01)

    # # constraint 8: max weekends
    for nurse in N:
        for w in W:
            NSP.add_constraint(k[nurse.numerical_ID, w] <= sum(
                [x[nurse.numerical_ID, (7 * w - 1), shift.numerical_ID] for shift in S]) + sum(
                [x[nurse.numerical_ID, 7 * w, shift.numerical_ID] for shift in S]))
            NSP.add_constraint(sum([x[nurse.numerical_ID, (7 * w - 1), shift.numerical_ID] for shift in S]) + sum(
                [x[nurse.numerical_ID, 7 * w, shift.numerical_ID] for shift in S]) <= 2 * k[nurse.numerical_ID, w])

    for nurse in N:
        NSP.add_constraint(sum([k[nurse.numerical_ID, w] for w in W]) <= nurse.max_weekends)

    # constraint 9: days off
    for nurse in N:
        for day in nurse.days_off:
            for shift in S:
                NSP.add_constraint(x[nurse.numerical_ID, day + 1, shift.numerical_ID] == 0)

    # constraint 10: cover requirements
    for day in D:
        for shift in S:
            df = shift.cover_req
            shift_day_required = df.loc[(df['Day'] == day - 1 ) & (df['ShiftID'] == shift.shift_ID)].Requirement.item()

            NSP.add_constraint(
                sum([x[nurse.numerical_ID, day, shift.numerical_ID] for nurse in N]) - z[day, shift.numerical_ID] + y[
                    day, shift.numerical_ID] == shift_day_required)

    sol = NSP.solve()
    gap = NSP.solve_details.mip_relative_gap
    print(f"Optimal objective value z = {NSP.objective_value} ({NSP.get_solve_details()}")
    #print(f'Requests penalty: {}')
    # print(f"Percentage of wishes granted = {NSP.objective_value}")
    # print(f"Average satisfaction = {NSP.objective_value}")
    # print coverage
    # print satisfaction of the worst off nurse

    # visualize schedule, who works when
    schedule = pd.read_csv(r'../data/schedule_to_fill.csv')
    schedule.set_index('nurse', inplace=True)
    for nurse in N:
        for shift in S:
            for day in D:
                if sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]) == 1.0:
                    schedule.iloc[nurse.numerical_ID, day - 1] = shift.shift_ID
                else:
                    schedule.iloc[nurse.numerical_ID, day - 1] = '_'

    # add over- and undercoverage rows
    under = 0
    over = 0
    for day in D:
        schedule.iloc[8, day-1] = ' '
        schedule.iloc[9, day - 1] = int(sol.get_value(y[day, 0]))
        under = under + int(sol.get_value(y[day, 0]))
        schedule.iloc[10, day - 1] = int(sol.get_value(z[day, 0]))
        over = over + int(sol.get_value(z[day, 0]))

    # add requests % column
    obj_requests = 0
    obj_requests_total = 0
    # requests: sum of weights of violated requests per nurse, day, shift
    df_on = instance.req_on
    df_off = instance.req_off
    for nurse in N:
        schedule.iloc[nurse.numerical_ID, 14] = ' '
        for shift in S:
            for day in D:
                # check if nurse has request for this shift, day
                if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (df_off['Day'] == day-1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + (int(sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID])) * df_off.loc[
                        (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (df_off['Day'] == day-1)].Weight.item())

                # check if nurse has request for this shift, day
                if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (df_on['Day'] == day-1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + ((1-int(sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]))) * df_on.loc[
                        (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (df_on['Day'] == day-1)].Weight.item())
        schedule.iloc[nurse.numerical_ID, 15] = obj_requests
        obj_requests_total = obj_requests_total + obj_requests
        obj_requests = 0

    schedule.to_csv('solution_schedule.csv')
    print(f'{beta}, {under}, {over}, {obj_requests_total}')
    # write to result file, append: beta, under, over, requests
    with open('results.txt', 'a') as f:
        f.write(f'{beta}, {under}, {over}, {obj_requests_total}\n')

    print(schedule)  # to app st.dataframe(schedule)
    return NSP, sol

def satisfaction(schedule_nurse, nurse='A'):
    for idx in range(len(schedule_nurse)):
        # recovery_shift(schedule_nurse[idx-1], schedule_nurse[idx+1])
        nr_prior = len(schedule_nurse[:idx].rsplit('_', 1))  # not _ before this index
        return nr_prior  # satisfaction_score = TODO
        # workload_shift(schedule_nurse[idx], nr_prior, with_senior=False) # TODO with senior requires whole schedule, all nurses
        # wish_shift = schedule_nurse[idx] in nurse.wishes_on # TODO check right wish
        # shift_satisfaction = recovery_shift + workload_shift + wish_shift

# satisfaction(schedule_nurse=[_, _, D, D, D, D, _], nurse='A')

def evaluate_schedule(schedule, nurse):
    schedule = pd.read_csv(r'D:\EvaR\Documents\GitHub\thesis_MSc\data\shift_cover_req.csv')
    schedule.set_index('nurse', inplace=True)
    satisfaction_all = [satisfaction(row, nurse) for row in schedule]
    return max(min(satisfaction_all))

def string_to_numerical_shift(shiftID, S):
    # look for shift in set S with shiftID string
    for shift in S:
        if shift.shift_ID == shiftID:
            return shift.numerical_ID

cover = pd.read_csv(r'instances1_24\instance1\shift_cover_req.csv')
req_on = pd.read_csv(r'instances1_24\instance1\requests_on_all_1_Weight.csv')
req_off = pd.read_csv(r'instances1_24\instance1\requests_off_all_1_weight.csv')
staff = pd.read_csv(r'instances1_24\instance1\staff.csv')
shifts = pd.read_csv(r'instances1_24\instance1\shifts.csv')

N = set()
ID = 0
for index, row in staff.iterrows():
    N.add(Nurse(ID, row['ID'], [], {}, row['MaxTotalMinutes'], row['MinTotalMinutes'], row['MaxConsecutiveShifts'], row['MinConsecutiveShifts'], row['MinConsecutiveDaysOff'], row['MaxWeekends']))
    ID = ID + 1

S = set()
ID = 0
for index, row in shifts.iterrows():
    S.add(Shift(ID, row['ShiftID'], row['Length in mins'], cover, []))
    ID = ID + 1

for index, row in shifts.iterrows():
    if index == 0:
        continue
    if (len(row['Shifts which cannot follow this shift | separated'])) > 1:
        list_off_string_IDS = row['Shifts which cannot follow this shift | separated'].split('|')
    else:
        list_off_string_IDS = [row['Shifts which cannot follow this shift | separated']]

    list_of_impossible_shifts_to_follow = [string_to_numerical_shift(shiftID, S) for shiftID in list_off_string_IDS]
    for shift in S:
        if shift.shift_ID == row['ShiftID']:
            shift.shifts_cannot_follow_this = list_of_impossible_shifts_to_follow
    # shifts cannot follow this must be numerical IDs of shifts | separated so translate:
    # TODO: find numerical ID of shift with ShiftID 'E' (input) and returns int
    # per shift ID in shifts which cannot follow: add numericalID to a list, replace this list as shifts_cannot_follow_this

# TODO: check cover
nurse0 = Nurse(0, 'A', [0], {'D': 14}, 4320, 3360, 5, 2, 2, 1)
nurse1 = Nurse(1, 'B', [5], {'D': 14}, 4320, 3360, 5, 2, 2, 1)
nurse2 = Nurse(2, 'C', [8], {'D': 14}, 4320, 3360, 5, 2, 2, 1)
nurse3 = Nurse(3, 'D', [2], {'D': 14}, 4320, 3360, 5, 2, 2, 1)
nurse4 = Nurse(4, 'E', [9], {'D': 14}, 4320, 3360, 5, 2, 2, 1)
nurse5 = Nurse(5, 'F', [5], {'D': 14}, 4320, 3360, 5, 2, 2, 1)
nurse6 = Nurse(6, 'G', [1], {'D': 14}, 4320, 3360, 5, 2, 2, 1)
nurse7 = Nurse(7, 'H', [7], {'D': 14}, 4320, 3360, 5, 2, 2, 1)
S = {Shift(0, 'D', 480, cover, [])}
N = {nurse0, nurse1, nurse2, nurse3, nurse4, nurse5, nurse6, nurse7}
print(N)
assert len(S) != 0, "Empty set of shifts"
assert len(N) != 0, "Empty set of nurses"
inst_1 = Instance(1, 14, S, N, req_on, req_off)

# Solve NSP for instance 1
find_schedule(inst_1)

if True:
    #req_on = pd.read_csv(r'../data/requests_on_all_1_Weight.csv')
    #req_off = pd.read_csv(r'../data/requests_off_all_1_weight.csv')

    open("results.txt", "w").close()
    for beta in range(11):
        find_schedule(inst_1, beta=beta / 10, weight_under =100, weight_over=1)

test = False
if test:


    # change weekend pref (like more weekends cause extra pay)
    nurse0.max_weekends = 4
    find_schedule(inst_1)

    # change consecutiveness preferences
    nurse1.max_consecutive_shifts = 1  # more rest
    find_schedule(inst_1)

    nurse2.min_consecutive_shifts = 3  # more blocks TODO: look for bug here !
    find_schedule(inst_1)

# tests & TBC
# adding shift Shift(1, 'E', 480, cover2, [0]) breaks down system.. TBC


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
# # def update_preferences(changes or requests):
# #     for change in changes:
# #
# #     # create table with changes by nurse
# #
# #     for nurse in nurses_changed:
# #         train_satisfaction(nurse, changes[nurse])
