import pandas as pd
from dataclasses import dataclass, field
from docplex.mp.model import Model
import numpy as np


# instance has ID, nurses, shifts, days and time horizon
@dataclass
class Instance:
    instance_ID: int
    horizon: int
    S: set
    N: set
    req_on: dict
    req_off: dict
    best_undercover: int = 1000
    best_overcover: int = 1000
    best_sum_viol_req: int = 1000
    worst_off_sat: int = 1000
    total_dissat: int = 1000
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
    pref_alpha: float = 0.5
    pref_min_cons: int = 2
    pref_max_cons: int = 4
    requestPenalty: float = 0
    consecutivenessPenalty: float = 0
    satisfaction: float = 0

    # def __post_init__(self):
    #     # nr. of prefered days must be integer
    #     self.pref_min_cons = round(np.random.normal(3, 1, 1)[0])
    #     self.pref_max_cons = round(np.random.normal(5, 2, 1)[0]) # TODO: CHECK THESE WITH SURVEY

    def __str__(self):
        return f"Nurse {self.nurse_ID} prefers min {self.pref_min_cons} and max {self.pref_max_cons} consecutive shifs with alpha {self.pref_alpha} ({self.max_total_minutes / 60} hrs)"

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


def calc_cons_penalty(consecutiveness, pref_min, pref_max):
    if pref_min <= consecutiveness <= pref_max:
        return 0
    elif consecutiveness < pref_min:
        return pow(2, 2 * (pref_min - consecutiveness))
    elif consecutiveness > pref_max:
        return pow(2, 2 * (consecutiveness - pref_max))


