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
import xml.dom.minidom
import xml.etree.ElementTree as ET
import cv2
import os
import subprocess
#import imutils
import time
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import xml.dom.minidom
import RPi.GPIO as GPIO
from datetime import datetime
GPIO.setmode(GPIO.BCM)
#Pump relay
PumpRly = 12
LED = 17
GPIO.setup(PumpRly, GPIO.OUT)
GPIO.output(PumpRly, GPIO.LOW)
GPIO.setup(LED, GPIO.OUT)
GPIO.output(LED, GPIO.LOW)

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

config = get_config()
print(config[1]," Watching")
print("Dose enabled:",config[2])
print("Dose duration:",config[3])
print("Dose interval:",config[10])
print("Motion sensitivity: ",config[4])
print("IP Address: ",config[5]," Port: ",config[6])
print("Remote IP Address: ",config[7]," Port: ",config[8])
dose_time = time.time()
doseit = True
resume_time = float(config[10])+time.time()
def save_config(data):
    config = get_config()
    tree = ET.parse('static/config.xml')
    root = tree.getroot()
    #root[0].text = str(config[0])
    #root[1].text = str(config[1])
    #root[2].text = str(config[2])
    #root[3].text = str(config[3])
    #root[4].text = str(config[4])
    #root[5].text = str(config[5])
    #root[6].text = str(config[6])
    #root[7].text = str(config[7])
    #root[8].text = str(config[8])
    root[9].text = str(data)
    #root[10].text = str(config[10])
    #root[11].text = str(config[11])
    # create a new XML file with the new element
    tree.write('static/config.xml')
    return True

time.sleep(3)
while True:
    # initialize the camera and grab a reference to the raw camera capture
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 15
    rawCapture = PiRGBArray(camera, size=(640, 480))
    # Initialize the first frame of the video stream
    first_frame = None
    
    # Create kernel for morphological operation. You can tweak
    # the dimensions of the kernel.
    # e.g. instead of 20, 20, you can try 30, 30
    kernel = np.ones((20,20),np.uint8)
    # allow the camera to warmup
    time.sleep(0.5)
    AlarmCount = 0
    capcount = 0
    # capture frames from the camera
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the raw NumPy array representing the image, then initialize the timestamp
        # and occupied/unoccupied text
        image = frame.array
        #image = cv2.rotate(image,cv2.ROTATE_180)
        # Convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray,5)
        # Close gaps using closing
        gray = cv2.morphologyEx(gray,cv2.MORPH_CLOSE,kernel)
        # If first frame, we need to initialize it.
        if first_frame is None:
            first_frame = gray
            # Clear the stream in preparation for the next frame
            rawCapture.truncate(0)
            # Go to top of for loop
            continue                
        # Calculate the absolute difference between the current frame
        # and the first frame
        absolute_difference = cv2.absdiff(first_frame, gray)
        #print("absolute_difference: ",absolute_difference)
        # If a pixel is less than ##, it is considered black (background). 
        # Otherwise, it is white (foreground). 255 is upper limit.
        # Modify the number after absolute_difference as you see fit.
        _, absolute_difference = cv2.threshold(absolute_difference,config[4], 255, cv2.THRESH_BINARY)
    
        # Find the contours of the object inside the binary image
        contours, hierarchy = cv2.findContours(absolute_difference,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[-2:]
        areas = [cv2.contourArea(c) for c in contours]
        # text
        text = time.time()
        font = cv2.FONT_HERSHEY_SIMPLEX
        org = (10, 30)
        fontScale = 1
        color = (0, 255, 0)
        thickness = 2
        image = cv2.putText(image, str(datetime.now()), org, font, fontScale, 
                color, thickness, cv2.LINE_AA, False)
        status = cv2.imwrite("static/captures/preview_"+str(capcount)+".png",image)
        capcount += 1
        if capcount > 1:
            capcount = 0
        # If there are no countours
        if len(areas) < 1:
            GPIO.output(LED, GPIO.LOW)
            rawCapture.truncate(0)
        else:
            if doseit:
                AlarmCount += 1
                status = cv2.imwrite("static/captures/capture.png",image)
                save_config(AlarmCount)
                resume_time = float(config[10])+time.time()
                doseit = False
                GPIO.output(LED, GPIO.HIGH)
                if config[2] == "True":
                    GPIO.output(PumpRly, GPIO.HIGH)
                    time.sleep(float(config[3]))
                    GPIO.output(PumpRly, GPIO.LOW)
            if time.time() > resume_time:
                print("reseting clock")
                doseit = True

            if config[11] == "1":
                status = cv2.imwrite("static/captures/capture_"+config[1]+"_"+str(time.time())+".png",image)
                if status:
                    print("static/captures/capture_"+config[1]+"_"+str(time.time())+".png Saved")
                else:
                    print("Error saving: ","static/captures/capture_"+config[1]+"_"+str(time.time())+".png")

            rawCapture.truncate(0)
    time.sleep(0.5)
