# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 15:25:41 2019

@author: hhh
"""
# create a YOLOv3 Keras model and save it to file
# based on https://github.com/experiencor/keras-yolo3
import numpy as np
from tensorflow import *
from keras.layers import Conv2D
from keras.layers import Input
from keras.layers import BatchNormalization
from keras.layers import LeakyReLU
from keras.layers import ZeroPadding2D
from keras.layers import UpSampling2D
from keras.layers import add, concatenate
from keras.models import Model
from numpy import expand_dims
from keras.models import load_model
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
import argparse
import os
import numpy as np
from keras.layers import Conv2D, Input, BatchNormalization, LeakyReLU, ZeroPadding2D, UpSampling2D
from keras.layers import add, concatenate
from keras.models import Model
import struct
from matplotlib import pyplot
from matplotlib.patches import Rectangle

import sqlite3


# load and prepare an image
def load_image_pixels(filename, shape):
    # load the image to get its shape
    image = load_img(filename)
    width, height = image.size
    # load the image with the required size
    image = load_img(filename, target_size=shape)
    # convert to numpy array
    image = img_to_array(image)
    # scale pixel values to [0, 1]
    image = image.astype('float32')
    image /= 255.0
    # add a dimension so that we have one sample
    image = expand_dims(image, 0)
    return image, width, height

def _sigmoid(x):
    return 1. / (1. + np.exp(-x))

class BoundBox:
    def __init__(self, xmin, ymin, xmax, ymax, objness = None, classes = None):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        
        self.objness = objness
        self.classes = classes

        self.label = -1
        self.score = -1

    def get_label(self):
        if self.label == -1:
            self.label = np.argmax(self.classes)
        
        return self.label
    
    def get_score(self):
        if self.score == -1:
            self.score = self.classes[self.get_label()]
            
        return self.score
    
def decode_netout(netout, anchors, obj_thresh, net_h, net_w):
    grid_h, grid_w = netout.shape[:2]
    nb_box = 3
    netout = netout.reshape((grid_h, grid_w, nb_box, -1))
    nb_class = netout.shape[-1] - 5

    boxes = []

    netout[..., :2]  = _sigmoid(netout[..., :2])
    netout[..., 4:]  = _sigmoid(netout[..., 4:])
    netout[..., 5:]  = netout[..., 4][..., np.newaxis] * netout[..., 5:]
    netout[..., 5:] *= netout[..., 5:] > obj_thresh

    for i in range(grid_h*grid_w):
        row = i / grid_w
        col = i % grid_w
        
        for b in range(nb_box):
            # 4th element is objectness score
            objectness = netout[int(row)][int(col)][b][4]
            #objectness = netout[..., :4]
            
            if(objectness.all() <= obj_thresh): continue
            
            # first 4 elements are x, y, w, and h
            x, y, w, h = netout[int(row)][int(col)][b][:4]

            x = (col + x) / grid_w # center position, unit: image width
            y = (row + y) / grid_h # center position, unit: image height
            w = anchors[2 * b + 0] * np.exp(w) / net_w # unit: image width
            h = anchors[2 * b + 1] * np.exp(h) / net_h # unit: image height  
            
            # last elements are class probabilities
            classes = netout[int(row)][col][b][5:]
            
            box = BoundBox(x-w/2, y-h/2, x+w/2, y+h/2, objectness, classes)
            #box = BoundBox(x-w/2, y-h/2, x+w/2, y+h/2, None, classes)

            boxes.append(box)

    return boxes
def correct_yolo_boxes(boxes, image_h, image_w, net_h, net_w):
    if (float(net_w)/image_w) < (float(net_h)/image_h):
        new_w = net_w
        new_h = (image_h*net_w)/image_w
    else:
        new_h = net_w
        new_w = (image_w*net_h)/image_h
        
    for i in range(len(boxes)):
        x_offset, x_scale = (net_w - new_w)/2./net_w, float(new_w)/net_w
        y_offset, y_scale = (net_h - new_h)/2./net_h, float(new_h)/net_h
        
        boxes[i].xmin = int((boxes[i].xmin - x_offset) / x_scale * image_w)
        boxes[i].xmax = int((boxes[i].xmax - x_offset) / x_scale * image_w)
        boxes[i].ymin = int((boxes[i].ymin - y_offset) / y_scale * image_h)
        boxes[i].ymax = int((boxes[i].ymax - y_offset) / y_scale * image_h)
        
# get all of the results above a threshold
def get_boxes(boxes, labels, thresh):
	v_boxes, v_labels, v_scores = list(), list(), list()
	# enumerate all boxes
	for box in boxes:
		# enumerate all possible labels
		for i in range(len(labels)):
			# check if the threshold for this label is high enough
			if box.classes[i] > thresh:
				v_boxes.append(box)
				v_labels.append(labels[i])
				v_scores.append(box.classes[i]*100)
				# don't break, many labels may trigger for one box
	return v_boxes, v_labels, v_scores

def do_nms(boxes, nms_thresh):
    if len(boxes) > 0:
        nb_class = len(boxes[0].classes)
    else:
        return
        
    for c in range(nb_class):
        sorted_indices = np.argsort([-box.classes[c] for box in boxes])

        for i in range(len(sorted_indices)):
            index_i = sorted_indices[i]

            if boxes[index_i].classes[c] == 0: continue

            for j in range(i+1, len(sorted_indices)):
                index_j = sorted_indices[j]

                if bbox_iou(boxes[index_i], boxes[index_j]) >= nms_thresh:
                    boxes[index_j].classes[c] = 0
                    
def bbox_iou(box1, box2):
    intersect_w = _interval_overlap([box1.xmin, box1.xmax], [box2.xmin, box2.xmax])
    intersect_h = _interval_overlap([box1.ymin, box1.ymax], [box2.ymin, box2.ymax])
    
    intersect = intersect_w * intersect_h

    w1, h1 = box1.xmax-box1.xmin, box1.ymax-box1.ymin
    w2, h2 = box2.xmax-box2.xmin, box2.ymax-box2.ymin
    
    union = w1*h1 + w2*h2 - intersect
    
    return float(intersect) / union


def _interval_overlap(interval_a, interval_b):
    x1, x2 = interval_a
    x3, x4 = interval_b

    if x3 < x1:
        if x4 < x1:
            return 0
        else:
            return min(x2,x4) - x1
    else:
        if x2 < x3:
             return 0
        else:
            return min(x2,x4) - x3     

# draw all results
def draw_boxes(filename, v_boxes, v_labels, v_scores):
	# load the image
	data = pyplot.imread(filename)
	# plot the image
	pyplot.imshow(data)
	# get the context for drawing boxes
	ax = pyplot.gca()
	# plot each box
	for i in range(len(v_boxes)):
		box = v_boxes[i]
		# get coordinates
		y1, x1, y2, x2 = box.ymin, box.xmin, box.ymax, box.xmax
		# calculate width and height of the box
		width, height = x2 - x1, y2 - y1
		# create the shape
		rect = Rectangle((x1, y1), width, height, fill=False, color='white')
		# draw the box
		ax.add_patch(rect)
		# draw text and score in top left corner
		label = "%s (%.3f)" % (v_labels[i], v_scores[i])
		pyplot.text(x1, y1, label, color='white')
	# show the plot
	pyplot.show()

def get_object(photo_filename):
    # define the expected input shape for the model
    input_w, input_h = 416, 416
    # define our new photo
    # photo_filename = 'zebra.jpg'
    # load and prepare image
    image, image_w, image_h = load_image_pixels(photo_filename, (input_w, input_h))
    # make prediction
    yhat = model.predict(image)
    # summarize the shape of the list of arrays
    #print([a.shape for a in yhat]) 
    # define the anchors
    anchors = [[116,90, 156,198, 373,326], [30,61, 62,45, 59,119], [10,13, 16,30, 33,23]]
    # define the probability threshold for detected objects
    class_threshold = 0.6
    boxes = list()
    for i in range(len(yhat)):
	# decode the output of the network
    	boxes += decode_netout(yhat[i][0], anchors[i], class_threshold, input_h, input_w)
    # correct the sizes of the bounding boxes for the shape of the image
    correct_yolo_boxes(boxes, image_h, image_w, input_h, input_w) 
    # suppress non-maximal boxes
    do_nms(boxes, 0.5)   
    # define the labels
    labels = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", 
              "truck","boat", "traffic light", "fire hydrant", "stop sign", "parking meter",
              "bench","bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", 
              "zebra", "giraffe","backpack", "umbrella", "handbag", "tie", "suitcase",
              "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", 
              "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana",
              "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", 
              "donut", "cake","chair", "sofa", "pottedplant", "bed", "diningtable",
              "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock",
              "vase", "scissors", "teddy bear", "hair drier", "toothbrush"]
    v_boxes, v_labels, v_scores = get_boxes(boxes, labels, class_threshold)
    return v_labels,v_scores

import cv2
def video_preprocessing(video_path):
    cap = cv2.VideoCapture(video_path)
    currentFrame = 0
    second=0.0
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps
    index=video_path.rfind("\\")
    videoName=video_path[(index+1):len(video_path)-4]
    start=0
    end=0
    while(True):
        if(currentFrame%fps==0):                
            second=second+1
            # Capture frame-by-frame
        ret, frame = cap.read()
        if(not ret):
            cap.release()
            cv2.destroyAllWindows()
            print("finishing")
            break
        if(second%5==0):
            #Saves image of the current frame in jpg file
            name = 'E:\\Projects\\data\\frame' + str(currentFrame) + '.jpg'
            cv2.imwrite(name, frame)
            labels,scores=get_object(name)
            for index in range(len(labels)):
                if(scores[index]<88.0):
                    continue
                c.execute("select * from objects where object=:object and name=:name",
                          {'object':labels[index],'name':videoName})
                allRows=c.fetchall()
                if(len(allRows)>0):
                    difference=second-(allRows[len(allRows)-1][4]);
                    if(second>=5):
                        start=second-5
                    else:
                        start=0
                    if(second+5>duration):
                        end=duration
                    else:
                        end=second+5
                    if(difference>=0 and difference<=5):
                        c.execute("update objects set end=:end where name =:name and
                                  "path=:path and object=:object and start=:start",
                                  "{'end':end ,'name':(allRows[len(allRows)-1][0]),
                                   'path':allRows[len(allRows)-1][1],
                                   'object':allRows[len(allRows)-1][2],
                                   'start':allRows[len(allRows)-1][3]})
                        conn.commit()
                    elif(difference>0):      
                        c.execute("insert into objects values(:name,:path,:object
                                                              ",:start,:end)",
    {'name':videoName,'path':video_path,'object':labels[index],'start':start,'end':end})
                        conn.commit()
                else:
                    if(second>=5):
                        start=second-5
                    else:
                        start=0
                    if(second+5>duration):
                        end=duration
                    else:
                        end=second+5
                    c.execute("insert into objects values(:name,:path,:object
                                                          ",:start,:end)",
    {'name':videoName,'path':video_path,'object':labels[index],'start':start,'end':end})
                    conn.commit()
        # To stop duplicate images
        currentFrame += 1

import MySQLdb
conn=sqlite3.connect('SearchInVideo4.db')
c=conn.cursor()
c.execute("""Create Table if not exists objects(
        name text,
        path text,
        object text,
        start real,
        end real
  )""")


conn = MySQLdb.connect(host="localhost",    # your host, usually localhost
                     user="root",         # your username
                     passwd="yarab19234",  # your password
                     db="graduation")        # name of the data base

# you must create a Cursor object. It will let
#  you execute all the queries you need
c = conn.cursor()

       
# load yolov3 model
model = load_model('E:\\Projects\\model.h5')
video_preprocessing("E:\\Projects\\Video\\search2.mp4")

conn.close()




    
    
























