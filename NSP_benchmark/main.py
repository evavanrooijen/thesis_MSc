import pandas as pd
from dataclasses import dataclass, field
from docplex.mp.model import Model

# instance has ID, nurses, shifts, days and time horizon
@dataclass
class Instance:
    def __init__(self):
        pass

    instance_ID: int
    horizon: int
    S: set # set of shifts
    N: set # set of nurses
    D: set = field(init = False)
    W: list = field(init = False)

    def __str__(self):
        return f"Instance {self.instance_ID} ({self.horizon} days)"

    def __post_init__(self):
        self.D = set(range(1, self.horizon+1)) # days
        self.W = list(range(1, int(self.horizon/7+1))) # weekends

    def __hash__(self):
        return hash(self.instance_ID)

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.instance_ID == other.instance_ID

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
        return load

    # def show_schedule(self, solution):
    #     # for given solution (3D), show assigned shifts to nurse (2D) in df with
    #     for v in NSP.iter_binary_vars():
    #         print(v) #outcome.append(int(v.solution_value))
    #
    #     return schedule

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

@dataclass
class Shift:
    numerical_ID: int
    shift_ID: str
    length_in_min: int
    cover_req: dict
    shifts_cannot_follow_this: list # u must be the numerical shift ID of the shift that cannot follow shift t

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
    # requests 3D, to calculate obj_requests

    # define MIP
    # demo: have shifts to cover and set of nurses with different weekend preferences (check CAO!)
    # by changing their weekend tolerance, show differences in schedule
    # some like weekends: pay others do not: personal life

    # satisfaction is dan assigned_weekends/preference_weekends en maxmin
    # objective: maxmin satisfaction + penalty unassigned shifts

    NSP = Model('NSP')
    NSP.context.cplex_parameters.mip.tolerances.mipgap = 0 # check if gap is always 0 ensured
    NSP.set_time_limit(1*60) # seconds

    # decision variables
    x = NSP.binary_var_dict((i, d, s) for i in range(len(N)) for d in range(1, time_horizon+1) for s in range(len(S)))
    k = NSP.binary_var_matrix(len(N), range(1, len(W)+1), name = "w")
    y = NSP.integer_var_matrix(range(1, time_horizon+1), len(S), name = "y")
    z = NSP.integer_var_matrix(range(1, time_horizon+1), len(S), name="z")

    # objective function
    obj_cover = NSP.sum([y[day, shift.numerical_ID]*get_weight_under(shift, day) + z[day, shift.numerical_ID]*get_weight_over(shift, day) for shift in S for day in D])
    obj_requests = NSP.sum([0*x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S for day in D for nurse in N])
    # TODO: satisfaction score (consecutiveness)
    NSP.set_objective('min', obj_cover + obj_requests)

    # constraint 1, max one shift per day per nurse
    for day in D:
        for nurse in N:
            NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) <= 1)

    # constraint 2, shift rotation (not in instance 1 so still needs to be tested)
    for nurse in N:
        for day in range(1, time_horizon):
            for shift in S:
                for u in shift.shifts_cannot_follow_this: # u must be the numerical shift ID of the shift that cannot follow shift t
                    x[nurse.numerical_ID, day, shift.numerical_ID] + x[nurse.numerical_ID, day+1, u] <= 1

    # constraint 3: personal shift limitations
    for shift in S:
        for nurse in N:
            NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for day in D]) <= nurse.max_shifts.get(shift.shift_ID))

    # constraint 4: FTE
    for nurse in N:
        NSP.add_constraint(nurse.min_total_minutes <= sum([sum([x[nurse.numerical_ID, day, shift.numerical_ID]*shift.length_in_min for shift in S]) for day in D]))
        NSP.add_constraint(sum([sum([x[nurse.numerical_ID, day, shift.numerical_ID]*shift.length_in_min for shift in S]) for day in D]) <= nurse.max_total_minutes)

    # constraint 5: max consecutive shifts
    for nurse in N:
        for day in range(1, time_horizon-nurse.max_consecutive_shifts + 1):
            NSP.add_constraint(sum([x[nurse.numerical_ID, j, shift.numerical_ID] for shift in S for j in range(day, day+nurse.max_consecutive_shifts+1)]) <= nurse.max_consecutive_shifts)

    # constraint 6: min consecutiveness
    for nurse in N:
        for s in range(1, nurse.min_consecutive_shifts):
            for day in range(1, time_horizon-(s+2)):
                NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) + (s-sum([x[nurse.numerical_ID, j, shift.numerical_ID] for shift in S for j in range(day+1, day+s+1)])) + sum([x[nurse.numerical_ID, day+s+1, shift.numerical_ID]for shift in S]) >= 0.00000000000001)

    # constraint 7: min consecutive days
    for nurse in N:
        for s in range(1, nurse.min_consecutive_days_off):
            for day in range(1, time_horizon-(s+2)):
                NSP.add_constraint(1 - sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) + (sum([x[nurse.numerical_ID, j, shift.numerical_ID] for shift in S for j in range(day+1, day+s+1)])) + 1 - sum([x[nurse.numerical_ID, day+s+1, shift.numerical_ID]for shift in S]) >= 0.00000000000001)

    # # constraint 8: max weekends
    for nurse in N:
        for w in W:
            NSP.add_constraint(k[nurse.numerical_ID, w] <= sum([x[nurse.numerical_ID, (7*w-1), shift.numerical_ID] for shift in S]) + sum([x[nurse.numerical_ID, 7*w, shift.numerical_ID] for shift in S]))
            NSP.add_constraint(sum([x[nurse.numerical_ID, (7*w-1), shift.numerical_ID] for shift in S]) + sum([x[nurse.numerical_ID, 7*w, shift.numerical_ID] for shift in S])<= 2*k[nurse.numerical_ID, w])

    for nurse in N:
        NSP.add_constraint(sum([k[nurse.numerical_ID, w] for w in W]) <= nurse.max_weekends)

    # constraint 9: days off
    for nurse in N:
        for day in nurse.days_off:
            for shift in S:
                NSP.add_constraint(x[nurse.numerical_ID, day+1, shift.numerical_ID] == 0)

    # constraint 10: cover requirements
    for day in D:
        for shift in S:
            df = shift.cover_req
            shift_day_required = int(df.loc[(df['Day'] == day-1) & (df['ShiftID'] == shift.shift_ID)].Requirement)

            NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for nurse in N]) - z[day, shift.numerical_ID] + y[day, shift.numerical_ID] == shift_day_required)

    sol = NSP.solve()
    gap = NSP.solve_details.mip_relative_gap
    print(f"Optimal objective value z = {NSP.objective_value}")
    #print(f"Percentage of wishes granted = {NSP.objective_value}")
    #print(f"Average satisfaction = {NSP.objective_value}")
    # print coverage
    # print satisfaction of the worst off nurse

    # visualize schedule, who works when
    schedule = pd.read_csv(r'D:\EvaR\Documents\GitHub\thesis_MSc\data\shift_cover_req.csv')
    schedule.set_index('nurse', inplace= True)
    for nurse in N:
        for shift in S:
            for day in D:
                if sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]) == 1.0:
                    schedule.iloc[nurse.numerical_ID, day-1] = shift.shift_ID
                else:
                    schedule.iloc[nurse.numerical_ID, day-1] = '_'

    print(schedule) # to app st.dataframe(schedule)
    return NSP, sol

