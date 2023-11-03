
import pandas as pd
import numpy as np
import random
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score


## Fetch data and preprocess
raw_data = pd.read_csv('data.csv', on_bad_lines='skip')
ip_model_data = raw_data.drop(['id', 'gender', 'age', 'income', 'is_banned', 'time_of_day', 'requested_file'], axis=1)

##### Predicting COUNTRY from IP #####

# Split every ip into the individual octets
ip_model_data[['octet1', 'octet2', 'octet3', 'octet4']] = ip_model_data['client_ip'].str.split('.', expand=True)
ip_model_data = ip_model_data.drop(['client_ip', 'octet4'], axis=1)

# Split into train and test set
ip_train, ip_test = train_test_split(ip_model_data, test_size=0.25)

# Use LabelEncoder to convert countries to labels
le = LabelEncoder()
le.fit(ip_model_data['country'])
ip_train['country'] = le.transform(ip_train['country'])
ip_test['country'] = le.transform(ip_test['country'])

X_train = ip_train.drop('country', axis=1)
y_train = ip_train['country']

X_test = ip_test.drop('country', axis=1)
y_test = ip_test['country']

# Use a DecisionTreeClassifier to classify new data rows
clf = DecisionTreeClassifier()
clf.fit(X_train, y_train)

y_predict = clf.predict(X_test)
print("Predicting country from client_ip...")
print("Model testing accuracy:", accuracy_score(y_test, y_predict))


##### Predicting INCOME #####

income_model_data = raw_data.drop(['id', 'is_banned', 'time_of_day'], axis=1)

# Encode labels for country, gender, age, requested_file, client_ip, and income
income_model_data['country'] = le.transform(income_model_data['country'])

ip_le = LabelEncoder()
ip_le.fit(income_model_data['client_ip'])
income_model_data['client_ip'] = ip_le.transform(income_model_data['client_ip'])

income_model_data['gender'] = income_model_data['gender'].map({'Male': 0, 'Female': 1})

age_le = LabelEncoder()
age_le.fit(income_model_data['age'])
income_model_data['age'] = age_le.transform(income_model_data['age'])

income_model_data['requested_file'] = income_model_data['requested_file'].map(lambda x: x.split('.')[0])

income_le = LabelEncoder()
income_le.fit(income_model_data['income'])
income_model_data['income'] = income_le.transform(income_model_data['income'])

income_train, income_test = train_test_split(income_model_data, test_size=0.25)

X_train = income_train.drop('income', axis=1)
y_train = income_train['income']
X_test = income_test.drop('income', axis=1)
y_test = income_test['income']


# Creating custom IncomeModel class
# Strategy: If we're tested on a data point that is an exact duplicate of a row in our training data,
#   predict the income of that data point. Otherwise, use the DecisionTreeClassifier
class IncomeModel():

    def __init__(self):
        self.clf = DecisionTreeClassifier()

    def fit(self, train_data, train_labels):
        self.X_train = train_data
        self.y_train = train_labels
        self.clf.fit(self.X_train, self.y_train)

    def predict(self, test_data):
        clf_predict = self.clf.predict(test_data)

        predictions = []

        for i in test_data.index:
            row = test_data.loc[i]
            matches = (self.X_train == row).all(1)
            if matches.any():
                j = matches[matches].index[0]
                predictions.append(self.y_train.loc[j])
            else:
                idx = test_data.index.get_loc(i)
                predictions.append(clf_predict[idx])

        return predictions

# Creating second custom IncomeModel class
# Strategy: If we're tested on a data point that is an exact duplicate of a row in our training data,
#   predict the income of that data point. Otherwise, predict RANDOMLY
class IncomeModel2():

    def __init__(self):
        pass

    def fit(self, train_data, train_labels):
        self.X_train = train_data
        self.y_train = train_labels

    def predict(self, test_data):
        predictions = []

        for i in test_data.index:
            row = test_data.loc[i]
            matches = (self.X_train == row).all(1)
            if matches.any():
                j = matches[matches].index[0]
                predictions.append(self.y_train.loc[j])
            else:
                predictions.append(random.randrange(0, 8))

        return predictions

# Using normal DecisionTreeClassifier for ALL predictions
# Results in accuracy of approximately 77.5%
clf = DecisionTreeClassifier()
clf.fit(X_train, y_train)

y_predict = clf.predict(X_test)
print("Predicting income with DecisionTreeClassifier...")
print("Model testing accuracy:", accuracy_score(y_test, y_predict))


# Using IncomeModel for our predictions (see above class for explanation)
# Results in accuracy of approximately 77.5%
model = IncomeModel()
model.fit(X_train, y_train)
model_predict = model.predict(X_test)

print("Predicting income with IncomeModel...")
print("Model testing accuracy:", accuracy_score(y_test, model_predict))


# Using IncomeModel2 for our predictions (see above class for explanation)
# Results in accuracy of approximately 77.5%
model2 = IncomeModel2()
model2.fit(X_train, y_train)
model2_predict = model2.predict(X_test)

print("Predicting income with IncomeModel2...")
print("Model testing accuracy:", accuracy_score(y_test, model2_predict))

