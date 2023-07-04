from dowhy import CausalModel
from IPython.display import Image, display
import pandas as pd
df = pd.read_csv('testCase.csv', delimiter=';')
df.info()


model= CausalModel(
        data = training,
        graph=causal_graph.replace("\n", " "),
        treatment='consecutiveness',
        outcome='sequence_satisfaction')
model.view_model()
display(Image(filename="causal_model.png"))