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
    pref_alpha: float = 0.5
    pref_min_cons: int = 2
    pref_max_cons: int = 4

    def __post_init__(self):
        self.satisfaction = 0
        #self.pref_alpha = 0.5

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

def calc_cons_penalty(consecutiveness, pref_min, pref_max):
    if pref_min <= consecutiveness <= pref_max:
        return 0
    elif consecutiveness < pref_min:
        return pow(2, pref_min - consecutiveness)
    elif consecutiveness > pref_max:
        return pow(2, consecutiveness - pref_max)

def find_schedule(instance, beta = 0.5, alpha=0.5, weight_under = 100, weight_over =1):
    S = instance.S
    N = instance.N
    W = instance.W
    time_horizon = instance.horizon
    D = instance.D

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

    # objective function (coverage)
    obj_cover = NSP.sum([y[day, shift.numerical_ID] * weight_under + z[
        day, shift.numerical_ID] * weight_over for shift in S for day in D])

    # objective function (satisfaction)
    df_on = instance.req_on
    df_off = instance.req_off

    satisfaction_nurses = []
    obj_worst_off = 0

    for nurse in N:
        nurse_requests_penalty = 0
        for shift in S:
            for day in D:
                # check if nurse has request for this shift, day
                if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (df_off['Day'] == day-1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    nurse_requests_penalty = nurse_requests_penalty + ((x[nurse.numerical_ID, day, shift.numerical_ID]) * df_off.loc[
                        (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (df_off['Day'] == day-1)].Weight.item())

                # check if nurse has request for this shift, day
                if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (df_on['Day'] == day-1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    nurse_requests_penalty = nurse_requests_penalty + ((1-x[nurse.numerical_ID, day, shift.numerical_ID]) * df_on.loc[
                        (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (df_on['Day'] == day-1)].Weight.item())

        # consecutiveness preferences
        working_on = False
        count_on = 0
        consPerNurse = []
        for day in D:
            if sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) is not 0.0:
                count_on += 1
                working_on = True
            else:
                if working_on:
                    consPerNurse.append(calc_cons_penalty(count_on, nurse.pref_min_cons, nurse.pref_max_cons))
                    count_on = 0
                    working_on = False
        if working_on:
            consPerNurse.append(calc_cons_penalty(count_on, nurse.pref_min_cons, nurse.pref_max_cons))

        # convex combination of satisfaction components
        satisfaction_nurses.append((1 - nurse.pref_alpha) * nurse_requests_penalty + nurse.pref_alpha * NSP.sum(consPerNurse) / len(consPerNurse))

        if obj_worst_off <= ((1 - alpha) * nurse_requests_penalty + alpha * NSP.sum(consPerNurse) / len(consPerNurse)):
            obj_worst_off = (1 - alpha) * nurse_requests_penalty + alpha * NSP.sum(consPerNurse) / len(consPerNurse)

    # TODO: satisfaction score (consecutiveness)
    NSP.set_objective('min', obj_cover + 10* obj_worst_off)

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
    print(f"Optimal objective value z = {NSP.objective_value} ({NSP.get_solve_details()}")

    # print satisfaction of the worst off nurse
    under = sol.get_value(sum([y[day, shift.numerical_ID] for shift in instance.S for day in instance.D]))
    over = sol.get_value(sum([z[day, shift.numerical_ID] for shift in instance.S for day in instance.D]))
    print(f'Shifts underassigned: {under}, \nShifts overassigned: {over}, \nWorst-off nurse: {0} \n')
    obj_consecutiveness = 0
    obj_requests = 0
    df_on = instance.req_on
    df_off = instance.req_off
    with open('scores1.txt', 'w') as f:
        f.write('NurseID, consecutiveness penalty (avg), requests penalty (sum), satisfaction (Pi) \n')
        requests_all_nurses = []
        cons_all_nurses = []
        for nurse in N:
            f.write(f'{nurse.nurse_ID}, ')
            nurse_requests_penalty = 0
            for shift in S:
                for day in D:
                    # check if nurse has request for this shift, day
                    if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                            df_off['Day'] == day - 1)].Weight.any():
                        # if yes, add to obj_requests if violated
                        nurse_requests_penalty = nurse_requests_penalty + (
                                    (x[nurse.numerical_ID, day, shift.numerical_ID]) * df_off.loc[
                                (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                                            df_off['Day'] == day - 1)].Weight.item())

                    # check if nurse has request for this shift, day
                    if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                            df_on['Day'] == day - 1)].Weight.any():
                        # if yes, add to obj_requests if violated
                        nurse_requests_penalty = nurse_requests_penalty + (
                                    (1 - x[nurse.numerical_ID, day, shift.numerical_ID]) * df_on.loc[
                                (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                                            df_on['Day'] == day - 1)].Weight.item())
            requests_all_nurses.append(nurse_requests_penalty)
            f.write(f'{nurse_requests_penalty}, ')

            # consecutiveness preferences
            working_on = False
            count_on = 0
            consPerNurse = []

            for day in D:
                if sum([x[nurse.numerical_ID, day, shift.numerical_ID] for shift in S]) is not 0.0:
                    count_on += 1
                    working_on = True
                else:
                    if working_on:
                        consPerNurse.append(calc_cons_penalty(count_on, nurse.pref_min_cons, nurse.pref_max_cons))
                        count_on = 0
                        working_on = False

            if working_on:
                consPerNurse.append(calc_cons_penalty(count_on, nurse.pref_min_cons, nurse.pref_max_cons))

            cons_all_nurses.append(
                sum(consPerNurse) / len(consPerNurse))  # average penalty of all blocks in nurse i's roster

            # satisfaction_scores[nurse.numerical_ID, 2] = sum(consPerNurse)/len(consPerNurse)
            f.write(f'{sum(consPerNurse) / len(consPerNurse)}, ')

            # combine requests and consecutiveness in Pi satisfaction score per nurse
            alpha = nurse.pref_alpha
            # satisfaction_scores[nurse.numerical_ID, 3] = (1-alpha) * satisfaction_scores[nurse.numerical_ID, 1] + alpha * satisfaction_scores[nurse.numerical_ID, 2]
            f.write(f'{(1 - alpha) * nurse_requests_penalty + alpha * sum(consPerNurse) / len(consPerNurse)}\n')

    return NSP, sol

