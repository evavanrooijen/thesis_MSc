
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
