# functions to import, preprocess and visualize data
import pandas as pd
import numpy as np
import csv
import timeit

# classes: instance, nurse, schedule

# instance has nurses, shifts, ..
class Instance:
    nurses: set  # I
    time_horizon: int # h
    days: set # D
    weekends: set # W
    shift_types: set # T
    shift_types_not_allowed: set # R_t
    days_off: set # N_i
    length_shift: dict # l_t

    # find schedule

# nurse has personal characteristics and preference parameters
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
    loads: [] # init=False

  def __init__(self, days_off, MaxShifts, MaxTotalMinutes, MinTotalMinutes, MaxConsecutiveShifts, MinConsecutiveShifts, MinConsecutiveDaysOff, MaxWeekends, on_requests, off_requests):
    self.name = name
    self.age = age

    def __post_init__(self):
        self.satisfaction = 0

    def calc_satisfaction(self, sat_param):
        load = 8
        rest = 2
        self.satisfaction = load + rest

  def __str__(self):
    return f"{self.name}({self.age})"

p1 = Person("John", 36)

print(p1)

# shift has characteristics (time, activities, nurse)
@dataclass
class Shift:
    shift_ID: str
    length_in_min: int
    cover_req: dict
    shifts_cannot_follow_this: list

  def __str__(self):
    return f"{self.name}({self.age})"

p1 = Person("John", 36)

print(p1)



# schedule is assignment of shifts to nurses (maybe not needed)
# for this instance, horizon, shifts, nurses, assignment who what when

def import_instance(file):
    # returns an instance of the instance class

    file = open(file, 'r')
    print(file.readline())
    for line in file.readline():
        print(line)

    #first_line = file.readline().strip().split(' ')
    #values = list(file.readline().strip().split(' '))
    #values = [int(value) for value in values]
    #weights = list(file.readline().strip().split(' '))
    #weights = [int(value) for value in weights]
    #n, B = first_line

    file.close()
    return None

# tests

print(read_instance('NSP_benchmark\instances1_24\Instance1.txt'))

file = r"Code\NSP_benchmark\instances1_24\Instance1.txt"
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
