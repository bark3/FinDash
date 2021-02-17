# This code creates a financial dashboard to track spending, saving, and budgeting habits. Currently it only pulls from
# a few different financial sources. This code is also heavily customized to my specific financial institutions, so a
# decent amount of editing is required to repurpose this for your specific needs.

# Additionally, there are deprecated sections that I leave inside the code in case I want to use them at some point. I
# will designate these sections in their comment as "D!".

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

# D! Passwords should not be hardcoded. I used this only in the testing phase of the automated data gathering. Since wells
# fargo's login is pretty robust to bot entry, I don't use these two functions, but kept them in the event I wanted to
# in the future.
Username = ""
PW = ""

username_wells = ""
password_wells = ""


#### D!. Automate data gathering
# UBS
def ubssselenium():
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


def welselenium2():
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
# Read Wells Fargo Spending Report CSV. This section will need to be repurposed for your own file structure and bank
# statement(s).
statement = pd.read_csv(
    "/Users/zacharybarkley/PycharmProjects/pythonProject/WellsFargoStatements/Statements/All_Payment_Methods021321.csv")
statement.index = pd.to_datetime(statement['Date'], format='%m/%d/%Y')
statement['Amount'] = statement['Amount'].str.replace(',', '')
statement['Amount'] = statement['Amount'].str.replace('$', '')
statement.Amount = statement.Amount.astype(float)


#D! Import Wells Fargo Checking Report
Checking2020 = pd.read_csv(
    "/Users/zacharybarkley/PycharmProjects/pythonProject/WellsFargoStatements/Checking/WellsFargoChecking2020.csv",
    names=['Date', 'Amount', 'Nothing1', 'Nothing2', 'Description'])
Checking2020.index = pd.to_datetime(Checking2020['Date'], format='%m/%d/%Y')

# Import Wells Fargo Checking Activity
check = pd.read_csv("/Users/zacharybarkley/PycharmProjects/pythonProject/WellsFargoStatements/Checking Activity/Checking1.csv",
                    names=['Date', 'Amount', 'Identifier', 'DELETE', 'Title'])
check.index = pd.to_datetime(check['Date'], format='%m/%d/%Y')
print(check.dtypes)



#### Manipulate data for charting and analysis
# Wells Fargo Spending report wrangling
statementWeek = statement.groupby(pd.Grouper(freq='M')).sum()
statementWeek['SMA_5'] = statementWeek.iloc[:, 0].rolling(window=5).mean()
statementWeek['Mean'] = statementWeek.iloc[:, 0].mean()
statementWeek['Ticklabels'] = [ item.strftime('%b %y') for item in statementWeek.index]

# Wells Fargo Checking Activity. The CheckInit initializes the cumulative sum since it was the closing balance at the
# start of my data.
checkInit = 173.63
interim = check.sort_index()
interim['Amount'] = interim['Amount'].cumsum() + checkInit
checkBalance = interim.groupby(pd.Grouper(freq='d')).last().ffill()

print(checkBalance['Amount'])


# Function to format multiple different data frames for different charts.
def catGrab(catLevel='Master Category', spendCat='Food/Drink', interval='W', ceil=150, goal=100, start='2020-11-01',
            end='2020-12-01', slicer=True, excludeColumn='Master Category', exclude=['']):
    if slicer == True:
        cat = statement.loc[lambda df: df[catLevel] == spendCat, :]
    else:
        cat = statement

    mask = cat[excludeColumn].isin(exclude)
    cat = cat[~mask]

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

start = (dt.date.today() - dt.timedelta(weeks=90)).strftime('%m/%d/%Y')
end = dt.date.today().strftime('%m/%d/%Y')
catIntervalFood = catGrab(interval='M', start=start, end=end)
catIntervalGas = catGrab(interval='W', catLevel='Subcategory', spendCat='Gasoline', start=start, end=end, goal=50, ceil=60)
catIntervalSpend = catGrab(start=start, end=end, goal=850, ceil=1250, slicer=False, exclude=['Outgoing Transfers'])


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
        id='example-graph5',
        figure= px.line(checkBalance, y=["Amount"]),
    ),

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


# Plot bi-weekly income
# Checking2020Income.plot(y='Amount')

#plt.show()

plt.close("all")

#### Experiment
# print(catIntervalFood)

