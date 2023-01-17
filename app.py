import streamlit as st

import streamlit as st
import pandas as pd
import numpy as np

import datetime

st.sidebar.title('Select options ')

d = st.sidebar.date_input(
    "What's the starting data?",
    datetime.date(2023, 1, 1))

nurse = st.sidebar.selectbox('For whom is this schedule?', ['A', 'B', 'C'])

st.title(f'Happy Nurse: Schedule Satisfaction ')
st.subheader(f'Current Schedule for {nurse} from {d}')
data = pd.read_csv('schedule.csv', delimiter=';', index_col=0, keep_default_na = False)
st.table(data.head())
st.write('Schedule for week starting:', d)

show_schedule = st.sidebar.checkbox('Show schedule')

# open nurses file to add nurse
add_schedule = st.sidebar.button('Rooster toevoegen')

pref_consecutiveness = st.slider('Preference consecutiveness: ', 0, 5)
pref_weekend = st.slider('Preference weekend over weekday: ', 0, 5)
pref_night = st.slider('Preference night shifts (over non-night): ', 0, 5)
pref_weekend_night = st.slider('Preference weekend + night: ', 0, 5)
pref_variability = st.slider('Preference variability: ', 0, 5)

if st.checkbox('Show schedule statistics: '):
    st.write('Consecutiveness: 4 ')
    st.write(f'Consecutiveness night: {1}')
    st.write('Weekend shifts: 1')
    st.write('Night shifts: 2')
    st.write('Weekend + night: 1')

    st.write('Variability shift types: 0')
    st.write('Variability location: 0')

satisfaction_score = pref_consecutiveness/5 *4+pref_weekend/5*1+pref_night/5*2+pref_variability/5*0+pref_weekend_night/5*1
st.write(f'satisfaction score: {satisfaction_score}')


add_profile = st.checkbox('Create new nurse profile', True)

# open nurses file to add nurse
if add_profile == True: #st.sidebar.button('Profiel toevoegen'):
    st.write('Create new nurse profile')
    name = st.text_input('Name')
    age = st.slider('Age', 18, 65)
    role = st.multiselect(
        'What is the role?',
        ['stagair', 'jongste', 'oudste', 'admin'])
    distance_to_work = st.slider('Distance to work (km)', 0, 50 )
    allowed_activities = st.multiselect(
        'What are the allowed activities',
        ['general', 'cleaning', 'surgery', 'secretary'])

    if st.button('Profiel toevoegen'):

        # Set up an output csv file with column headers
        with open('nurses.csv','a') as f:
            # Name;Role;Distance;list_activities;cluster
            f.write(f"{name}; {role}; {distance_to_work};{allowed_activities}")
            f.write("\n")
            add_profile = False

if add_schedule:
    M, D, W, D, V, Z, Z = st.columns(7)

    M.header("Maandag")
    M.selectbox(' ', ['D', 'A', 'N'])
    M.image(original, use_column_width=True)

    D.header("Grayscale")
    D.image(grayscale, use_column_width=True)

DATE_COLUMN = 'date/time'
DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
            'streamlit-demo-data/uber-raw-data-sep14.csv.gz')

@st.cache
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data

data = load_data(10000)

st.subheader('Satisfaction of schedule round by nurse ')
hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0,24))[0]
st.bar_chart(hist_values)

# Some number in the range 0-23
hour_to_filter = st.slider('hour', 0, 23, 17)
filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]

st.subheader('Map of all pickups at %s:00' % hour_to_filter)
st.map(filtered_data)
