schedule_nurse=['_', '_', 'D', 'D', 'D', 'D', '_']
schedule_nurse = '__DDDD_'

for idx in range(len(schedule_nurse)):
    if schedule_nurse[idx] is not '_':
        if schedule_nurse[idx-1] is '_':
            print(0)
        elif schedule_nurse[idx-2] is '_':
            print(1)
        elif schedule_nurse[idx-3] is '_':
            print(2)
        elif schedule_nurse[idx-4] is '_':
            print(3)
        else:
            print(' ERROR: nr prior miscalculated')

print(schedule_nurse.rsplit('_', 4)) # not _ before this index, nr prior shifts