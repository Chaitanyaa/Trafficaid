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
import time
import datetime as dt
import numpy as np

from flask import Flask, redirect, url_for,session,request, render_template
import time
import charts
import realtime
import utils
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
    return render_template('about_planner.html')

# Route to Data Analysis Page
@app.route('/data', methods = ['GET','POST'])
def data():
    #my_map = getFoliumdata()
    #return my_map._repr_html_()
    session.clear()
    if request.method == 'POST':
        stationid=request.form.get('station')
        Fwy=request.form.get('fwy')
        startDate=request.form.get('filterDate')
        if Fwy=="Select a Freeway":
            Fwy=""
        session['stationid']=stationid
        session['Fwy']=Fwy
        if startDate!="":
            startDate=startDate+" 00:00:00"
        session['startDate']=startDate
        redirect(url_for('getFoliumMap'))
    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    details=[stationid,Fwy,startDate[0:10]]
    liststatus=['Select a Freeway','101','280','680','880']
    return render_template('dataAnalysis.html',details=details,liststatus=liststatus)

@app.route("/simple_chart")
def chart():
    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    bar = charts.create_plot(stationid,Fwy,startDate)
    return render_template('chart.html', plot=bar)

@app.route("/dual_chart")
def dual_chart():
    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    bar = charts.create_dual_plot(stationid,Fwy,startDate)
    return render_template('dual_chart.html', plot=bar)

@app.route("/weather_chart")
def weather_chart():
    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    weather_details=charts.create_weather_chart(stationid,Fwy,startDate)
    return render_template('weather_chart.html',weather_details=weather_details)

# Route to model page
@app.route('/model', methods = ['GET'])
def model():
    return render_template('model.html')
# Route to prediction page

@app.route('/prediction', methods = ['GET','POST'])
def prediction(): 
    #session['Freeway'] = request.form.get("fwy")
    # if(session.get('avgocc')):
    #     avgocc = session.get('avgocc')
    #     print(avgocc)
    # if request.method == 'POST':
    Fwy = request.form.get('fwy')
    print(Fwy)
    timetak, avgocc, avgspeed, avgvisibility, avgwindspeed, avgprecipitation, incidentcount = getFoliumMapPred(Fwy)
    if(timetak!=0):
        timetaklow = str(float(timetak)-8)
        timetakhigh = str(float(timetak)+8)
    else:
        timetaklow = 0
        timetakhigh = 0
    return render_template('traffic_prediction.html',timetaklow=timetaklow,timetakhigh=timetakhigh, avgocc=avgocc, avgspeed=avgspeed, avgvisibility=avgvisibility, avgwindspeed=avgwindspeed, avgprecipitation=avgprecipitation, incidentcount=incidentcount)

@app.route('/getFoliumMap')
def getFoliumMap():

    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    print("Session",stationid,Fwy,startDate)
    my_map=charts.get_folium_map(stationid,Fwy,startDate)
    #my_map.save('index.html')
    return my_map._repr_html_()


@app.route('/getFoliumMapPred', methods = ['GET','POST'])
def getFoliumMapPred(Fwy):
    # Fwy = request.form.get("fwy")
    print("Here")
    if(Fwy!=None):
        my_map,timetak,avgocc, avgspeed, avgvisibility, avgwindspeed, avgprecipitation, incidentcount = realtime.getreal(Fwy)
    else:
        my_map=realtime.popdum()
        timetak = 0
        avgocc = 0
        avgspeed = 0
        avgvisibility = 0
        avgwindspeed = 0
        avgprecipitation = 0
        incidentcount = 0 

    return timetak, avgocc, avgspeed, avgvisibility, avgwindspeed, avgprecipitation, incidentcount    
        # return my_map._repr_html_()
    # redirect(url_for('prediction'))
    #return render_template('traffic_prediction.html')

if __name__ == '__main__':
    app.secret_key = "config1515"
    app.run(debug=True, port=20074)



