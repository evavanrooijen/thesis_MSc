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
        return f"Nurse {self.nurse_ID} prefers min {self.pref_min_cons} and max {self.pref_max_cons} consecutive shifs ({self.max_total_minutes / 60} hrs)"

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
        return pow(2, 2*(pref_min - consecutiveness))
    elif consecutiveness > pref_max:
        return pow(2, 2*(consecutiveness - pref_max))

def find_schedule(instance, weight_under = 100, weight_over = 10, vis_schedule = True, benchmark_obj = False):
    S = instance.S
    N = instance.N
    W = instance.W
    time_horizon = instance.horizon
    D = instance.D

    # define MIP
    NSP = Model('NSP')
    NSP.context.cplex_parameters.mip.tolerances.mipgap = 0  # check if gap is always 0 ensured
    NSP.set_time_limit(5 * 60)  # seconds

    # decision variables
    x = NSP.binary_var_dict((i, d, s) for i in range(len(N)) for d in range(1, time_horizon + 1) for s in range(len(S)))
    k = NSP.binary_var_matrix(len(N), range(1, len(W) + 1), name="w")
    y = NSP.integer_var_matrix(range(1, time_horizon + 1), len(S), name="y")
    z = NSP.integer_var_matrix(range(1, time_horizon + 1), len(S), name="z")
    c = NSP.binary_var_dict((i, d, r) for i in range(len(N)) for d in range(1, time_horizon + 1) for r in range(1, 11))
    # c is 1 if starting from day d, nurse i is working r consecutive shifts (sum over all types between day d and d+r = r)

    for nurse in N:
        for r in range(nurse.pref_max_cons+1, 11):
            for d in range(1, time_horizon+1-r):
                # r=3 mdwdvzz 1, 3  2, 4  3, 5, 7
                NSP.add_indicator(c[nurse.numerical_ID, d, r], NSP.sum([x[nurse.numerical_ID, day, 0] for day in range(d, d+r)]) == r) # TODO nog voor alle shift types na instanc 1 test TODO


