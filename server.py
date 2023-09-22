#! /usr/bin/env python3
#
#The MIT License (MIT)
#Copyright (c) 2023 Mike Jose
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
from flask import Flask, render_template, Response,request,redirect, send_file
import requests
import cv2
import os
#import imutils
import time
import threading
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import xml.dom.minidom
import xml.etree.ElementTree as ET
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
#Pump relay
PumpRly = 12
GPIO.setup(PumpRly, GPIO.OUT)
GPIO.output(PumpRly, GPIO.LOW)

def get_config():
    # parse the XML file
    xml_doc = xml.dom.minidom.parse('static/config.xml')
    # get all the config elements
    config = xml_doc.getElementsByTagName('config')
    # loop through the configuration and extract the data
    
    for item in config:
        description =   item.getElementsByTagName('description')[0].childNodes[0].data
        device_name = item.getElementsByTagName('device_name')[0].childNodes[0].data
        dose_enabled = item.getElementsByTagName('dose_enabled')[0].childNodes[0].data
        dose_time = float(item.getElementsByTagName('dose_time')[0].childNodes[0].data)
        sensitivity = int(item.getElementsByTagName('sensitivity')[0].childNodes[0].data)
        ip_address = item.getElementsByTagName('ip_address')[0].childNodes[0].data
        local_port = int(item.getElementsByTagName('local_port')[0].childNodes[0].data)
        remote_ip = item.getElementsByTagName('remote_ip')[0].childNodes[0].data
        remote_port = int(item.getElementsByTagName('remote_port')[0].childNodes[0].data)
        events = item.getElementsByTagName('events')[0].childNodes[0].data
        dose_interval = item.getElementsByTagName('dose_interval')[0].childNodes[0].data
        capture_image = item.getElementsByTagName('capture_image')[0].childNodes[0].data
    config = [description,device_name,dose_enabled,dose_time,sensitivity,ip_address,local_port,remote_ip,remote_port,events,dose_interval,capture_image]
    return config

def save_config(data):
    tree = ET.parse('static/config.xml')
    root = tree.getroot()
    root[0].text = data[0]
    root[1].text = data[1]
    root[2].text = data[2]
    root[3].text = data[3]
    root[4].text = data[4]
    root[5].text = data[5]
    root[6].text = data[6]
    root[7].text = data[7]
    root[8].text = data[8]
    root[9].text = data[9]
    root[10].text = data[10]
    root[11].text = data[11]
    # create a new XML file with the new element
    tree.write('static/config.xml')
    return True


app = Flask(__name__)

@app.route('/', methods=["GET"])
def index():
    #Get a list of images in the captures directory
    path = "/home/admin/watcher/static/captures/"
    # to store files in a list
    list = []
    #Iterate through the files and store in a list
    for (root, dirs, file) in os.walk(path):
        for f in file:
            if '.png' in f:
                list.append(f)

    config = get_config()
    config = get_config()
    return render_template('home.html',config=config,images=list)

@app.route('/save_config', methods=["POST"])
def configuration():
    config = get_config()
    data = ["device_name","dose_enabled","dose_time","sensitivity","ip_address","local_port","remote_ip","remote_port","description","events","dose_interval","capture_image"]
    data[0] = request.form['device_name']
    data[1] = request.form['sensitivity']
    data[2] = request.form['dose_time']
    data[3] = request.form['dose_enabled']
    data[4] = request.form['ip_address']
    data[5] = request.form['local_port']
    data[6] = request.form['remote_ip']
    data[7] = request.form['remote_port']
    data[8] = request.form['description']
    data[9] = config[9]
    data[10] = request.form['dose_interval']
    data[11] = request.form['capture_image']
    #print(data)
    save_config(data)
    config = get_config()
    os.system("sudo systemctl restart watcher.service")
    return redirect("/", code=302)

@app.route('/DeleteImage/<string:name>', methods=["GET"])
def DeleteImage(name):
    config = get_config()
    os.remove("static/captures/"+name)
    return redirect("/", code=302)

@app.route('/GetEvents', methods=["GET"])
def GetEvents():
    config = get_config()
    return str(config[9])

@app.route('/download/<string:name>')
def download_file(name):
	#path = "html2pdf.pdf"
	#path = "info.xlsx"
	path = "static/captures/"+name
	#path = "sample.txt"
	return send_file(path, as_attachment=True)

@app.route('/confirmrestart', methods=["GET"])
def ConfRestart():
    config = get_config()
    return render_template('restart.html',config=config)

@app.route('/confirmstop', methods=["GET"])
def ConfStop():
    return render_template('stop.html')

@app.route('/restart', methods=["GET"])
def Restart():
    os.system("sudo reboot &")
    return "REBOOTING"

@app.route('/stop', methods=["GET"])
def Stop():
    os.system("sudo shutdown now &")
    return "Shutdown"

@app.route('/checkconnect', methods=["GET"])
def checkconnect():
    return "Connected"

@app.route('/primepump/<int:status>', methods=["GET"])
def primepump(status):
    if status == 1:
        GPIO.output(PumpRly, GPIO.HIGH)
        return "On"
    else:
        GPIO.output(PumpRly, GPIO.LOW)
        return "Off"
      
if __name__ == '__main__':
    app.run(debug = True,host = "0.0.0.0",port = 5500)
    