def find_schedule(instance, weight_under=100, weight_over=10, vis_schedule=True, include_satisf = True):
    S = instance.S
    N = instance.N
    W = instance.W
    time_horizon = instance.horizon
    D = instance.D

    # define MIP
    NSP = Model('NSP')
    NSP.float_precision = 10
    NSP.context.cplex_parameters.mip.tolerances.mipgap = 0  # check if gap is always 0 ensured
    NSP.set_time_limit(5 * 60)  # seconds

    # decision variables
    x = NSP.binary_var_dict((i, d, s) for i in range(len(N)) for d in range(1, time_horizon + 1) for s in range(len(S)))
    k = NSP.binary_var_matrix(len(N), range(1, len(W) + 1), name="w")
    y = NSP.integer_var_matrix(range(1, time_horizon + 1), len(S), name="y")
    z = NSP.integer_var_matrix(range(1, time_horizon + 1), len(S), name="z")
    c = NSP.binary_var_dict((i, d, r) for i in range(len(N)) for d in range(1, time_horizon + 1) for r in range(1, 11))
    obj_worst_off = NSP.continuous_var(lb=0, name="worst-off penalty")
    obj_total_dissatisfaction = NSP.continuous_var(lb=0, name="Total sum of dissatisfaction (penalties) of all nurses")
    obj_cover = NSP.continuous_var(lb=0, name='Coverage penalty')

    # objective function (coverage)
    NSP.add_constraint(
    obj_cover == NSP.sum([y[day, shift.numerical_ID] * weight_under + z[
        day, shift.numerical_ID] * weight_over for shift in S for day in D]))

    if include_satisf:
        NSP.set_objective('min',  obj_cover + obj_total_dissatisfaction + obj_worst_off)
    else:
        NSP.set_objective('min', obj_cover)
    for nurse in N:
        # for r in range(nurse.pref_max_cons + 1, 11):
        #     for d in range(1, time_horizon + 2 - r):
        #         # TODO nog voor alle shift types na instanc 1 test TODO
        #         NSP.add(NSP.if_then(NSP.sum([x[nurse.numerical_ID, day, 0] for day in range(d, d + r)]) == r, c[nurse.numerical_ID, d, r] >= 0.5))
        #         NSP.add(NSP.if_then(NSP.sum([x[nurse.numerical_ID, day, 0] for day in range(d, d + r)]) != r, c[nurse.numerical_ID, d, r] <= 0.5))

    # consecutiveness measurement for violations min. pref (copied)        # if assume pref_max > pref_min, c_min can be c
        for r in range(1, 11):
            # count min cons violations
            d = 1
            NSP.add(NSP.if_then((1 - x[nurse.numerical_ID, d + r, 0]) +
                                  NSP.sum([x[nurse.numerical_ID, day, 0] for day in range(d, d + r)]) == r + 1, c[nurse.numerical_ID, d, r] >= 0.5))
            NSP.add(NSP.if_then((1 - x[nurse.numerical_ID, d + r, 0]) +
                                NSP.sum([x[nurse.numerical_ID, day, 0] for day in range(d, d + r)]) != r + 1,
                                c[nurse.numerical_ID, d, r] <= 0.5))

            # TODO nog voor alle shift types na instance 1 test TODO

            for d in range(2, time_horizon + 1 - r): # check d's
                NSP.add(NSP.if_then((1 - x[nurse.numerical_ID, d - 1, 0]) + (1 - x[nurse.numerical_ID, d + r, 0]) +
                                      NSP.sum([x[nurse.numerical_ID, day, 0] for day in range(d, d + r)]) == r + 2,
                                      c[nurse.numerical_ID, d, r] >= 0.5)) # TODO nog voor alle shift types na instanc 1 test TODO
                NSP.add(NSP.if_then((1 - x[nurse.numerical_ID, d - 1, 0]) + (1 - x[nurse.numerical_ID, d + r, 0]) +
                                    NSP.sum([x[nurse.numerical_ID, day, 0] for day in range(d, d + r)]) != r + 2,
                                    c[nurse.numerical_ID, d, r]<=0.5))
                                    # c[n, d, r] when c[n, d, -1] is NaN and should use 0
            d = time_horizon + 1 - r
            NSP.add(NSP.if_then((1 - x[nurse.numerical_ID, d - 1, 0]) +
                                  NSP.sum([x[nurse.numerical_ID, day, 0] for day in range(d, d + r)]) == r + 1,
                                  c[nurse.numerical_ID, d, r] >= 0.5))  # TODO nog voor alle shift types na instance 1 test

            NSP.add(NSP.if_then((1 - x[nurse.numerical_ID, d - 1, 0]) +
                                  NSP.sum([x[nurse.numerical_ID, day, 0] for day in range(d, d + r)]) != r + 1,
                                  c[nurse.numerical_ID, d, r] <= 0.5))  # TODO nog voor alle shift types na instance 1 test

    # auxiliary constraint (maximin criterion), # objective function (satisfaction)
    df_on = instance.req_on
    df_off = instance.req_off

    for nurse in N:
        obj_consecutiveness = 0
        obj_requests = 0
        for r in range(nurse.pref_max_cons + 1, nurse.max_consecutive_shifts + 1):
            obj_consecutiveness = obj_consecutiveness + NSP.sum(
                     [c[nurse.numerical_ID, d, r] for d in range(1, time_horizon + 2 - r)])

        for r in range(1, nurse.pref_min_cons):
            obj_consecutiveness = obj_consecutiveness + NSP.sum(
                     [c[nurse.numerical_ID, d, r] for d in range(1, time_horizon + 2 - r)])

        for shift in S:
            for day in D:
                # check if nurse has request for this shift, day
                if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                        df_off['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + (
                            x[nurse.numerical_ID, day, shift.numerical_ID] * df_off.loc[
                        (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                                df_off['Day'] == day - 1)].Weight.item())

                    # check if nurse has request for this shift, day
                if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                        df_on['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + (
                            (1 - x[nurse.numerical_ID, day, shift.numerical_ID]) * df_on.loc[
                        (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                                df_on['Day'] == day - 1)].Weight.item())

        total_penalty_per_nurse = nurse.pref_alpha * obj_consecutiveness + (
                    1 - nurse.pref_alpha) * obj_requests
        NSP.add_constraint(obj_worst_off >= total_penalty_per_nurse)
        obj_total_dissatisfaction = obj_total_dissatisfaction + total_penalty_per_nurse

    # constraint 1, max one shift per day per nurse
    for day in D:
        for nurse in N:
            NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) <= 1,
                               'max. one shift per day')

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
                NSP.add_constraint(1 - sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) + (sum(
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
            shift_day_required = df.loc[(df['Day'] == day - 1) & (df['ShiftID'] == shift.shift_ID)].Requirement.item()

            NSP.add_constraint(
                sum([x[nurse.numerical_ID, day, shift.numerical_ID] for nurse in N]) - z[day, shift.numerical_ID] + y[
                    day, shift.numerical_ID] == shift_day_required)

    sol = NSP.solve()
    print(f"Optimal objective value z = {NSP.objective_value} ({NSP.get_solve_details()}")
    print(f"Worst off: {sol.get_value(obj_worst_off)}")
    print(f"Total dissat: {sol.get_value(obj_total_dissatisfaction)}")

    max_cons_penalty_of_all_nurses = 1
    obj_req = 0

    for nurse in N:
        obj_consecutiveness = 0
        for r in range(nurse.pref_max_cons + 1, nurse.max_consecutive_shifts + 1):
            obj_consecutiveness = obj_consecutiveness + sum(
                [sol.get_value(c[nurse.numerical_ID, d, r]) for d in range(1, time_horizon + 2 - r)])
            value = sum(
                [sol.get_value(c[nurse.numerical_ID, d, r]) for d in range(1, time_horizon + 2 - r)])
            if value>0:
                print(f'nurse {nurse.nurse_ID} has {value} blocks of length {r}')

        for r in range(1, nurse.pref_min_cons):
            obj_consecutiveness = obj_consecutiveness + sum(
                [sol.get_value(c[nurse.numerical_ID, d, r]) for d in range(1, time_horizon + 2 - r)])
            value = sum(
                [sol.get_value(c[nurse.numerical_ID, d, r]) for d in range(1, time_horizon + 2 - r)])
            if value>0:
                print(f'nurse {nurse.nurse_ID} has {value} blocks of length {r}')

        nurse.consecutivenessPenalty = obj_consecutiveness
        if max_cons_penalty_of_all_nurses <= obj_consecutiveness:
            max_cons_penalty_of_all_nurses = obj_consecutiveness

        nurse_requests_violations_penalty = 0
        nurse_sum_req_penalties = sum(df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID)].Weight) + sum(
            df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID)].Weight)

        for shift in S:
            for day in D:
                # check if nurse has request for this shift, day
                if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                        df_off['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    nurse_requests_violations_penalty = nurse_requests_violations_penalty + (
                            sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]) * df_off.loc[
                        (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                                df_off['Day'] == day - 1)].Weight.item())

                # check if nurse has request for this shift, day
                if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                        df_on['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    nurse_requests_violations_penalty = nurse_requests_violations_penalty + (
                            (1 - sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID])) * df_on.loc[
                        (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                                df_on['Day'] == day - 1)].Weight.item())

        obj_req = obj_req + nurse_requests_violations_penalty
        # scale request penalty on [0, 1]
        if nurse_sum_req_penalties == 0:
            nurse.requestPenalty = 0
        else:
            nurse.requestPenalty = round(nurse_requests_violations_penalty) # / nurse_sum_req_penalties, 2)

        # rescale consecutiveness penalty on [0, 1]
        nurse.consecutivenessPenalty = nurse.consecutivenessPenalty #/ max_cons_penalty_of_all_nurses

        # combine requests and consecutiveness in Pi satisfaction score per nurse
        nurse.satisfaction = (1 - nurse.pref_alpha) * nurse.requestPenalty + nurse.pref_alpha * nurse.consecutivenessPenalty
        print(f'Dissatisfaction {nurse.satisfaction} for nurse {nurse.nurse_ID}, where cons {nurse.consecutivenessPenalty} and req {nurse.requestPenalty}')

    with open(
            f'C:/Users/EvavR/OneDrive/Documenten/GitHub/thesis_MSc/NSP_benchmark/instances1_24/instance{instance.instance_ID}/satisfaction_scores{instance.instance_ID}.csv',
            'w') as f:
        f.write('NurseID, requestsPen, consecutivenessPen, satisfaction (Pi) \n')
        worst_off = 0
        total_dissat = 0
        for nurse in N:
            f.write(
                f'{nurse.nurse_ID}, {round(nurse.requestPenalty, 2)}, {round(nurse.consecutivenessPenalty, 2)}, {round(nurse.satisfaction, 2)} \n')
            if worst_off < nurse.satisfaction:
                worst_off = nurse.satisfaction
            total_dissat = total_dissat + nurse.satisfaction
        instance.worst_off_sat = worst_off
        instance.total_dissat = total_dissat

    instance.best_undercover = round(sum([sol.get_value(y[day, shift.numerical_ID]) for day in D for shift in S]))
    instance.best_overcover = round(sum([sol.get_value(z[day, shift.numerical_ID]) for day in D for shift in S]))
    instance.best_sum_viol_req = obj_req

    # visualize schedule, who works when, coverage and satisfaction indicator values
    if vis_schedule:
        schedule = pd.read_csv(
            f'C:/Users/EvavR/OneDrive/Documenten/GitHub/thesis_MSc/NSP_benchmark/instances1_24/instance{instance.instance_ID}/schedule_to_fill.csv',
            delimiter=';')
        schedule.set_index('nurse', inplace=True)

        for day in D:
            for nurse in N:
                if sum([sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]) for shift in S]) == 0.0:
                    schedule.iloc[nurse.numerical_ID, day - 1] = '_'  # nurse is not working any shift this day
                for shift in S:
                    if round(sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID])) == 1:
                        schedule.iloc[nurse.numerical_ID, day - 1] = shift.shift_ID

        schedule.to_csv(f'Schedule{instance.instance_ID}.csv')
        return schedule, sol.get_value(obj_total_dissatisfaction), sol.get_value(obj_worst_off), sol.get_value(obj_cover)

    return NSP, sol

