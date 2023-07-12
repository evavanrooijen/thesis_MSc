import pandas as pd

df = pd.read_csv('requests_on_all_1_Weight.csv')
obj = 0
for day in range(15):
    if ((df.loc[(df['EmployeeID'] == 'A') & (df['ShiftID'] == 'D')& (df['Day'] ==day )].Weight.any())):
        obj = obj + (1 * df.loc[(df['EmployeeID'] == 'A') & (df['ShiftID'] == 'D') & (df['Day'] == day)].Weight).item()

print(obj)
if False:
    for nurse in ['A']:
        for shift in ['D']:
            for day in range(14):
                if len(req_on.loc[req_on['EmployeeID'] == nurse].loc[req_on['ShiftID'] == shift].loc[req_on['Day'] == day])<=0:
                    req_on.loc[len(req_on.index)] = [nurse, day, shift, 0]
                try:
                    print(req_on.loc[req_on['EmployeeID'] == nurse].loc[req_on['ShiftID'] == shift].loc[req_on['Day'] == day].Weight[0])
                except KeyError:
                    print('fout')

    print(req_on)
    req_on.set_index('EmployeeID', inplace=True)
    req_on.to_csv('filled_req_on.csv')
    inst_1.req_on = req_on
    for nurse in inst_1.N:
        for shift in inst_1.S:
            for day in range(inst_1.horizon+1):
                print(nurse.nurse_ID)
                print(day)
                try:
                    print(req_on.loc[((req_on['EmployeeID'] == nurse.nurse_ID) & (req_on['Day'] == day))])
                    #print(req_on.loc[req_on['EmployeeID'] == nurse.nurse_ID].loc[req_on['ShiftID'] == shift.shift_ID].loc[req_on['Day'] == day])
                except KeyError:
                    print(f'foutje {nurse.nurse_ID} {shift.shift_ID} {day}')


    # nurse0.shifts_on_req.append(Request(1, 'A', 'D', 2, 2))
    # nurse0.shifts_on_req.append(Request(1, 'A', 'D', 2, 3))
    # nurse1.shifts_on_req.append(Request(2, 'B', 'D', 3, 0))
    # nurse1.shifts_on_req.apend(Request(2, 'B', 'D', 3, 1))
    # nurse1.shifts_on_req.append(Request(2, 'B', 'D', 3, 2))
    # nurse1.shifts_on_req.append(Request(2, 'B', 'D', 3, 3))
    # nurse1.shifts_on_req.append(Request(2, 'B', 'D', 3, 4))
    # nurse2.shifts_on_req.append(Request(2, 'C', 'D', 1, 0))
    # nurse2.shifts_on_req.append(Request(2, 'C', 'D', 1, 1))
    # nurse2.shifts_on_req.add(Request(2, 'C', 'D', 1, 2))
    # nurse2.shifts_on_req.add(Request(2, 'C', 'D', 1, 3))
    # nurse2.shifts_on_req.add(Request(2, 'C', 'D', 1, 4))
    # nurse3.shifts_on_req.add(Request(2, 'D', 'D', 2, 8))
    # nurse3.shifts_on_req.add(Request(2, 'D', 'D', 2, 9))
    # nurse5.shifts_on_req.add(Request(2, 'F', 'D', 2, 0))
    # nurse5.shifts_on_req.add(Request(2, 'F', 'D', 2, 1))
    # nurse7.shifts_on_req.add(Request(2, 'H', 'D', 1, 9))
    # nurse7.shifts_on_req.add(Request(2, 'H', 'D', 1, 10))
    # nurse7.shifts_on_req.add(Request(2, 'H', 'D', 1, 11))
    # nurse7.shifts_on_req.add(Request(2, 'H', 'D', 1, 12))
    # nurse7.shifts_on_req.add(Request(2, 'H', 'D', 1, 13))
