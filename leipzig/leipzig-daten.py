# %%
import pandas as pd
import numpy as np

pd.set_option("display.max_rows", 100)

# %%
#
# Emissions 2011-2017 from CO2 Bilanz
#

data = [
    (2011, 2012, 2013, 2014, 2015, 2016, 2017, "Bereiche"),
    (3226146, 3357816, 3498206, 3336609, 3406229, 3392678, 3335572, "Gesamt"),
    (1488836, 1526249, 1612484, 1542437, 1537181, 1517865, 1480633, "Wirtschaft"),
    (968704, 1053086, 1094302, 976264, 1026631, 1034257, 1026955, "Private Haushalte"),
    (709541, 715052, 728304, 754432, 778429, 777697, 769514, "Verkehr"),
    (59065, 63429, 63116, 63477, 63989, 62858, 58470, "Kommunale Einrichtungen"),
]
emissions = pd.DataFrame(data[1:], columns=data[0])

# convert to 'long' format
emissions = emissions.melt(id_vars=["Bereiche"], var_name="year", value_name="value")

# convert to kt
emissions["value"] = emissions["value"] / 1000

# add missing columns
emissions["type"] = "real"
emissions["note"] = "Umsetzungsbericht 2018"

# rename category, use required value for total emissions and mark last emissions data entry
emissions.rename(columns={"Bereiche": "category"}, inplace=True)
emissions.loc[
    (emissions["category"] == "Gesamt") & (emissions["year"] == 2017), "note"
] = "last_emissions"

# use year column as index
emissions.set_index("year", inplace=True)
emissions.index = emissions.index.astype(int)

emissions


# %%
#
# Population historic
#

data = pd.read_csv(
    "./12411-0015_flat.csv",
    encoding="latin1",
    sep=";",
    usecols=["Zeit", "BEVSTD__Bevoelkerungsstand__Anzahl"],
    na_values="-",
    parse_dates=["Zeit"],
)
data.rename(columns={"BEVSTD__Bevoelkerungsstand__Anzahl": "value"}, inplace=True)
data = data.groupby("Zeit").sum()
data["year"] = data.index.year

population_historic = data.reset_index().set_index("year")[["value"]]
population_historic.loc[1990, "value"] = 557300

population_historic["category"] = "Einwohner"
population_historic["type"] = "Einwohner"
population_historic.loc[2019, "note"] = "latest"

population_historic

# %%
#
# Population forecast; needed to translate per-capita goals
#

parse_thousands = lambda x: (int(float(x.replace(",", ".")) * 1000))

population_forecast = pd.read_csv(
    "./leipzig-population-forecast-2019.csv",
    header=None,
    usecols=[0, 8],
    names=["year", "value"],
    converters={"value": parse_thousands},
    index_col=["year"],
)
population_forecast["type"] = "geplant"

population_forecast


# %%
#
# Emission goals 2020-2050
#

years = [2020, 2030, 2040]
goals = pd.DataFrame(index=years, data={"per_capita": [4.26, 3.48, 2.93],})

goals["population"] = population_forecast.loc[years]["value"]
goals["value"] = goals.population * goals.per_capita / 1000
goals["note"] = "Klimaschutzkonzept 2014-2020"

goals = goals.append(
    pd.DataFrame(
        index=[2050],
        data={"per_capita": 0.0, "value": 0, "note": "Ratsbeschluss Klimanotstand",},
    )
)
goals["category"] = "Gesamt"
goals["type"] = "geplant"

goals

# %%
#
# Historic emissions
#

years = [1990, 1998, 2005, 2008]
data = {
    "Private Haushalte": [4.79, 2.32, 1.83, 1.81],
    "Wirtschaft": [4.83, 2.66, 2.52, 2.24],
    "Verkehr": [1.69, 2.03, 1.79, 1.48],
}

emissions_historic = pd.DataFrame(data=data, index=years)
emissions_historic["population"] = population_historic.loc[
    emissions_historic.index.values, "value"
]
emissions_historic["Gesamt"] = emissions_historic[
    ["Private Haushalte", "Wirtschaft", "Verkehr"]
].sum(axis=1)

emissions_historic.index.name = "year"
emissions_historic = emissions_historic.reset_index().melt(
    id_vars=["year", "population"], value_name="per_capita", var_name="category"
)

emissions_historic["value"] = (
    emissions_historic.population * emissions_historic.per_capita / 1000
)
emissions_historic["type"] = "real"
emissions_historic["note"] = "Klimaschutzkonzept 2014-2020"
emissions_historic = emissions_historic.set_index("year")

emissions_historic
# %%
#
# Consolidate into single DataFrame
#

columns = ["category", "type", "value", "note"]
consolidated = pd.DataFrame(columns=columns)

# emission data
consolidated = consolidated.append(emissions_historic[columns])
consolidated = consolidated.append(emissions[columns])

# emission goals
consolidated = consolidated.append(goals[columns])

# population
consolidated = consolidated.append(population_historic.loc[2019])

# add header for year
consolidated.index.name = "year"

# rename "value" to "co2"
consolidated.rename(columns={"value": "co2"}, inplace=True)

consolidated

# %%
#
# write CSV
#

consolidated.to_csv("leipzig.csv")
