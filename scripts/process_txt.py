#coding=utf-8
import os
import random
from os import path

trainval = open('/opt/zhangjing/darknet/data/VOCdevkit/VOC2007/ImageSets/Main/benchmark_349_2.txt','w+')
with open('/opt/zhangjing/darknet/data/VOCdevkit/VOC2007/ImageSets/Main/benchmark_349_1.txt') as ann_file: #.read().strip().split()
	lines = ann_file.readlines()
	for i in xrange(len(lines)):
		l = lines[i]
		lst = l.strip().split()
		if len(lst)>-1:
			trainval.write('/opt/zhangjing/darknet/data/VOCdevkit/VOC2007/JPEGImages/' +lst[0]+".jpg" + "\n")
		'''if len(lst)>1:
			name = lst[0][:len(lst[0])-4]
			trainval.write(name + "\n")'''
trainval.close()
