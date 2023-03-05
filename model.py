# find_schedule, update_preferences

# find_schedule: given instance and model solve NSP
def find_schedule(instance):
    # define MIP
    # demo: have shifts to cover and set of nurses with different weekend preferences (check CAO!)
    # by changing their weekend tolerance, show differences in schedule
    # some like weekends: pay others do not: personal life

    NSP = Model('NSP')
    #NSP.context.cplex_parameters.mip.tolerances.mipgap = 0 # check if gap is always 0 ensured
    NSP.set_time_limit(1*60) # in seconds CHECK
    x = NSP.binary_var_matrix(N_nurses, N_shifts, name = "x")

    obj_fn = sum(values[i]*p[i] for i in range(n))
    NSP.set_objective('max', obj_fn)

    NSP.solve()
    return NSP 
    gap = NSP.solve_details.mip_relative_gap
    #print(f"Optimal objective value z = {NSP.objective_value}")

    # visualize schedule, who works when

    # functions take solution as input and transform to readable schedule
    # get schedule_per_nurse(i)
    # get all shifts with nurse i
    outcome = []
    for v in NSP.iter_binary_vars():
        outcome.append(int(v.solution_value))
        #print(outcome)
    return NSP.objective_value, gap


    # satisfaction is dan assigned_weekends/preference_weekends en maxmin

    # objective: maxmin satisfaction + penalty unassigned shifts

    # constraints: copied from benchmark

    # max one shift per day

    # min full day rest between shifts (forward rotation)

    # cover requirements

    # solve



# update_preferences: given changes and nurse objects, update their preference parameters/profile
def nurse_schedule_satisfaction(nurse, schedule):
    # from schedule get consecutiveness, workload etc.

    # flexibility, worklaod

    satisfaction = None
    return satisfaction

def dept_schedule_satisfaction(dept_satisfactions):
    return (min(dept_satisfactions)) # objective is maximization of min

def update_preferences(changes):
    for change in changes:

    # create table with changes by nurse

    for nurse in nurses_changed:
        train_satisfaction(nurse, changes[nurse])
