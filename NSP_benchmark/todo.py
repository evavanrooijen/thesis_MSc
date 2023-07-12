def satisfaction(schedule_nurse, nurse='A'):
    for idx in range(len(schedule_nurse)):
        # recovery_shift(schedule_nurse[idx-1], schedule_nurse[idx+1])
        nr_prior = len(schedule_nurse[:idx].rsplit('_', 1))  # not _ before this index
        return nr_prior  # satisfaction_score = TODO
        # workload_shift(schedule_nurse[idx], nr_prior, with_senior=False) # TODO with senior requires whole schedule, all nurses
        # wish_shift = schedule_nurse[idx] in nurse.wishes_on # TODO check right wish
        # shift_satisfaction = recovery_shift + workload_shift + wish_shift


def evaluate_schedule(schedule, nurse):
    schedule = pd.read_csv(r'D:\EvaR\Documents\GitHub\thesis_MSc\data\shift_cover_req.csv')
    schedule.set_index('nurse', inplace=True)
    satisfaction_all = [satisfaction(row, nurse) for row in schedule]
    return max(min(satisfaction_all))
