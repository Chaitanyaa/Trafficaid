import io
import pandas as pd
import gpxpy
import gpxpy.gpx
import folium
import pandas as pd
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import json
from folium.map import *
from folium import plugins
from folium.plugins import MeasureControl
from folium.plugins import FloatImage
import os
import datetime as dt
import numpy as np
import boto3

# Fetch global dataframe values
def def_variables(stationid,Fwy,startdate,intent):
    print("Def",stationid,Fwy)
    #startdate = '2018-01-01 00:00:00' # Choose Date and time (Required) calendar
    #enddate = '2018-01-02 00:00:00' # Can be blank (Optional) calendar
    start_obj = dt.datetime.strptime(startdate, '%Y-%m-%d %H:%M:%S')
    end_obj = start_obj+dt.timedelta(days=1)
    year = startdate[0:4]
    #end_obj = dt.datetime.strptime(enddate, '%Y-%m-%d %H:%M:%S')
    #if(enddate!=""):
    #    end_obj = dt.datetime.strptime(enddate, '%Y-%m-%d %H:%M:%S')

    #Fwy = "" # Can be blank (Optional) Listbox
    stationsdisplaycount = 20 # Can be blank (Optional) textbox  -- Blank means zero here
    #stationid = "" #Can be blank (Optional) textbox

    #Note: All blanks take empty strings
    AWS_ACCESS_KEY = "AKIA4JL5A5WR3V5RODMP"
    AWS_SECRET_KEY = "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"
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
    traffic_weather_incident = io.BytesIO(s3.get_object(Bucket='pemstwi', Key=year+'/twi')['Body'].read())
    # twi_df = pd.read_csv('C:/Sindu_SJSU/Sem04/trafficaid-master/twi_df_500.csv')
    twi_df = pd.read_parquet(traffic_weather_incident)
    if(end_obj!=""): 
        twi_df=twi_df[(twi_df['timestamp_']>=np.datetime64(start_obj))&(twi_df['timestamp_']<=np.datetime64(end_obj))]
        #if((Fwy!="") and (stationid!="")):
        #    selected_date_df = twi_df[(twi_df['freeway']==Fwy)&(twi_df['station']==stationid)]
        #elif(Fwy!=""):
        #    selected_date_df = twi_df[(twi_df['freeway']==Fwy)]
        if(stationid!=""):
            selected_date_df = twi_df[twi_df['station']==int(stationid)]
        else:
            selected_date_df = twi_df
    else:
        twi_df = twi_df[(twi_df['timestamp_']>=np.datetime64(start_obj))]
        #if((Fwy!="") and (stationid!="")):
            #selected_date_df = twi_df[(twi_df['freeway']==Fwy)&(twi_df['station']==stationid)]
        #elif(Fwy!=""):
            #selected_date_df = twi_df[(twi_df['freeway']==Fwy)]
        if(stationid!=""):
            selected_date_df = twi_df[(twi_df['station']==int(stationid))]
        else:
            selected_date_df = twi_df

    selected_date_df['incident'] = np.where(selected_date_df['incident']>0,1,0)
    selected_date_df = selected_date_df.sort_values(['station'])
        
    if(end_obj!=""):
        selected_date = selected_date_df.set_index(['station'])
        grouped_selected_date_df = selected_date.groupby(selected_date.index).agg({'speed':'mean','incident':'sum','occupancy':'mean','hourlyprecipitation':'mean','hourlywindspeed':'mean','hourlyvisibility':'mean'})
        grouped_selected_date_df = grouped_selected_date_df.reset_index()
    df_traffic_metadata = pd.read_csv("station_meta_finalv2.csv", sep=',', header=0)
    selected_date_withmeta_df = grouped_selected_date_df.merge(df_traffic_metadata,left_on="station",right_on="ID",how="left").round(3)
    if((Fwy=="") & (stationid!="") & (selected_date_withmeta_df['Fwy'].count() ==1)):
        Fwy=selected_date_withmeta_df['Fwy'].values[0]
    print("DF",selected_date_withmeta_df.head())
    if(Fwy != ""):
        selected_date_withmeta_df = selected_date_withmeta_df[(selected_date_withmeta_df['Fwy']==int(Fwy))]
    if intent=="dual":
        return selected_date_df
    else:
        return selected_date_withmeta_df