def get_solution_statistics(sol, instance):
    # print satisfaction of the worst off nurse
    under = sol.get_value(sum([y[day, shift.numerical_ID] for shift in instance.S for day in instance.D]))
    over = sol.get_value(sum([z[day, shift.numerical_ID] for shift in instance.S for day in instance.D]))
    obj_requests = 0
    # requests: sum of weights of violated requests per nurse, day, shift
    df_on = instance.req_on
    df_off = instance.req_off
    for nurse in instance.N:
        for shift in instance.S:
            for day in instance.D:
                # check if nurse has request for this shift, day
                if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                        df_off['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + (sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]) * df_off.loc[
                        (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                                    df_off['Day'] == day - 1)].Weight.item())

                # check if nurse has request for this shift, day
                if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                        df_on['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + ((1 - sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID])) * df_on.loc[
                        (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                                    df_on['Day'] == day - 1)].Weight.item())

    return under, over, obj_requests
def print_schedule(sol, instance):
    # TODO: fix size of pd dataframe to export schedule (IndexError)
    S = instance.S
    N = instance.N
    W = instance.W
    time_horizon = instance.horizon
    D = instance.D
    # visualize schedule, who works when
    # schedule = pd.read_csv(r'../data/schedule_to_fill.csv')
    schedule = pd.DataFrame()
    # schedule.set_index('nurse', inplace=True)
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
        schedule.iloc[8, day - 1] = ' '
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
                if df_off.loc[(df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                        df_off['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + (
                                int(sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID])) * df_off.loc[
                            (df_off['EmployeeID'] == nurse.nurse_ID) & (df_off['ShiftID'] == shift.shift_ID) & (
                                        df_off['Day'] == day - 1)].Weight.item())

                # check if nurse has request for this shift, day
                if df_on.loc[(df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                        df_on['Day'] == day - 1)].Weight.any():
                    # if yes, add to obj_requests if violated
                    obj_requests = obj_requests + (
                                (1 - int(sol.get_value(x[nurse.numerical_ID, day, shift.numerical_ID]))) * df_on.loc[
                            (df_on['EmployeeID'] == nurse.nurse_ID) & (df_on['ShiftID'] == shift.shift_ID) & (
                                        df_on['Day'] == day - 1)].Weight.item())
        schedule.iloc[nurse.numerical_ID, 15] = obj_requests
        obj_requests_total = obj_requests_total + obj_requests
        obj_requests = 0

    schedule.to_csv('solution_schedule_instance{}.csv'.format(instance.instance_ID))
    print(f'{beta}, {under}, {over}, {obj_requests_total}')
    # write to result file, append: beta, under, over, requests
    with open('results.txt', 'a') as f:
        f.write(f'{beta}, {under}, {over}, {obj_requests_total}\n')

    print(schedule)  # to app st.dataframe(schedule)
    verticalPenalty = under + over
    horizontalPenalty = obj_requests_total
    return verticalPenalty, horizontalPenalty

def string_to_numerical_shift(shiftID, S):
    # look for shift in set S with shiftID string
    for shift in S:
        if shift.shift_ID == shiftID:
            return shift.numerical_ID

def read_instance(inst_id):
    cover = pd.read_csv(r'instances1_24\instance{}\shift_cover_req.csv'.format(inst_id))
    req_on = pd.read_csv(r'instances1_24\instance{}\requests_on.csv'.format(inst_id))
    req_off = pd.read_csv(r'instances1_24\instance{}\requests_off.csv'.format(inst_id))
    staff = pd.read_csv(r'instances1_24\instance{}\staff.csv'.format(inst_id))
    shifts = pd.read_csv(r'instances1_24\instance{}\shifts.csv'.format(inst_id))
    daysOff = pd.read_csv(r'instances1_24\instance{}\daysOff.csv'.format(inst_id))

    time_horizons = [14, 14, 14, 28, 28, 28, 28, 28, 28, 28]

    N = set()
    ID = 0
    for index, row in staff.iterrows():
        # maxshifts split per | first, then by = to get key value pairs
        max_shifts_dict = {}
        list_of_all_max_shifts = row['MaxShifts'].split('|')

        for max_shift in list_of_all_max_shifts:
            list_max_shifts = max_shift.split('=')

            # add to dict
            max_shifts_dict[list_max_shifts[0]] = int(list_max_shifts[1])
            #max_shifts_dict = {list_max_shifts[0]: int(list_max_shifts[1])}

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