#
#
# for r in range(max_pref + 1, 11)
#     # If needtrans[i] is 0 then delta[i] must be 0.
#     # Since needtrans[i] is penalized in the objective, the solver will
#     # try hard to set it to 0. It will only set it to 1 if delta[i] != 0.
#     # That is exactly what we want
#     m.add_indicator(c[i, d, r], NSP.sum([x[n, d, r] for d in range(day, day + r)]) == r, 0)
#
# obj_cons = 1 * m.sum([c[n, d, r] for d in)  # summation over all days -> nr of blocks of length r in i's schedule
#            + 1 * m.sum([c[n, d, 6] for d in) + 1 * m.sum([c[n, d, 5] for d in)

    # objective function (coverage)
    obj_cover = NSP.sum([y[day, shift.numerical_ID] * weight_under + z[
        day, shift.numerical_ID] * weight_over for shift in S for day in D])

    # objective function (satisfaction)
    df_on = instance.req_on
    df_off = instance.req_off
    obj_requests = 0
    obj_worst_off = 0
    unscaled_satisfaction_scores = []

    for nurse in N:
        nurse_requests_violations_penalty = 0
        for shift in S:
            for day in D:
                # check if nurse has request for this shift, day
                if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                        df_off['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    nurse_requests_violations_penalty = nurse_requests_violations_penalty + (
                            x[nurse.numerical_ID, day, shift.numerical_ID] * df_off.loc[
                        (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                                df_off['Day'] == day - 1)].Weight.item())

                # check if nurse has request for this shift, day
                if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                        df_on['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    nurse_requests_violations_penalty = nurse_requests_violations_penalty + (
                            (1 - x[nurse.numerical_ID, day, shift.numerical_ID]) * df_on.loc[
                        (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                                df_on['Day'] == day - 1)].Weight.item())
        obj_requests = obj_requests + nurse_requests_violations_penalty

        obj_consecutiveness = 0
        # sum counts of blocks of length > max_pref
        # so if pref is 4 max, then obj should be sum of c[i, d, 5] for d in range(1, time_horizon+1-5
        for r in range(nurse.pref_max_cons+1, 11):
            obj_consecutiveness = obj_consecutiveness + NSP.sum([c[nurse.numerical_ID, d, r] for d in range(1, time_horizon+1-r)])
            print(obj_consecutiveness)
        unscaled_satisfaction_scores.append(nurse.pref_alpha * obj_consecutiveness + (1-nurse.pref_alpha) * obj_requests)

    obj_worst_off = sum(unscaled_satisfaction_scores)/len(unscaled_satisfaction_scores)

    #     # consecutiveness preferences
    #     working_on = False
    #     count_on = 0
    #     consPerNurse = []
    #
    #     for day in D:
    #         if NSP.sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) >= 1:
    #             count_on += 1
    #             working_on = True
    #         else:
    #             if working_on:
    #                 consPerNurse.append(calc_cons_penalty(count_on, nurse.pref_min_cons, nurse.pref_max_cons))
    #                 count_on = 0
    #                 working_on = False
    #
    #     if working_on:
    #         consPerNurse.append(calc_cons_penalty(count_on, nurse.pref_min_cons, nurse.pref_max_cons))
    #
    #     # combine requests and consecutiveness in Pi satisfaction score per nurse
    #     consecutivenessP = sum(consPerNurse)/len(consPerNurse)
    #     unscaled_satisfaction_scores.append((1 - nurse.pref_alpha) * nurse_requests_violations_penalty + nurse.pref_alpha * consecutivenessP)
    #     obj_worst_off = max(unscaled_satisfaction_scores)
    #     # for value in unscaled_satisfaction_scores:
    #     #     if worst_off < nurse.satisfaction:
    #     #         worst_off = nurse.satisfaction



    if benchmark_obj:
        NSP.set_objective('min', obj_cover + obj_requests)
    else:
        NSP.set_objective('min', obj_cover + obj_worst_off)

    # constraint 1, max one shift per day per nurse
    for day in D:
        for nurse in N:
            NSP.add_constraint(sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) <= 1, 'max. one shift per day')

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

    # constraint BONUS: consecutive preference

    for nurse in N:
        # for r in range(1, 11):
        #     for day in range(1, time_horizon + 1):
        #         #NSP.add_constraint(c[nurse.numerical_ID, day, r] <= 0)
        for r in range(nurse.pref_max_cons+1, 10):
            for day in range(1, instance.horizon - r + 2):
                M = r - NSP.sum([x[nurse.numerical_ID, day_c, shift.numerical_ID] for day_c in range(day, day+r)])
                NSP.add_constraint((1-c[nurse.numerical_ID, day, r]) * M + NSP.sum([x[nurse.numerical_ID, day_c, shift.numerical_ID] for day_c in range(day, day+r)]) == r)

    sol = NSP.solve()
    print(f"Optimal objective value z = {NSP.objective_value} ({NSP.get_solve_details()}")
    for nurse in N:
        print(nurse)
        for r in range(1, 11):
            for d in range(1, time_horizon + 1):
                print(sol.get_value(c[nurse.numerical_ID, d, r]))
        #print(sol.get_value(x[nurse.numerical_ID, 0, 5]))

    max_cons_penalty_of_all_nurses = 1
    obj_req = 0
    for nurse in N:
        nurse_sum_req_penalties = sum(df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID)].Weight) + sum(
            df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID)].Weight)

        nurse_requests_violations_penalty = 0
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
            nurse.requestPenalty = round(nurse_requests_violations_penalty / nurse_sum_req_penalties, 2)

        # consecutiveness preferences
        working_on = False
        count_on = 0
        consPerNurse = []

        for day in D:
            if round(sum([sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]) for shift in S])) > 0:
                count_on += 1
                working_on = True
            else:
                if working_on:
                    consPerNurse.append(calc_cons_penalty(count_on, nurse.pref_min_cons, nurse.pref_max_cons))
                    count_on = 0
                    working_on = False

        if working_on:
            consPerNurse.append(calc_cons_penalty(count_on, nurse.pref_min_cons, nurse.pref_max_cons))

        if max_cons_penalty_of_all_nurses < max(consPerNurse):
            max_cons_penalty_of_all_nurses = max(consPerNurse)

        nurse.consecutivenessPenalty = sum(consPerNurse) / len(consPerNurse)

    for nurse in N:
        # rescale consecutiveness penalty on [0, 1]
        nurse.consecutivenessPenalty = nurse.consecutivenessPenalty / max_cons_penalty_of_all_nurses

        # combine requests and consecutiveness in Pi satisfaction score per nurse
        nurse.satisfaction = (1 - nurse.pref_alpha) * nurse.requestPenalty + nurse.pref_alpha * nurse.consecutivenessPenalty

    with open(f'C:/Users/EvavR/OneDrive/Documenten/GitHub/thesis_MSc/NSP_benchmark/instances1_24/instance{instance.instance_ID}/satisfaction_scores{instance.instance_ID}.csv', 'w') as f:
        f.write('NurseID, requestsPen, consecutivenessPen, satisfaction (Pi) \n')
        worst_off = 0
        for nurse in N:
            f.write(f'{nurse.nurse_ID}, {round(nurse.requestPenalty, 2)}, {round(nurse.consecutivenessPenalty, 2)}, {round(nurse.satisfaction, 2)} \n')
            if worst_off < nurse.satisfaction:
                worst_off = nurse.satisfaction
        instance.worst_off_sat = worst_off

    instance.best_undercover = round(sum([sol.get_value(y[day, shift.numerical_ID]) for day in D for shift in S]))
    instance.best_overcover = round(sum([sol.get_value(z[day, shift.numerical_ID]) for day in D for shift in S]))
    instance.best_sum_viol_req = obj_req

    # visualize schedule, who works when, coverage and satisfaction indicator values
    if vis_schedule:
        schedule = pd.read_csv(f'C:/Users/EvavR/OneDrive/Documenten/GitHub/thesis_MSc/NSP_benchmark/instances1_24/instance{instance.instance_ID}/schedule_to_fill.csv',
                               delimiter=',')
        schedule.set_index('nurse', inplace=True)

        for day in D:
            for nurse in N:
                if sum([sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]) for shift in S]) == 0.0:
                    schedule.iloc[nurse.numerical_ID, day - 1] = '_'  # nurse is not working any shift this day
                for shift in S:
                    if round(sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID])) == 1:
                        schedule.iloc[nurse.numerical_ID, day - 1] = shift.shift_ID
            # schedule.iloc[len(instance.N), day-1] = ' '
            # schedule.iloc[len(instance.N)+1, day-1] = round(sol.get_value(y[day, 0]))
            # schedule.iloc[len(instance.N)+2, day-1] = round(sol.get_value(z[day, 0]))

        # for nurse in N:
        #     schedule.iloc[nurse.numerical_ID, 15] = nurse.requestPenalty
        #     schedule.iloc[nurse.numerical_ID, 16] = nurse.consecutivenessPenalty
        #     schedule.iloc[nurse.numerical_ID, 17] = nurse.satisfaction
        #
        schedule.to_csv(f'Schedule{instance.instance_ID}.csv')
        print(schedule)
        return schedule

    return NSP, sol


