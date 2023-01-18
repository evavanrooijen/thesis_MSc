import streamlit as st

import streamlit as st
import pandas as pd
import numpy as np

import datetime

st.sidebar.title('Selecteer opties: ')

d = st.sidebar.date_input(
    "Startdatum rooster:",
    datetime.date(2023, 1, 1))

nurse = st.sidebar.selectbox('Voor wie is het rooster?', ['A', 'B', 'C'])

st.title(f'Rooster tevredenheid')
st.subheader(f'Rooster van verpleegkundige {nurse}')
data = pd.read_csv('schedule.csv', delimiter=';', index_col=0, keep_default_na = False)
st.table(data.head())
st.write('Start van dit rooster:', d)

show_schedule = st.sidebar.checkbox('Print rooster')

# open nurses file to add nurse
add_schedule = st.sidebar.button('Rooster toevoegen')

pref_consecutiveness = st.slider('Hoeveel waardeer je opeenvolgendheid van diensten?: ', 0, 5)
pref_weekend = st.slider('Hoeveel waardeer je weekend diensten t.o.v. doordeweeks?: ', 0, 5)
pref_night = st.slider('Hoeveel waardeer je nacht diensten t.o.v. dag of avond? ', 0, 5)
pref_weekend_night = pref_weekend*pref_night #st.slider('Preference weekend + night: ', 0, 5)
pref_variability = st.slider('Ik heb graag afwisseling in de dientsten die ik draai', 0, 5)

if st.checkbox('Laat eigenschappen van dit rooster zien: '):
    st.write('Opeenvolgendheid alle diensten: 4 ')
    st.write(f'Opeenvolgendheid nachtdiensten: {1}')
    st.write('Aantal weekend diensten t.o.v. doordeweeks: 1')
    st.write('Aantal nachtdiensten t.o.v. dag en avond: 2')

    st.write('Afwisseling in diensttypes: 0')
    st.write('Afwisseling in locaties: 0')

satisfaction_score = pref_consecutiveness/5 *4+pref_weekend/5*1+pref_night/5*2+pref_variability/5*0+pref_weekend_night/5*1
st.write(f'Tevredenheidsscore: {satisfaction_score}')

add_profile = st.checkbox('Maak nieuw verpleegkundige profiel aan', True)

# open nurses file to add nurse
if add_profile == True: #st.sidebar.button('Profiel toevoegen'):
    st.write('Maak nieuw verpleegkundige profiel aan')
    name = st.text_input('Naam')
    age = st.slider('Leeftijd', 18, 65)
    role = st.multiselect(
        'Wat is de functie?',
        ['stagiar', 'jongste', 'oudste', 'admin'])
    distance_to_work = st.slider('Afstand naar werk (km)', 0, 50 )
    allowed_activities = st.multiselect(
        'Welke activiteiten mogen er gedaan worden?',
        ['alles', ' '])

    pref_variability1 = st.slider('Ik weet graag zo ver mogelijk van tevoren wanneer ik werk: ', 0, 5)
    pref_variability1 = st.slider('Ik neem vaak andermans diensten over: ', 0, 5)

    pref_variability1 = st.slider('Ik wissel vaak mijn diensten vanwege persoonlijke afspraken  (tijdsprobleem): ', 0, 5)
    pref_variability1 = st.slider('Ik wissel vaak mijn diensten vanwege voorkeur voor andere dienst types: ', 0, 5)

    pref_variability1 = st.slider('Ik vind het vervelend om flexibel ingezet te worden op verschillende afdelingen (flexpool groep afdelingen): ', 0, 5)
    pref_variability1 = st.slider('Ik vind het vervelend om flexibel ingezet te worden op verschillende diensten (flexpool eigen afdeling): ', 0, 5)


    if st.button('Profiel toevoegen'):

        # Set up an output csv file with column headers
        with open('nurses.csv','a') as f:
            # Name;Role;Distance;list_activities;cluster
            f.write(f"{name}; {role}; {distance_to_work};{allowed_activities}")
            f.write("\n")
            add_profile = False

#st.subheader('Tevredenheid van deze roosterronde ')
# utility per groep -> max difference, max utility, min utility, average
