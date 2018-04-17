#coding=utf-8
'''
脚本描述：先根据./darknet detector valid cfg/voc_test.data cfg/yolov3-voc-test.cfg backup/yolov3-voc_10000.weights -out 1000_ 生成每个类别对应的txt;
			再通过该脚本将bbox、置信度标注报图上并保存到指定的目录。
'''
import numpy as np
import matplotlib
matplotlib.use('Agg')
import os
import xml.dom.minidom
import cv2
import time

class_name_lst = ["autotruck", "crane", "digger", "mixerTruck", "forklift", "colorPlate", "pit", "bricksPile", "mound", "worker", "car"]  #改
pre = "14000_"  #改
folder_path_txt = "/opt/zhangjing/darknet/results/"  #改
save_image_folder = "/opt/zhangjing/darknet/results/test/"   #改
orig_image_folder = "/opt/zhangjing/darknet/data/VOCdevkit/VOC2007/JPEGImages/" #改

all_lst = []
image_class_name_lst = []
image_lst = []
for i in range(len(class_name_lst)):
	class_name = class_name_lst[i]
	temp_path = folder_path_txt + pre + class_name + ".txt"
	with open(temp_path, 'r') as ann_file:
		lines = ann_file.readlines()
		all_lst = all_lst + lines
		for i in xrange(len(lines)):
			l = lines[i]
			lst = l.strip().split()
			if 6 == len(lst):
				image_lst.append(lst[0])
				image_class_name_lst.append(class_name)
			
if len(image_class_name_lst)!= len(all_lst):
	print "error!!!!!!!!!!!!!!!!"

image_lst = list(set(image_lst))#list(set(lst)) 去除列表中重复的元素

image_num = len(image_lst)
for j in range(len(image_lst)):
	print j, image_num
	for i in range(len(all_lst)):	
		lst = all_lst[i].strip().split()
		class_name = image_class_name_lst[i]
		if 6 == len(lst):
			image_name = lst[0]
			if image_name==image_lst[j]:
				conf = lst[1]
				if conf > 0.3:
					xmin = int(float(lst[2]))
					ymin = int(float(lst[3]))
					xmax = int(float(lst[4]))
					ymax = int(float(lst[5]))
					
					orig_image_path = orig_image_folder + image_name + ".jpg"
					saveimge = cv2.imread(orig_image_path)
					
					cv2.rectangle(saveimge,(xmin, ymin),(xmax,ymax),(0,255,0),2) 
					cv2.putText(saveimge, str(conf)[:3], (xmin, ymin), cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,0))				   
					cv2.putText(saveimge, class_name, (xmin+50, ymin), cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,255))
		   
					save_image_path = save_image_folder + image_name + ".jpg"
					cv2.imwrite(save_image_path,saveimge)	 
		
		
	
	
 
