

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


import pandas as pd
from dataclasses import dataclass, field
from docplex.mp.model import Model
from model import find_schedule, read_instance

instance = read_instance(1)

# solve LP to find base schedule
OG_schedule = find_schedule(instance)
#
# # publish schedule
# publish_schedule(OG_schedule) # this show the schedule per nurse in the application
#
# # collect changes
# changes = collect_changes(time = 7) # collect changes over 7 days, from publication by setting status planboard to "open marketplace"
#
# # update preference parameters
# update_preferences(changes) # change preferences in nurse objects who have made a change
#
# # solve LP to find improved schedule
# round2 = find_schedule(instance) # nurse objects have updated preferences (consecutiveness/workload-> motivation), soft constraint per (un)desired shift (hygiene)
#
# # this can be done by shift (when nurses ask for change) or collectively after all change behavior is collected (could differ for self-scheduling)
# publish_schedule(round2)
#
# # self-scheduling: if nurse selects shift to (not) work, schedule is optimized to allow suggested changes but this might give early nurses a headstart
# # better to collect all preferred changes and then optimize again incorporating all desired changes
