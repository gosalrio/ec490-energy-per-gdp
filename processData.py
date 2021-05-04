import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pickle
import os

path = "/home/ken/Documents/SP21/EC490/API_NY.GDP.MKTP.CD_DS2_en_csv_v2_2017804"
os.chdir(path)

energyRaw = pd.read_csv("Energy.csv")
gdpRaw = pd.read_csv("GDP.csv")
metadataRaw = pd.read_csv("metadata.csv")
renewableEnergy = pd.read_csv("renewable-share-energy.csv")
internetAdoption = pd.read_csv("share-of-individuals-using-the-internet.csv")
employmentRate = pd.read_csv("DP_LIVE_07042021220848110.csv")
education = pd.read_csv("mean-years-of-schooling-1.csv").rename(columns = {"Average Total Years of Schooling for Adult Population (Lee-Lee (2016), Barro-Lee (2018) and UNDP (2018))": "Years_of_Schooling"})

with open("populationArr.pickle", 'rb') as file:
    populationArr = pickle.load(file)
    populationDF = pd.DataFrame(populationArr, columns=["Country", "Population"])

#Dictionaries
USSR_countries = {'Azerbaijan', 'Ukraine', 'Belarus',
                  'Estonia', 'Turkmenistan', 'Moldova',
                  'Tajikistan', 'Georgia', 'Lithuania',
                  'Russia', 'Uzbekistan', 'Kyrgyzstan',
                  'Latvia', 'Kazakhstan', 'Armenia'}
with open('EU_countries.pickle', 'rb') as file:
    EU_countries = pickle.load(file)

#Land Data
with open('landData.pickle', 'rb') as f:
    # The protocol version used is detected automatically, so we do not
    # have to specify it.
    landDataDict = pickle.load(f)
landDataSeries = pd.Series(data = landDataDict)

#Process Employment
employmentRate = pd.merge(employmentRate, metadataRaw,
                          how="inner", left_on="LOCATION",
                          right_on="Country Code")

metadata = metadataRaw.loc[:, ['IncomeGroup', 'Country']].set_index('Country')

countries = list(x.strip() for x in list(energyRaw.T.loc['Country']))

data = pd.DataFrame(columns = ["Year", "Country", "GDP", "Energy"])
gdpRefined = gdpRaw.set_index('Country Name').iloc[:,23:]

# handle energy and gdp
i = 0
for index, gdps in energyRaw.T.iloc[1:].items():
    for year, energy in gdps.iteritems():
        try:
            gdp = gdpRefined.loc[countries[i]].loc[str(year)]
        except KeyError:
            gdp = 0
            
        data = data.append({
                'Year': year,
                'Country': countries[i],
                'GDP': gdp,
                'Energy': energy if not gdp == 0 else 0
            }, ignore_index=True)
    i += 1

data.dropna(inplace=True)
data = data[data['Energy'] != '--']
data['Energy'] = data['Energy'].astype(np.float64)
data['energyPerGDP'] = data.Energy / data.GDP #should be a decreasing scheme
data.Year = data.Year.astype(int)

data = pd.merge(data, metadata, on="Country", how="left")
data = pd.merge(data,
                landDataSeries.replace(',', '', regex=True)\
                .astype(np.float).to_frame().rename(columns = {0: "Size"}),
                left_on="Country", right_index=True,
                how="left")
data = pd.merge(
    data,
    renewableEnergy.loc[:, ["Year", "Entity","Renewables (% sub energy)"]],
    how="left",
    left_on=["Year","Country"],
    right_on=["Year", "Entity"]
    ).drop(["Entity"], axis=1).rename(columns = {"Renewables (% sub energy)":
                                                 "Renewables"})
data["Renewables"] = data["Renewables"].fillna(0)

data = pd.merge(
    data,
    internetAdoption.loc[:, ["Year", "Entity", "Individuals using the Internet (% of population)"]],
    how="left",
    left_on=["Year","Country"],
    right_on=["Year", "Entity"]
    ).drop(["Entity"], axis=1).rename(columns = {"Individuals using the Internet (% of population)":
                                                 "Internet"})
data["Internet"] = data["Internet"].fillna(0)

data = pd.merge(
    data, employmentRate.loc[:, ["TIME", "Country", "Value"]],
    how="left", left_on=["Year", "Country"],
    right_on=["TIME", "Country"]).rename(columns = {"Value": "Employment"})