def string_to_numerical_shift(shiftID, S):
    # look for shift in set S with shiftID string
    for shift in S:
        if shift.shift_ID == shiftID:
            return shift.numerical_ID

def read_instance(inst_id):
    cover = pd.read_csv(r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\shift_cover_req.csv'.format(inst_id))
    req_on = pd.read_csv(r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\requests_on.csv'.format(inst_id))
    req_off = pd.read_csv(r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\requests_off.csv'.format(inst_id))
    staff = pd.read_csv(r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\staff.csv'.format(inst_id))
    shifts = pd.read_csv(r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\shifts.csv'.format(inst_id))
    daysOff = pd.read_csv(r'C:\Users\EvavR\OneDrive\Documenten\GitHub\thesis_MSc\NSP_benchmark\instances1_24\instance{}\daysOff.csv'.format(inst_id))

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

    for nurse in N:
        nurseID = nurse.nurse_ID
        daysOffNurse1 = daysOff.loc[daysOff['EmployeeID'] == nurseID]['DayIndexes (start at zero)'].item()
        #daysOffNurse2 = daysOff.loc[daysOff['EmployeeID'] == nurseID]['DayIndexes2 (start at zero)'].item()
        nurse.days_off = [daysOffNurse1]

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

    return Instance(inst_id, time_horizons[inst_id-1], S, N, req_on, req_off)

if False:
    req_on = pd.read_csv(r'../data/requests_on_all_1_Weight.csv')
    req_off = pd.read_csv(r'../data/requests_off_all_1_weight.csv')

    open("results.txt", "w").close()
    for beta in range(11):
        find_schedule(inst_1, beta=beta / 10, weight_under =1, weight_over=1)
