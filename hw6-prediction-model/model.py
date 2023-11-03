
import pandas as pd
import sklearn


## Fetch data and preprocess
raw_data = pd.read_csv('/data.csv')
ip_model_data = raw_data.drop(['gender', 'age', 'income', 'is_banned', 'time_of_day', 'requested_file'], axis=1)

