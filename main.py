# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

# Import libraries
from __future__ import print_function
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import random
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import seaborn as sns
from os import listdir
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets

Username = ""
PW = ""

username_wells = ""
password_wells = ""


#### Automate data gathering
# UBS
def boaselenium():
    browser = webdriver.Safari()
    browser.maximize_window()
    browser.get("https://onlineservices.ubs.com/olsauth/ex/pbl/ubso/dl")

    username = browser.find_element_by_id("username").send_keys(Username)
    time.sleep(4)
    password = browser.find_element_by_id("password")
    password.send_keys(PW)
    password.send_keys(Keys.RETURN)
    time.sleep(10)
    return (print("1"))


def boaselenium2():
    browser = webdriver.Safari()
    browser.maximize_window()
    browser.get("https://connect.secure.wellsfargo.com/auth/login/present?origin=cob&error=yes")

    time.sleep(random.random())
    username = browser.find_element_by_id("j_username").send_keys(username_wells)
    time.sleep(random.random() + 4)
    password = browser.find_element_by_id("j_password")
    password.send_keys(password_wells)
    time.sleep(random.random() + 3)
    password.send_keys(Keys.RETURN)
    time.sleep(10)
    return (print("1"))


#### Read in Wells Fargo Data manually and format
# Read Wells Fargo Spending Report CSV
statement = pd.read_csv(
    "/Users/zacharybarkley/PycharmProjects/pythonProject/WellsFargoStatements/Statements/All_Payment_Methods021021.csv")
statement.index = pd.to_datetime(statement['Date'], format='%m/%d/%Y')
statement['Amount'] = statement['Amount'].str.replace(',', '')
statement['Amount'] = statement['Amount'].str.replace('$', '')
statement.Amount = statement.Amount.astype(float)
print(statement)

# Import Wells Fargo Checking Report
Checking2020 = pd.read_csv(
    "/Users/zacharybarkley/PycharmProjects/pythonProject/WellsFargoStatements/Checking/WellsFargoChecking2020.csv",
    names=['Date', 'Amount', 'Nothing1', 'Nothing2', 'Description'])
Checking2020.index = pd.to_datetime(Checking2020['Date'], format='%m/%d/%Y')

#### Manipulate data for charting and analysis
# Wells Fargo Spending report wrangling
statementWeek = statement.groupby(pd.Grouper(freq='M')).sum()
statementWeek['SMA_5'] = statementWeek.iloc[:, 0].rolling(window=5).mean()
statementWeek['Mean'] = statementWeek.iloc[:, 0].mean()
statementWeek['Ticklabels'] = [ item.strftime('%b %y') for item in statementWeek.index]


# Slicing on a given category or subcategory *should write this as function and change var names*
def catGrab(catLevel='Master Category', spendCat='Food/Drink', interval='W', ceil=150, goal=100, start='2020-11-01',
            end='2020-12-01', slicer=True):
    if slicer == True:
        cat = statement.loc[lambda df: df[catLevel] == spendCat, :]
    else:
        cat = statement

    cat1 = cat.sort_index()
    cat2 = cat1.loc[start:end]

    catInterval = cat2.groupby(pd.Grouper(freq=interval)).sum()

    catInterval['SMA_5'] = catInterval.iloc[:, 0].rolling(window=5).mean()
    catInterval['Mean'] = catInterval.iloc[:, 0].mean()

    catInterval['Ceiling'] = ceil

    if interval == 'W':
        catInterval['Ceiling'] = ceil
    elif interval == 'M':
        catInterval['Ceiling'] = ceil * 4.2
    elif interval == 'd':
        catInterval['Ceiling'] = ceil / 7
    elif interval == 'y':
        catInterval['Ceiling'] = ceil * 52
    else:
        catInterval['Ceiling'] = ceil

    if interval == 'W':
        catInterval['Goal'] = goal
    elif interval == 'M':
        catInterval['Goal'] = goal * 4.2
    elif interval == 'd':
        catInterval['Goal'] = goal / 7
    elif interval == 'y':
        catInterval['Goal'] = goal * 52
    else:
        catInterval['Goal'] = goal

    return catInterval

# Get list of all subcategories
subcategories = statement["Subcategory"].unique()
print(subcategories)

start = (dt.date.today() - dt.timedelta(weeks=52)).strftime('%m/%d/%Y')
end = dt.date.today().strftime('%m/%d/%Y')
catIntervalFood = catGrab(interval='W', start=start, end=end)
catIntervalGas = catGrab(interval='W', catLevel='Subcategory', spendCat='Gasoline', start=start, end=end, goal=50, ceil=60)
catIntervalSpend = catGrab(start=start, end=end, goal=850, ceil=1250, slicer=False)
print(catIntervalGas)

# Wells Fargo Checking Wrangling
Checking2020Income = Checking2020[Checking2020['Description'].str.contains("DFAS")]
totalNetIncome = Checking2020Income['Amount'].sum()

#### Plot and print output
# Plot total spending by week
# statementWeek.plot(y=['Amount', 'SMA_5', 'Mean'])
fig, axes = plt.subplots(2,2)
catIntervalSpend.plot.line(ax=axes[0,0], y=['Amount', 'SMA_5', 'Mean', 'Ceiling', 'Goal'])
catIntervalFood.plot(ax=axes[1,1], y=["Amount", "SMA_5", "Mean", "Ceiling", "Goal"])
catIntervalGas.plot(ax=axes[1,0], y=["Amount", "SMA_5", "Mean", "Ceiling", "Goal"])
ax5 = statementWeek.plot.bar(ax=axes[0,1],y='Amount')
pd.options.plotting.matplotlib.register_converters = True
ax5.xaxis.set_major_formatter(ticker.FixedFormatter(statementWeek.Ticklabels))
#ax6 = statementWeek.plot.line(ax=ax5,y='SMA_5')a


# Make html dash
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1('Financials'),

    html.Div('Total Expended Per Week'),
    dcc.Graph(
        id='example-graph3',
        figure= px.line(catIntervalSpend, y=["Amount", "SMA_5", "Mean", "Ceiling", "Goal"]),
    ),
    dcc.Graph(
        id='example-graph',
        figure= px.line(catIntervalFood, y=["Amount", "SMA_5", "Mean", "Ceiling", "Goal"]),
    ),
    dcc.Graph(
        id='example-graph2',
        figure= px.line(catIntervalGas, y=["Amount", "SMA_5", "Mean", "Ceiling", "Goal"]),
    ),
dcc.Graph(
        id='example-graph4',
        figure= px.bar(statementWeek, y="Amount"),
    )



]
)

if __name__ == '__main__':
    app.run_server(debug=True)


# Print net income Checking
print(totalNetIncome)

# Plot bi-weekly income
# Checking2020Income.plot(y='Amount')

#plt.show()

plt.close("all")

#### Experiment
# print(catIntervalFood)
print(statementWeek)
