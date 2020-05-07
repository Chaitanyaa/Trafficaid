import io
import pandas as pd
import gpxpy
import gpxpy.gpx
import folium
import pandas as pd
import tensorflow as tf
from folium.map import *
from folium import plugins
from flask import Flask, redirect, url_for,session,request, render_template
from folium.plugins import MeasureControl
from folium.plugins import FloatImage
import os
import datetime as dt
import numpy as np
import boto3
import requests
import utils
from tensorflow.python.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import numpy as np
import math
import statsmodels.api as sm
from geopy.distance import geodesic
from sklearn.metrics import mean_squared_error

def getreal(Fwy):
    list280 = [400319,407710,403402]
    onoff280 = [405428,410590]
    list680 = [400335,420614,404690]
    onoff680 = [409056,408289]
    list101 = [400868,401472,400119,400661]
    onoff101 = [402883,409308]
    list880 = [400844,401871,401545,400284,400662]
    onoff880 = [403200,403098]
# stations_list = [400319,407710,403402,400335,420614,404690,400868,400661,400119,401472,400844,401871,401545,400284,400662]
    Fwy = 101 # Required Listbox
# pointA #dummy textbox
# pointB #dummy textbox
    if(Fwy==101):
        stations_list = list101
        onoff = onoff101 
    elif(Fwy==280):
        stations_list = list280
        onoff = onoff280
    elif(Fwy==680):
        stations_list = list680
        onoff = onoff680
    else:
        stations_list = list880
        onoff = onoff880

    cols = ['station','timestamp_','occupancy','hourlyprecipitation','hourlywindspeed','hourlyvisibility','incident','day_of_week_num','hour_of_day','weekend','speed']
    colstomod = ['occupancy','day_of_week_num','hour_of_day','speed']
    final = pd.DataFrame(columns=cols)
    pred_speeds=np.array([])
    for station in stations_list:
        url = "https://n8nucy5gbh.execute-api.us-east-2.amazonaws.com/production/realtime/?station="+str(station)
        r = requests.get(url = url)
        data = r.json()
        df = pd.read_json(data, orient='columns')[cols]
        print("counting",df.count())
        dfx=df.set_index(['station','timestamp_']).sort_values(['station','timestamp_'])[colstomod]
        stationid = station
        modelfile = "../models/"+str(Fwy)+"_"+str(stationid)+"_"+"speed.h5"
        #define how many timesteps to look back as input with the variable n_lag.
        n_lag = 3
        #define how many timesteps ahead to predict with the variable n_steps.
        n_steps = 1
        treframed, tkey, tscaled, tscaler1 = utils.format_model_data(dfx, n_lag, n_steps)
        treframed.drop(treframed.columns[[12,13,14]], axis=1, inplace=True)
        tinv_y, tinv_yhat= utils.predict_data(treframed,modelfile,tscaler1)
        y_actual=pd.DataFrame(tinv_y)
        y_predicted=pd.DataFrame((tinv_yhat))
        df_2020=pd.concat([y_actual,y_predicted],axis=1)
        col=['y_actual','y_predicted']
        df_2020.columns=col
        pred_speeds=np.append(pred_speeds, tinv_yhat[-1])
        final = final.append(df)

    final['station'] = final['station'].astype('int64')
    final['occupancy'] = final['occupancy'].astype('float')
    final['speed'] = final['speed'].astype('float')
    final['hourlyprecipitation'] = final['hourlyprecipitation'].astype('float')
    final['hourlywindspeed'] = final['hourlywindspeed'].astype('float')
    final['hourlyvisibility'] = final['hourlyvisibility'].astype('int32')
    final['incident'] = final['incident'].astype('int32')
    final_data = final.set_index(['station'])
    finals = final_data.groupby(final_data.index).agg({'speed':'mean','incident':'sum','occupancy':'mean','hourlyprecipitation':'mean','hourlywindspeed':'mean','hourlyvisibility':'mean'})
    finals['p_speed'] = pred_speeds
    finals = finals.reset_index(['station'])
    finals.head()

    # Should have this part merged stationwise with above cell later
    df_traffic_metadata = pd.read_csv("station_meta_finalv2.csv", sep=',', header=0)
    onoff_withmeta_df = df_traffic_metadata[df_traffic_metadata['ID'].isin(onoff)]
    onoff_withmeta_df.drop_duplicates(subset='ID',inplace=True)
    withmeta_df = finals.merge(df_traffic_metadata,left_on="station",right_on="ID",how="left").round(3)
    withmeta_df.head()

    #Time Taken
    sorter = [onoff[0]]+stations_list+[onoff[1]]
    sorterIndex = dict(zip(sorter,range(len(sorter))))
    a = df_traffic_metadata[df_traffic_metadata['ID'].isin(onoff+stations_list)]
    a['Rank'] = a['ID'].map(sorterIndex)
    cols1 = ['ID','Fwy','Latitude','Longitude']
    a = a.sort_values(['Rank'])[cols1]
    a.drop_duplicates(subset=['ID'],inplace=True)
    a['speed'] = [pred_speeds[0]]+list(pred_speeds)+[pred_speeds[-1]]
    tim = np.array([])
    for i in range(1,len(a)):
        p1 = (a.iloc[i-1][2],a.iloc[i-1][3])
        p2 = (a.iloc[i][2],a.iloc[i][3]) 
        dist = geodesic(p1, p2).miles
        spd = (a.iloc[i-1][4]+a.iloc[i][4])/2
        t = dist/spd
        tim = np.append(tim, t)
    timetak = sum(tim*60).round(2)
    print(timetak)
    #Map

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
    if(Fwy==101):
        fg101 = folium.FeatureGroup(name="U.S 101",show=True)
        fg280 = folium.FeatureGroup(name="I280",show=False)
        fg680 = folium.FeatureGroup(name="I680",show=False)
        fg880 = folium.FeatureGroup(name="I880",show=False)
    if(Fwy==280):    
        fg280 = folium.FeatureGroup(name="I280",show=True)
        fg101 = folium.FeatureGroup(name="U.S 101",show=False)
        fg680 = folium.FeatureGroup(name="I680",show=False)
        fg880 = folium.FeatureGroup(name="I880",show=False)
    if(Fwy==680):
        fg680 = folium.FeatureGroup(name="I680",show=True)
        fg101 = folium.FeatureGroup(name="U.S 101",show=False)
        fg280 = folium.FeatureGroup(name="I280",show=False)
        fg880 = folium.FeatureGroup(name="I880",show=False)
    if(Fwy==880):
        fg880 = folium.FeatureGroup(name="I880",show=True)
        fg101 = folium.FeatureGroup(name="U.S 101",show=False)
        fg280 = folium.FeatureGroup(name="I280",show=False)
        fg680 = folium.FeatureGroup(name="I680",show=False)
    ###Changes from here
    for row in withmeta_df.itertuples():
        popuptext = "<b>Station:</b>"+str(row.station)+"<br>"+"<b>City:</b>"+str(row.City)+"<br>"+ \
        "<b>Direction:</b>"+str(row.Dir)+"<br>"+ \
        "<b>Predicted Speed:</b>"+str(row.p_speed)+"<br>"+ \
        "<b>Avg Occupancy:</b>"+str(row.occupancy)+"<br>"+ \
        "<b>Avg Precipitation:</b>"+str(row.hourlyprecipitation)+"<br>"+ \
        "<b>Avg Windspeed:</b>"+str(row.hourlywindspeed)+"<br>"+ \
        "<b>Avg Visibility:</b>"+str(row.hourlyvisibility)+"<br>"+ \
        "<b>Incident Count:</b>"+str(row.incident)
        test = folium.Html(popuptext, script=True)
        popup = folium.Popup(test, max_width=200)
        if row.Fwy == 101:
            fg101.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                        popup=popup,
                                        icon=folium.Icon(color='blue', prefix='fa', icon='car')))    
        if row.Fwy == 280:
            fg280.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                        popup=popup,
                                        icon=folium.Icon(color='blue', prefix='fa', icon='car')))
        if row.Fwy == 680:
            fg680.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                        popup=popup,
                                        icon=folium.Icon(color='blue', prefix='fa', icon='car')))
        if row.Fwy == 880:
            fg880.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                        popup=popup,
                                        icon=folium.Icon(color='blue', prefix='fa', icon='car')))
        
    for row in onoff_withmeta_df.itertuples():
        if row.Fwy == 101:
            fg101.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                    icon=folium.Icon(color='red', prefix='fa', icon='circle')))    
        if row.Fwy == 280:
            fg280.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                        icon=folium.Icon(color='red', prefix='fa', icon='circle')))
        if row.Fwy == 680:
            fg680.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                        icon=folium.Icon(color='red', prefix='fa', icon='circle')))
        if row.Fwy == 880:
            fg880.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                        icon=folium.Icon(color='red', prefix='fa', icon='circle')))
        
    folium.PolyLine(points101, color="black", weight=2.5, opacity=1).add_to(fg101)
    folium.PolyLine(points280, color="purple", weight=2.5, opacity=1).add_to(fg280)
    folium.PolyLine(points680, color="green", weight=2.5, opacity=1).add_to(fg680)
    folium.PolyLine(points880, color="yellow", weight=2.5, opacity=1).add_to(fg880)
    my_map.add_child(fg101)
    my_map.add_child(fg280)
    my_map.add_child(fg680)
    my_map.add_child(fg880)

    folium.LayerControl().add_to(my_map)

    legend_html =   "<div style=\"position: fixed; \
                                bottom: 10px; left: 30px; width: 220px; height: 70px;\
                                border:2px solid grey; z-index:9999; font-size:14px; + \
                                \"><br>\
                                &nbsp;&nbsp;&nbsp;<i class=\"fa fa-car fa-2x\" style=\"color:purpule\"></i>\
                                &nbsp; Travel Time: &nbsp;"+str(timetak.round(2))+" mins"+"<br/><br/>\
                    </div>"
    #my_map.get_root().html.add_child(folium.Element(legend_html))
    my_map.save('./static/Map.html')
    # my_map
    withmeta_df.drop_duplicates(subset=['station'],inplace=True)
    finavg = withmeta_df.groupby('Dir').agg({'speed':'mean','incident':'sum','occupancy':'mean','hourlyprecipitation':'mean','hourlywindspeed':'mean','hourlyvisibility':'mean'})
    finavg = finavg.reset_index()
    # finavg.head()
    avgocc = str(finavg['occupancy'][0].astype('float').round(1))
    avgspeed = str(finavg['speed'][0].astype('float').round(1))
    avgvisibility = str(finavg['hourlyvisibility'][0].astype('float').round(1))
    avgwindspeed = str(finavg['hourlywindspeed'][0].astype('float').round(1))
    avgprecipitation = str(finavg['hourlyprecipitation'][0].astype('float').round(1))
    incidentcount = str(finavg['incident'][0].astype('int'))
    return my_map, timetak, avgocc, avgspeed, avgvisibility, avgwindspeed, avgprecipitation, incidentcount