data = pd.merge(
    data,education.loc[:, ["Year", "Years_of_Schooling", "Entity"]],
    left_on=["Year", "Country"], right_on=["Year", "Entity"],
    how="left").drop(columns=["Entity"])

#Population data merge
data = data.merge(populationDF, how="left", on="Country")

data["TIME"] = data.Year - 1980
data["Developed"] = data.IncomeGroup == "High"
data.energyPerGDP = data.energyPerGDP * (10**9)

data.to_excel("final.xlsx")

dataByCountry = pd.DataFrame(np.arange(1980, 2020), columns=['Year'])
for country in data[data['IncomeGroup'] == 'High'].Country.unique(): #only for high income countries
##for country in data.Country.unique():
    dataByCountry = dataByCountry.merge(
        data[data['Country'] == country].set_index('Year').loc[:,['energyPerGDP']].rename(columns = {'energyPerGDP': country}),
        left_on="Year", right_on="Year", how="left")

dataByCountry.set_index('Year', inplace=True)
dataByCountry = dataByCountry * np.float(10**9) #convert from billions of kWh to kWh

def getCorrForCountry(data, country):
    workingData = data[data.Country == country]
    return np.corrcoef(workingData.Energy, workingData.GDP)

##countries = ['Netherlands', 'United Kingdom',
##             'United States', 'Singapore', 'Germany',
##             'Norway', 'Australia', 'Japan']
##dataByCountry.loc[:, countries].plot()
##lowCountries = ['Chad', 'Ethiopia', 'Gambia, The', 'Guinea',
##                'Guinea-Bissau', 'Haiti', 'Liberia', 'Madagascar', 'Mali',
##                'Mozambique', 'Niger', 'Rwanda', 'Sierra Leone', 'Somalia',
##                'South Sudan', 'Sudan', 'Tajikistan', 'Togo', 'Uganda']

#Special Case low countries
##["Afghanistan", "Eritrea", "Central African Republic",
## "Malawi", "Mozambique", "Tajikistan"]

def percentChangeIncomeGroup(data, incomeGroup):
    df = data.loc[(data.Year > 1990) &
                  (data.IncomeGroup == incomeGroup) &
                  ~(data.Country.isin(USSR_Countries)) &
                  (data.Country != "Timor-Leste"),
                  ["energyPerGDP", "Country", "Year"]]
    percentChange_dict = {}
    for country in df.Country.unique():
        dataSet = df.loc[df.Country == country].dropna()
        percentChange_dict[country] = (dataSet.iloc[-1, 0] - dataSet.iloc[0, 0]) \
                                            / dataSet.iloc[0, 0] #new - old / old
    return pd.Series(percentChange_dict).sort_values(ascending=False)*100

#Plot high income example
##(percentChange_high.sort_values(ascending=False)*100).plot(kind="bar", ylabel="Energy/$ Changes in %")
##plt.hlines(0, 0, len(percentChange_high.values), colors="red")

## Upper Middle Class Countries only from 1980 - 2018 because some data is missing
##upperMiddleCountries = (dataByCountry.loc[1980:2018, data[data.IncomeGroup == "Upper middle"].Country.unique()])
##upperMiddleCountries.loc[:,
##(upperMiddleCountries < 0.9).all()].plot(legend=None, ylabel="Energy Efficiency (kWh/$)")
##plt.show()

def getGDPMinMax(data, incomeGroup, max):
    df = data[data.Country.isin(data[data.IncomeGroup == incomeGroup].Country.unique())]
    return df[df.Year > 2015].GDP.max() if max else df[df.Year > 2015].GDP.min()

##getGDPMinMax(data, "Lower middle", True)

corrDict = dict()
for country in data.Country.unique():
	corrDict[country] = getCorrForCountry(data, country)[0][1]
	
print(pd.Series(corrDict)[pd.Series(corrDict).notna()].sort_values().median())
print(pd.Series(corrDict)[pd.Series(corrDict).notna()].mean())

##How many times the US Energy usage is compared to Uganda
data.loc[(data.Country == "United States") & (data.Year == 2018),
         ["GDP", "Energy", "Year"]].Energy.iloc[0] / data.loc[
             (data.Country == "Uganda") & (data.Year == 2018),
             ["GDP", "Energy", "Year"]].Energy.iloc[0]
