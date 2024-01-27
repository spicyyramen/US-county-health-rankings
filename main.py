import requests
import pandas as pd
import plotly.express as px
import json
from urllib.request import urlopen

from io import StringIO


raw_data = 'County_Health_Rankings.csv'

def clean(data):
    # import raw data
    data = pd.read_csv(raw_data)
    # remove unwanted columns
    df = data.drop(['Confidence Interval Lower Bound', 'Confidence Interval Upper Bound', 'Data Release Year'], axis=1)
    # remove rows where State is PR or NaN
    df = df.loc[df['State'] != "PR"].dropna(subset=['State'])

    # change datatype of columns that should be integers
    int_list = ['State code', 'County code', 'Measure id']
    for col in int_list:
        df[col] = df[col].astype('int')
        
    ## handle rows where FIPS Code is missing
    # create reference table of counties and corresponding FIPS codes
    fips_df = df.dropna(subset=['fipscode'])
    # keep only first row for each county name
    fips_df = fips_df.drop_duplicates(subset=['County', 'County code', 'State'], keep='first')
    # remove unnecessary columns
    fips_df = fips_df[['State','County', 'fipscode']].copy()

    # transform fips code to integer and standardize format
    fips_df['fipscode'] = fips_df['fipscode'].astype('int').apply(lambda x: '{0:0>5}'.format(x))
    # rename FIPS column
    fips_df = fips_df.rename(columns={"fipscode": "FIPS Code"}).reset_index(drop=True)

    # rejoin back onto dataframe to fill missing values
    df2 = df.merge(fips_df, how="left",on=["County", "State"])

    # get rid of rows where Year span = "."
    state_data = df2.loc[df2['Year span'] != "."].copy()
    
    return state_data


def plot_data(state_data, outfile):
    # open counties location file
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    fig = px.choropleth(state_data.loc[(state_data['State'] != "US") & (state_data['Measure name'] == "Unemployment")],
                        geojson=counties,
                        locations='State',
                        locationmode="USA-states",
                        color='Raw value',
                            color_continuous_scale="turbo",
                            range_color=(0, 0.15),
                            scope="usa",
                                title='<b>Unemployment Rates in the US',
                            labels={'Raw value':'Unemployment Rate'},
                                hover_name = 'State',
                        animation_frame="Year span"
                            )
    fig.update_layout(margin={"r":0,"t":45,"l":0,"b":0},
                    height=600,
                    width=800)
    # Adjust map geo options
    fig.update_geos(showcountries=False, showcoastlines=True,
                    fitbounds="locations",
                    )

    fig.write_html(outfile, include_plotlyjs='cdn')


if __name__ == "__main__":
    state_data = clean(raw_data)

    plot_data(state_data, "index.html")