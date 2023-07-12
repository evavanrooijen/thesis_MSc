from model import find_schedule, read_instance
import streamlit as st
import pandas as pd

st.title('Hello World!')
inst = st.sidebar.slider('Select an instance', 1, 2)
st.sidebar.write('Select a nurse to change preference profiles')
st.sidebar.selectbox('Nurse', ['A', 'B', 'C', 'D'])

st.sidebar.write('Current profile:')
st.sidebar.table([[2, 2, 2], [2,2, 2]])

instance = read_instance(inst)
schedule = find_schedule(instance) # returns NSP and sol

st.write(f'Best we can do for instance {inst} is undercoverage of {instance.best_undercover} and overcoverage of {instance.best_overcover}')
st.write(f'Worst-off nurse has penalty off {instance.worst_off_sat}')
show_schedule = st.checkbox('Show schedule')

if show_schedule:
    st.dataframe(schedule)

scores = pd.read_csv(f'C:/Users/EvavR/OneDrive/Documenten/GitHub/thesis_MSc/NSP_benchmark/scores{inst}.csv')
st.dataframe(scores.sort_values('NurseID'))