def create_plot(stationid,Fwy,startdate):
    selected_date_withmeta_df=def_variables(stationid,Fwy,startdate,"pie")
    #selected_date_withmeta_df=pd.read_csv("/home/cmpe295-2/datamonks/Sindu/SampleData/selected_date_withmeta_df.csv")
    incident_df=selected_date_withmeta_df.groupby('County.1')['incident'].agg('sum').reset_index()
    x = incident_df['County.1']
    y = incident_df['incident']
    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    df = pd.DataFrame({'x': x, 'y': y}) # creating a sample dataframe
    data = [
        go.Pie(
            labels=df['x'], # assign x as the dataframe column 'x'
            values=df['y']
        )
    ]
    fig = go.Figure(data=data,layout=layout)
    fig.update_traces(hoverinfo='value',textinfo='value')
    fig.update_traces(textposition='inside')
    fig.update_layout(uniformtext_minsize=16, uniformtext_mode='hide')
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

def create_weather_chart(stationid,Fwy,startdate):
    selected_date_withmeta_df=def_variables(stationid,Fwy,startdate,"weather")
    #selected_date_withmeta_df=pd.read_csv("/home/cmpe295-2/datamonks/Sindu/SampleData/selected_date_withmeta_df.csv")
    ws=round(selected_date_withmeta_df['hourlywindspeed'].agg('mean'),3)
    vis=round(selected_date_withmeta_df['hourlyvisibility'].agg('mean'),3)
    per=round(selected_date_withmeta_df['hourlyprecipitation'].agg('mean'),3)
    incidents_sum=selected_date_withmeta_df['incident'].agg('sum')
    return [ws,vis,per,incidents_sum]

def create_dual_plot(stationid,Fwy,startdate):
    selected_date_df=def_variables(stationid,Fwy,startdate,"dual")
    #selected_date_df=pd.read_csv("/home/cmpe295-2/datamonks/Sindu/SampleData/selected_date_df.csv")
    if(Fwy!=""):
        selected_date_df=selected_date_df[(selected_date_df['freeway']==int(Fwy))]
    occupancy_df=selected_date_df.groupby('timestamp_')['occupancy'].agg('mean').reset_index()
    speed_df=selected_date_df.groupby('timestamp_')['speed'].agg('mean').reset_index()
    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title='Speed Vs Occupancy'
    )
    fig=make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
    go.Scatter(
        x=speed_df['timestamp_'], # assign x as the dataframe column 'x'
        y=speed_df['speed'],
        name="Speed"
        ),
        secondary_y=True
    )
    fig.add_trace(
    go.Bar(
        x=occupancy_df['timestamp_'], # assign x as the dataframe column 'x'
        y=occupancy_df['occupancy'],
        name="Occupancy"
        ),
        secondary_y=False
    )
        # Set x-axis title
    fig.update_xaxes(title_text="<b>Hour of the Day</b>")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Occupancy</b>", secondary_y=False)
    fig.update_yaxes(title_text="<b>Speed</b>", secondary_y=True)
    figure=go.Figure(data=fig,layout=layout)
    graphJSON = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

