import pandas as pd
import numpy as np
import timeit
import csv
import data, model, app

file = 'Code\NSP_benchmark\instances1_24\Instance1.txt'
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
