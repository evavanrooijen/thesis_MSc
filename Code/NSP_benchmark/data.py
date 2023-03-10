# functions to import, preprocess and visualize data
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

cover = pd.read_csv(r'Code\NSP_benchmark\shift_cover_req.csv')
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