def string_to_numerical_shift(shiftID, S):
    # look for shift in set S with shiftID string
    for shift in S:
        if shift.shift_ID == shiftID:
            return shift.numerical_ID

def read_instance(inst_id):
    cover = pd.read_csv(
        r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\shift_cover_req.csv'.format(
            inst_id))
    req_on = pd.read_csv(
        r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\requests_on.csv'.format(
            inst_id))
    req_off = pd.read_csv(
        r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\requests_off.csv'.format(
            inst_id))
    staff = pd.read_csv(
        r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\staff.csv'.format(
            inst_id))
    shifts = pd.read_csv(
        r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\shifts.csv'.format(
            inst_id))
    daysOff = pd.read_csv(
        r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\daysOff.csv'.format(
            inst_id))

    time_horizons = [14, 14, 14, 28, 28, 28, 28, 28, 28, 28]

    N = set()
    ID = 0
    for index, row in staff.iterrows():
        # maxshifts split per | first, then by = to get key value pairs
        max_shifts_dict = {}
        list_of_all_max_shifts = row['MaxShifts'].split('|')

        for max_shift in list_of_all_max_shifts:
            list_max_shifts = max_shift.split('=')
            max_shifts_dict[list_max_shifts[0]] = int(list_max_shifts[1])

        N.add(Nurse(ID, row['ID'], [], max_shifts_dict, row['MaxTotalMinutes'],
                    row['MinTotalMinutes'], row['MaxConsecutiveShifts'], row['MinConsecutiveShifts'],
                    row['MinConsecutiveDaysOff'], row['MaxWeekends']))
        ID = ID + 1

    if inst_id < 4:
        for nurse in N:
            nurseID = nurse.nurse_ID
            daysOffNurse1 = daysOff.loc[daysOff['EmployeeID'] == nurseID]['DayIndexes (start at zero)'].item()
            nurse.days_off = [daysOffNurse1]

    elif inst_id >= 4:
        for nurse in N:
            nurseID = nurse.nurse_ID
            daysOffNurse1 = daysOff.loc[daysOff['EmployeeID'] == nurseID]['DayIndexes1 (start at zero)'].item()
            daysOffNurse2 = daysOff.loc[daysOff['EmployeeID'] == nurseID]['DayIndexes2 (start at zero)'].item()
            nurse.days_off = [daysOffNurse1, daysOffNurse2]

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

        assert len(S) != 0, "Empty set of shifts"
        assert len(N) != 0, "Empty set of nurses"

    return Instance(inst_id, time_horizons[inst_id - 1], S, N, req_on, req_off)


if False:
    req_on = pd.read_csv(r'../data/requests_on_all_1_Weight.csv')
    req_off = pd.read_csv(r'../data/requests_off_all_1_weight.csv')

    open("results.txt", "w").close()
    for beta in range(11):
        find_schedule(inst_1, beta=beta / 10, weight_under=1, weight_over=1)
