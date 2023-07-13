from model import find_schedule, read_instance
import streamlit as st
import pandas as pd

filepath = 'C:/Users/EvavR/OneDrive/Documenten/GitHub/thesis_MSc/NSP_benchmark/instances1_24'

st.title('Hello World! [nurse view]')

st.sidebar.title('Options')
st.sidebar.header('Instance')
st.sidebar.write('Select an instance')
inst = st.sidebar.slider('Instance', 1, 2)
st.sidebar.header('Preferences')
st.sidebar.write('Select a nurse')

@st.cache_data
def load_instance(inst):
    return read_instance(inst)

instance = load_instance(inst)
list_of_nurse_IDs = []
for nurse in instance.N:
    list_of_nurse_IDs.append(nurse.nurse_ID)

nurse_ID = st.sidebar.selectbox('Nurse', sorted(list_of_nurse_IDs))
st.sidebar.subheader('Set consecutiveness preferences')

for nurse in instance.N:
    if nurse.nurse_ID == nurse_ID:
        nurse.pref_min_cons = st.sidebar.number_input('Min consecutive shifts', min_value=1, max_value=7, value=2,
                                                      step=1,
                                                      key='min{}'.format(nurse.numerical_ID))
        nurse.pref_max_cons = st.sidebar.number_input('Max consecutive shifts', min_value=1, max_value=7, value=4,
                                                      step=1, key='max{}'.format(nurse.numerical_ID))

st.sidebar.subheader('Set weights')
st.sidebar.write('alpha is the weight assigned to consecutiveness compared to incidental requests')
for nurse in instance.N:
    if nurse.nurse_ID == nurse_ID:
        nurse.pref_alpha = st.sidebar.slider('alpha*', 0.0, 1.0, 0.5, step=0.1)

schedule = find_schedule(instance)  # returns NSP and sol

st.write(
    f'Best we can do for instance {inst} is undercoverage of {instance.best_undercover} and overcoverage of {instance.best_overcover}')
st.write(f'Worst-off nurse has penalty off {instance.worst_off_sat}')

show_nurses = st.checkbox('Show nurses ')
if show_nurses:
    for nurse in instance.N:
        st.write(nurse)

show_schedule = st.checkbox('Show schedule ')
if show_schedule:
    st.dataframe(schedule)

# print coverage scores

# print satisfaction scores
scores = pd.read_csv(f'{filepath}/instance{instance.instance_ID}/satisfaction_scores{instance.instance_ID}.csv')
st.dataframe(scores.sort_values('NurseID').set_index('NurseID'))
