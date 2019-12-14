#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import numpy as np

def emissions_historic(population):
    data = [
        (2011, 2012, 2013, 2014, 2015, 2016, 'Bereiche'),
        (6.42, 6.45, 6.63, 6.21, 6.15, 5.96, 'Gesamt'),
        (3.13, 3.05, 3.21, 3.04, 2.93, 2.79, 'Wirtschaft und Kommune'),
        (1.90, 2.02, 2.06, 1.79, 1.83, 1.81, 'Haushalte'),
        (1.39, 1.37, 1.37, 1.38, 1.39, 1.36, 'Verkehr')
    ]
    df = pd.DataFrame(data[1:], columns=data[0])

    # convert to 'long' format
    emissions = df.melt(id_vars=['Bereiche'], var_name='year', value_name='per_capita')

    # add missing columns
    emissions['type'] = 'real'
    emissions['note'] = 'Amtsblatt Nr. 20/2019'

    # rename category, use required value for total emissions and mark last emissions data entry
    emissions.rename(columns={'Bereiche': 'category'}, inplace=True)
    emissions.loc[(emissions['category'] == 'Gesamt') & (emissions['year'] == 2016), 'note'] = 'last_emissions'

    # use year column as index
    emissions.set_index('year', inplace=True)
    emissions.index = emissions.index.astype(int)

    # calculate absolute emissions using population data and convert to kt
    emissions['value'] = emissions.loc[2011:2016, 'per_capita'] * population.loc[2011:2016, 'value'] / 1000
    emissions['value'] = emissions.value.astype(float).round(2)

    return emissions


def population_historic():
    # Bevölkerung mit Hauptwohnsitz historisch
    population = pd.read_csv('./leipzig-population-historic.csv', nrows=1)
    population = population.loc[0, "2011":]

    population = pd.DataFrame.from_dict({
        "year": population.index.values.astype(int),
        "value": population.values,
        "type": "real"
    })

    population.set_index('year', inplace=True)
    return population

def population_forecast():
    parse_thousands = lambda x: (int(float(x.replace(",", ".")) * 1000 ))

    population_forecast = pd.read_csv(
        './leipzig-population-forecast-2019.csv', 
        header=None,
        usecols=[0,8],
        names=["year", "value"],
        converters={"value": parse_thousands},
        index_col=['year']
    )
    population_forecast['type'] = 'geplant'
    return population_forecast.loc[2019:]


def emission_targets(population):
    years = [2020,2030,2040]
    goals = pd.DataFrame(
        index = years,
        data = {
            "population": population.loc[years].value,
            "per_capita": [4.26, 3.48, 2.93]
        }
    )

    goals['value'] = goals.population * goals.per_capita / 1000
    goals['category'] = "Gesamt"
    goals['type'] = "geplant"
    goals['note'] = "Klimaschutzkonzept 2014-2020"
    return goals


def emissions_reference():
    emissions_1990 = pd.DataFrame([
        {'year': 1990, 'category': 'Wirtschaft und Kommune', 'per_capita': 4.83},
        {'year': 1990, 'category': 'Haushalte', 'per_capita': 4.79},
        {'year': 1990, 'category': 'Verkehr', 'per_capita': 1.69},
        {'year': 1990, 'category': 'Gesamt', 'per_capita': 11.31}
    ])
    emissions_1990.set_index('year', inplace=True)

    population_1990 = 557300
    emissions_1990['value'] = emissions_1990['per_capita'] * population_1990 / 1000
    emissions_1990['type'] = 'real'
    emissions_1990['note'] = 'Klimaschutzkonzept 2014-2020'

    return emissions_1990


def generate():
    population     = pd.concat([population_historic(), population_forecast()])
    emissions      = emissions_historic(population)
    emissions_1990 = emissions_reference()
    goals          = emission_targets(population)

    columns = ['category', 'type', 'value', 'note']
    consolidated = pd.DataFrame(columns=columns)

    # emission data
    consolidated = consolidated.append(emissions_1990[columns])
    consolidated = consolidated.append(emissions[columns])

    # emission goals
    consolidated = consolidated.append(goals[columns])

    # latest population data
    consolidated = consolidated.append(pd.DataFrame(
        {
            'category': 'Einwohner',
            'type': 'Einwohner',
            'value': population.loc[2018, 'value'],
            'note': 'Bevölkerungsstatistik Leipzig'
        },
        index = [2018]
    ))

    # add header for year
    consolidated.index.name = 'year'

    return consolidated

if __name__ == "__main__":
    result = generate()
    result.to_csv('./leipzig.csv')

    