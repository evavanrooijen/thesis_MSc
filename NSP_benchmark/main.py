from model import read_instance

for inst in range(1, 2):
    instance = read_instance(inst)
    NSP, sol = instance.find_schedule()
    schedule = instance.process_solution(NSP, sol)

    #schedule = find_schedule(instance, weight_over=1, weight_under=100)  # returns NSP and
    # for nurse in instance.N:
    #     if nurse.numerical_ID == 7:
    #         nurse.pref_max_cons = 2
    #         nurse.pref_min_cons = 4 # TODO: min meenemen in berekenen consecutiveness penalty
    # schedule = find_schedule(instance, weight_over=1, weight_under=100) # returns NSP and sol

# # TEST: vary alpha for nurse between 0, 1 and see if it increases (where possible)
# instance= read_instance(1)
# for alpha in range(11):
#     #[0.1, 0.2, 0.3, 0.4, 0.5]:
#     alpha = alpha/10 + 0.000000001
#     print(alpha)
#     for nurse in instance.N:
#         if nurse.numerical_ID == 2:
#             nurse.pref_alpha = alpha
#     find_schedule(instance, test_ID=alpha)