def shift_satisfaction(shift, nurse): # TODO maybe make this nested in sequence to get nr prior cons shifts and shift prior and after...
    # function to combine workload, wishes, recovery per shift (now assumed to be linear)
    workload = 0 # shift_type*nurse.pref_type #TODO fix this
    return shift_sat

def sequence_satisfaction(sequence = [D, D, D], nurse):
    # function to combine diversity, weekend, recovery, consecutiveness (now assumed to be linear)
    diversity = len(set(sequence))
    consecutiveness = len(sequence)/4
    weekend = 0
    recovery = recovery_seq(nurse, sequence[0], sequence[-1])

    sequence_sat = diversity*nurse.pref_diversity + consecutiveness*nurse.pref_consecutiveness + weekend * nurse.pref_weekend + recovery * nurse.pref_recovery
    return sequence_sat
def satisfaction(schedule_nurse=[_, _, D, D, D, D, _], nurse='A'):
    for idx in range(len(schedule_nurse)):
        #recovery_shift(schedule_nurse[idx-1], schedule_nurse[idx+1])
        nr_prior = len(schedule_nurse[:idx].rsplit('_', 1)# not _ before this index
        return (nr_prior)
        # workload_shift(schedule_nurse[idx], nr_prior, with_senior=False) # TODO with senior requires whole schedule, all nurses
        # wish_shift = schedule_nurse[idx] in nurse.wishes_on # TODO check right wish
        # shift_satisfaction = recovery_shift + workload_shift + wish_shift
satisfaction(schedule_nurse=[_, _, D, D, D, D, _], nurse='A')

    return satisfaction_score
def evaluate_schedule(schedule):
    schedule = pd.read_csv(r'D:\EvaR\Documents\GitHub\thesis_MSc\data\shift_cover_req.csv')
    schedule.set_index('nurse', inplace=True)
    satisfaction_all = [satisfaction(row, nurse) for row in schedule]
    return max(min(satisfaction_all))


# Instance 1 (ignoring all request in data and obj fn right now)
cover = pd.read_csv(r'D:\EvaR\Documents\GitHub\thesis_MSc\data\shift_cover_req.csv')
cover2 = pd.read_csv(r'D:\EvaR\Documents\GitHub\thesis_MSc\data\shift_cover_req.csv')
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
print(Request(1, 'A', 'D', 2, 2))
inst_1 = Instance(1, 14, S, N)

# Solve NSP for instance 1
find_schedule(inst_1)

# change weekend pref (like more weekends cause extra pay)
nurse0.max_weekends = 4
find_schedule(inst_1)

# change consecutiveness preferences
nurse1.max_consecutive_shifts = 1 # more rest
find_schedule(inst_1)

nurse2.min_consecutive_shifts = 3 # more blocks TODO: look for bug here !
find_schedule(inst_1)


file = r'Code\NSP_benchmark\instances1_24\Instance1.txt'

instance = import_instance(file)

# solve LP to find base schedule
OG_schedule = find_schedule(instance)

# publish schedule
publish_schedule(OG_schedule) # this show the schedule per nurse in the application

# collect changes
changes = collect_changes(time = 7) # collect changes over 7 days, from publication by setting status planboard to "open marketplace"

# update preference parameters
update_preferences(changes) # change preferences in nurse objects who have made a change

# solve LP to find improved schedule
round2 = find_schedule(instance) # nurse objects have updated preferences (consecutiveness/workload-> motivation), soft constraint per (un)desired shift (hygiene)

# this can be done by shift (when nurses ask for change) or collectively after all change behavior is collected (could differ for self-scheduling)
publish_schedule(round2)

# self-scheduling: if nurse selects shift to (not) work, schedule is optimized to allow suggested changes but this might give early nurses a headstart
# better to collect all preferred changes and then optimize again incorporating all desired changes