def get_folium_map(stationid,Fwy,startdate):
    selected_date_withmeta_df = def_variables(stationid,Fwy,startdate,"folium")
    #selected_date_withmeta_df=pd.read_csv("/home/cmpe295-2/datamonks/Sindu/SampleData/selected_date_withmeta_df.csv")
    print(selected_date_withmeta_df.head())
    stationsdisplaycount = 20
    #101
    gpx_file101 = open('101.gpx', 'r')
    gpx101 = gpxpy.parse(gpx_file101)
    points101 = []
    for track in gpx101.tracks:
        for segment in track.segments:
            for point in segment.points:
                points101.append(tuple([point.latitude, point.longitude]))

    #280
    gpx_file280 = open('280.gpx', 'r')
    gpx280 = gpxpy.parse(gpx_file280)
    points280 = []
    for track in gpx280.tracks:
        for segment in track.segments:
            for point in segment.points:
                points280.append(tuple([point.latitude, point.longitude]))


    #680
    gpx_file680 = open('680.gpx', 'r')
    gpx680 = gpxpy.parse(gpx_file680)
    points680 = []
    for track in gpx680.tracks:
        for segment in track.segments:
            for point in segment.points:
                points680.append(tuple([point.latitude, point.longitude]))


    #880
    gpx_file880 = open('880.gpx', 'r')
    gpx880 = gpxpy.parse(gpx_file880)
    points880 = []
    for track in gpx880.tracks:
        for segment in track.segments:
            for point in segment.points:
                points880.append(tuple([point.latitude, point.longitude]))

    ave_lat = sum(p[0] for p in points880)/len(points880)
    ave_lon = sum(p[1] for p in points880)/len(points880)

    # Load map centred on average coordinates
    my_map = folium.Map(location=[ave_lat, ave_lon], zoom_start=9,tiles="Stamen Terrain")
    if (Fwy=="") & (selected_date_withmeta_df['Fwy'].count() ==1):
        Fwy=selected_date_withmeta_df['Fwy']
    print("here",Fwy)
    Fwy = str(int(Fwy))
    if(Fwy=="101"): 
        toggle101 = True 
    else:
        toggle101= False
    if(Fwy=="280"): 
        toggle280 = True 
    else: 
        toggle280= False
    if(Fwy=="680"): 
        toggle680 = True 
    else: 
        toggle680= False
    if(Fwy=="880"): 
        toggle880 = True 
    else: 
        toggle880= False
    fg101 = folium.FeatureGroup(name="U.S 101",show=toggle101)
    fg280 = folium.FeatureGroup(name="I280",show=toggle280)
    fg680 = folium.FeatureGroup(name="I680",show=toggle680)
    fg880 = folium.FeatureGroup(name="I880",show=toggle880)

    ###Changes from here
    cnt = selected_date_withmeta_df['station'].count()
    if(cnt<stationsdisplaycount):
        stationsdisplaycount = cnt
    else:
        stationsdisplaycount

    for row in selected_date_withmeta_df.sample(stationsdisplaycount).itertuples():
        popuptext = "<b>Station:</b>"+str(row.station)+"<br>"+"<b>City:</b>"+str(row.City)+"<br>"+ \
        "<b>Direction:</b>"+str(row.Dir)+"<br>"+ \
        "<b>Occupancy:</b>"+str(row.occupancy)+"<br>"+ \
        "<b>Speed:</b>"+str(row.speed)+"<br>"+ \
        "<b>Precipitation:</b>"+str(row.hourlyprecipitation)+"<br>"+ \
        "<b>Windspeed:</b>"+str(row.hourlywindspeed)+"<br>"+ \
        "<b>Visibility:</b>"+str(row.hourlyvisibility)+"<br>"+ \
        "<b>Incident Count:</b>"+str(row.incident)
        test = folium.Html(popuptext, script=True)
        popup = folium.Popup(test, max_width=200)
        if row.Fwy == 101:
          fg101.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                         popup=popup,
                                         icon=folium.Icon(color='red', prefix='fa', icon='circle')))
        if row.Fwy == 280:
          fg280.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                         popup=popup,
                                         icon=folium.Icon(color='blue', prefix='fa', icon='circle')))
        if row.Fwy == 680:
          fg680.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                         popup=popup,
                                         icon=folium.Icon(color='green', prefix='fa', icon='circle')))
        if row.Fwy == 880:
          fg880.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                         popup=popup,
                                         icon=folium.Icon(color='orange', prefix='fa', icon='circle')))

    folium.PolyLine(points101, color="red", weight=2.5, opacity=1).add_to(fg101)
    folium.PolyLine(points280, color="blue", weight=2.5, opacity=1).add_to(fg280)
    folium.PolyLine(points680, color="green", weight=2.5, opacity=1).add_to(fg680)
    folium.PolyLine(points880, color="yellow", weight=2.5, opacity=1).add_to(fg880)
    my_map.add_child(fg101)
    my_map.add_child(fg280)
    my_map.add_child(fg680)
    my_map.add_child(fg880)

    folium.LayerControl().add_to(my_map)

    legend_html =   '''
                    <div style="position: fixed;
                                bottom: 50px; left: 50px; width: 140px; height: 160px;
                                border:2px solid grey; z-index:9999; font-size:14px;
                                "><br>
                                  &nbsp; U.S 101 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:red"></i><br>
                                  &nbsp; I280 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:blue"></i><br>
                                  &nbsp; I680 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:green"></i><br>
                                  &nbsp; I880 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:yellow"></i>
                    </div>
                    '''
    my_map.get_root().html.add_child(folium.Element(legend_html))
    return my_map