def popdum():
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
    fg101 = folium.FeatureGroup(name="U.S 101",show=False)
    fg280 = folium.FeatureGroup(name="I280",show=False)
    fg680 = folium.FeatureGroup(name="I680",show=False)
    fg880 = folium.FeatureGroup(name="I880",show=False)
        
    folium.PolyLine(points101, color="red", weight=2.5, opacity=1).add_to(fg101)
    folium.PolyLine(points280, color="blue", weight=2.5, opacity=1).add_to(fg280)
    folium.PolyLine(points680, color="green", weight=2.5, opacity=1).add_to(fg680)
    folium.PolyLine(points880, color="yellow", weight=2.5, opacity=1).add_to(fg880)
    my_map.add_child(fg101)
    my_map.add_child(fg280)
    my_map.add_child(fg680)
    my_map.add_child(fg880)

    folium.LayerControl().add_to(my_map)
    legend_html ='''
                <div style="position: fixed; 
                            bottom: 30px; left: 30px; width: 140px; height: 160px; 
                            border:2px solid grey; z-index:9999; font-size:14px;
                            "><br>
                            &nbsp; U.S 101 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:red"></i><br>
                            &nbsp; I280 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:blue"></i><br>
                            &nbsp; I680 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:green"></i><br>
                            &nbsp; I880 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:yellow"></i>
                </div>
                ''' 
    my_map.get_root().html.add_child(folium.Element(legend_html))
    my_map.save('./static/Map.html')
    # my_map
    return my_map
