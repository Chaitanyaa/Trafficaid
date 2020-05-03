from __future__ import division, print_function
# coding=utf-8


# Flask utils
from pydoc import html
import requests
import joblib
import boto3
import io
import pandas as pd
import gpxpy
import gpxpy.gpx
import folium
import pandas as pd
from folium.map import *
from folium import plugins
from folium.plugins import MeasureControl
from folium.plugins import FloatImage
import os
import datetime as dt
import numpy as np

from flask import Flask, redirect, url_for,session,request, render_template
import time
import config
import charts
#session_requests = requests.session()
#from bs4 import BeautifulSoup as BS


# Define a flask app
app = Flask(__name__)
app.secret_key='trafficaid'



# Route the user to the homepage
@app.route('/', methods = ['GET'])
def home():
    return render_template('index.html')

# Route to about page
@app.route('/about', methods = ['GET'])
def about():
    return render_template('about.html')

# Route to data analysis page
@app.route('/data', methods = ['GET','POST'])
def data():
    #my_map = getFoliumdata()
    #return my_map._repr_html_()
    if request.method == 'POST':
        stationid=request.form.get('station')
        Fwy=request.form.get('fwy')
        startDate=request.form.get('filterDate')
        print("here",Fwy)
        redirect(url_for('getFoliumMap',stationid = stationid,Fwy=Fwy,startdate=startDate))
    return render_template('dataAnalysis.html')

# Route to model page
@app.route('/model', methods = ['GET'])
def model():
    return render_template('model.html')

# Route to prediction page
@app.route('/prediction', methods = ['GET'])
def prediction():
    return render_template('traffic_prediction.html')

@app.route('/getFoliumMap', methods = ['GET','POST'])
def getFoliumMap(stationid="",Fwy="",startdate = '2018-01-01 05:00:00'):
    my_map=charts.get_folium_map(stationid,Fwy,startdate)
    #my_map.save('index.html')
    return my_map._repr_html_()

@app.route('/getFoliumMapPred', methods = ['GET','POST'])
def getFoliumMapPred():
    # Working stations
    list280 = [400319,407710,403402]
    onoff280 = [405428,410590]
    list680 = [400335,420614,404690]
    onoff680 = [409056,408289]
    list101 = [400868,400661,400119,401472]
    onoff101 = [402883,409308]
    list880 = [400844,401871,401545,400284,400662]
    onoff880 = [403200,403098]
    Fwy = request.form.get("fwy") # Required Listbox
    pointA = request.form.get("pointa") #dummy textbox
    pointB = request.form.get("pointb") #dummy textbox
    print(Fwy)
    # stations_list = [400319,407710,403402,400335,420614,404690,400868,400661,400119,401472,400844,401871,401545,400284,400662]
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
    final = pd.DataFrame(columns=cols)
    for station in stations_list:
        #print(station)
        url = "https://n8nucy5gbh.execute-api.us-east-2.amazonaws.com/production/realtime/?station="+str(station)
        r = requests.get(url = url)
        data = r.json()
        df = pd.read_json(data, orient='columns')[cols]
        final = final.append(df)
    final.head()
    # Should have this part merged stationwise with above cell later

    df_X, df_y = final.values[:,2:-1], df.values[:,-1]
    # Determine filename based on freeway and station
    filename = "ensemble_model_400001.sav"
    loaded_model = joblib.load(filename)
    result = loaded_model.predict(df_X)
    final['p_speed']=result
    df_traffic_metadata = pd.read_csv("station_meta_finalv2.csv", sep=',', header=0)
    onoff_withmeta_df = df_traffic_metadata[df_traffic_metadata['ID'].isin(onoff)]
    onoff_withmeta_df.drop_duplicates(subset='ID',inplace=True)
    withmeta_df = final.merge(df_traffic_metadata,left_on="station",right_on="ID",how="left").round(3)
    print(result)

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
    ###Changes from here
    for row in withmeta_df.itertuples():
        popuptext = "<b>Station:</b>"+str(row.station)+"<br>"+"<b>City:</b>"+str(row.City)+"<br>"+ \
        "<b>Direction:</b>"+str(row.Dir)+"<br>"+ \
        "<b>Predicted Speed:</b>"+str(row.p_speed)+"<br>"+ \
        "<b>Occupancy:</b>"+str(row.occupancy)+"<br>"+ \
        "<b>Precipitation:</b>"+str(row.hourlyprecipitation)+"<br>"+ \
        "<b>Windspeed:</b>"+str(row.hourlywindspeed)+"<br>"+ \
        "<b>Visibility:</b>"+str(row.hourlyvisibility)+"<br>"+ \
        "<b>Incident Count:</b>"+str(row.incident)
        test = folium.Html(popuptext, script=True)
        popup = folium.Popup(test, max_width=200)
        if row.Fwy == 101:
          fg101.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                         popup=popup,
                                         icon=folium.Icon(color='blue', prefix='fa', icon='circle')))
        if row.Fwy == 280:
          fg280.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                         popup=popup,
                                         icon=folium.Icon(color='blue', prefix='fa', icon='circle')))
        if row.Fwy == 680:
          fg680.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                         popup=popup,
                                         icon=folium.Icon(color='blue', prefix='fa', icon='circle')))
        if row.Fwy == 880:
          fg880.add_child(folium.Marker(location=[row.Latitude, row.Longitude],
                                         popup=popup,
                                         icon=folium.Icon(color='blue', prefix='fa', icon='circle')))

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

    legend_html =   '''
                    <div style="position: fixed;
                                bottom: 100px; left: 50px; width: 160px; height: 220px;
                                border:2px solid grey; z-index:9999; font-size:14px;
                                "><br>
                                  &nbsp; U.S 101 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:red"></i><br>
                                  &nbsp; I280 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:blue"></i><br>
                                  &nbsp; I680 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:green"></i><br>
                                  &nbsp; I880 &nbsp; <i class="fa fa-line-chart fa-2x" style="color:yellow"></i><br>
                                  &nbsp; Start/End &nbsp; <i class="fa fa-circle fa-2x" style="color:red"></i><br/>
                                  &nbsp; Stations &nbsp; &nbsp; <i class="fa fa-circle fa-2x" style="color:blue"></i><br/><br/>
                    </div>
                    '''
    my_map.get_root().html.add_child(folium.Element(legend_html))
    #my_map.save('index.html')
    return my_map._repr_html_()

if __name__ == '__main__':
	app.run(debug=True, port=20033)



