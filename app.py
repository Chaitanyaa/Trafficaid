from __future__ import division, print_function
# coding=utf-8


# Flask utils
from pydoc import html

import boto3
import folium as folium
import pandas as pd
from flask import Flask, redirect, url_for,session,request, render_template
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
import pyarrow.parquet as pq
import s3fs
import numpy as np
import requests
import pytz
from lxml import html
import datetime
import time
session_requests = requests.session()
from bs4 import BeautifulSoup as BS


# Define a flask app
app = Flask(__name__)
app.secret_key='trafficaid'



# Route the user to the homepage
@app.route('/', methods = ['GET'])
def home():
    return render_template('index.html')	

if __name__ == '__main__':
	app.run(debug=True, port=5000)


    

