#coding=utf-8
# --------------------------------------------------------
# Fast/er R-CNN
# Licensed under The MIT License [see LICENSE for details]
# Written by Bharath Hariharan
# --------------------------------------------------------

import xml.etree.ElementTree as ET
import os
import cPickle
import numpy as np
import sys
import re
import matplotlib.pyplot as plt
def parse_rec(filename):
	""" Parse a PASCAL VOC xml file """
	tree = ET.parse(filename)
	objects = []
	for obj in tree.findall('object'):
		obj_struct = {}
		obj_struct['name'] = obj.find('name').text
		obj_struct['pose'] = obj.find('pose').text
		obj_struct['truncated'] = int(obj.find('truncated').text)
		obj_struct['difficult'] = int(obj.find('difficult').text)
		bbox = obj.find('bndbox')
		obj_struct['bbox'] = [int(bbox.find('xmin').text),
							  int(bbox.find('ymin').text),
							  int(bbox.find('xmax').text),
							  int(bbox.find('ymax').text)]
		objects.append(obj_struct)

	return objects

def voc_ap(rec, prec, use_07_metric=False):
	""" ap = voc_ap(rec, prec, [use_07_metric])
	Compute VOC AP given precision and recall.
	If use_07_metric is true, uses the
	VOC 07 11 point method (default:False).
	"""
	if use_07_metric:
		# 11 point metric
		ap = 0.
		for t in np.arange(0., 1.1, 0.1):
			if np.sum(rec >= t) == 0:
				p = 0
			else:
				p = np.max(prec[rec >= t])
			ap = ap + p / 11.
	else:
		# correct AP calculation
		# first append sentinel values at the end
		mrec = np.concatenate(([0.], rec, [1.]))
		mpre = np.concatenate(([0.], prec, [0.]))

		# compute the precision envelope
		for i in range(mpre.size - 1, 0, -1):
			mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])

		# to calculate area under PR curve, look for points
		# where X axis (recall) changes value
		i = np.where(mrec[1:] != mrec[:-1])[0]

		# and sum (\Delta recall) * prec
		ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
	return ap

def voc_eval(detpath,
			 annopath,
			 imagesetfile,
			 classname,
			 confidence_threshold=0.0,
			 ovthresh=0.5,
			 use_07_metric=False):
	"""rec, prec, ap = voc_eval(detpath,
								annopath,
								imagesetfile,
								classname,
								[ovthresh],
								[use_07_metric])

	Top level function that does the PASCAL VOC evaluation.

	detpath: Path to detections
		detpath.format(classname) should produce the detection results file.
	annopath: Path to annotations
		annopath.format(imagename) should be the xml annotations file.
	imagesetfile: Text file containing the list of images, one image per line.
	classname: Category name (duh)
	cachedir: Directory for caching the annotations
	[ovthresh]: Overlap threshold (default = 0.5)
	[use_07_metric]: Whether to use VOC07's 11 point AP computation
		(default False)
	"""
	# assumes detections are in detpath.format(classname)
	# assumes annotations are in annopath.format(imagename)
	# assumes imagesetfile is a text file with each line an image name
	# cachedir caches the annotations in a pickle file

	# first load gt
	#if not os.path.isdir(cachedir):
	#	 os.mkdir(cachedir)
	#cachefile = os.path.join(cachedir, 'annots.pkl')
	# read list of images
	with open(imagesetfile, 'r') as f:
		lines = f.readlines()
	imagenames = [x.strip() for x in lines]

	#if not os.path.isfile(cachefile):
		# load annots
	recs = {}
	for i, imagename in enumerate(imagenames):
		#print i, imagename
		recs[imagename] = parse_rec(annopath.format(imagename))
		if i % 100 == 0:
			print 'Reading annotation for {:d}/{:d}'.format(
				i + 1, len(imagenames))
	# save
	#print 'Saving cached annotations to {:s}'.format(cachefile)
	#with open(cachefile, 'w') as f:
	#	 cPickle.dump(recs, f)
	#else:
		# load
	#	 with open(cachefile, 'r') as f:
	#		 recs = cPickle.load(f)

	# extract gt objects for this class
	class_recs = {}
	npos = 0
	for imagename in imagenames:
		R = [obj for obj in recs[imagename] if obj['name'] == classname]
		bbox = np.array([x['bbox'] for x in R])
		difficult = np.array([x['difficult'] for x in R]).astype(np.bool)
		det = [False] * len(R)
		npos = npos + sum(~difficult)
		class_recs[imagename] = {'bbox': bbox,
								 'difficult': difficult,
								 'det': det}

	# read dets
	detfile = detpath.format(classname)
	with open(detfile, 'r') as f:
		lines = f.readlines()

	splitlines = [x.strip().split(' ') for x in lines]
	image_ids = [x[0] for x in splitlines]
	confidence = np.array([float(x[1]) for x in splitlines])
	BB = np.array([[float(z) for z in x[2:]] for x in splitlines])

	#print ("confidence:", confidence)
	# sort by confidence
	sorted_ind = np.argsort(-confidence)
	#如果只想计算大于confidence_threshold的输出结果的mAP
	sorted_ind1 = np.where(confidence[sorted_ind] >= confidence_threshold)[0]#np.argsort(-confidence<=-.3) #加
	sorted_ind = sorted_ind[sorted_ind1]						#加

	sorted_scores = np.sort(-confidence)
	BB = BB[sorted_ind, :]
	image_ids = [image_ids[x] for x in sorted_ind]

	# go down dets and mark TPs and FPs
	nd = len(image_ids)
	tp = np.zeros(nd)
	fp = np.zeros(nd)
	for d in range(nd):
		R = class_recs[image_ids[d]]
		bb = BB[d, :].astype(float)
		ovmax = -np.inf
		BBGT = R['bbox'].astype(float)

		if BBGT.size > 0:
			# compute overlaps
			# intersection
			ixmin = np.maximum(BBGT[:, 0], bb[0])
			iymin = np.maximum(BBGT[:, 1], bb[1])
			ixmax = np.minimum(BBGT[:, 2], bb[2])
			iymax = np.minimum(BBGT[:, 3], bb[3])
			iw = np.maximum(ixmax - ixmin + 1., 0.)
			ih = np.maximum(iymax - iymin + 1., 0.)
			inters = iw * ih

			# union
			uni = ((bb[2] - bb[0] + 1.) * (bb[3] - bb[1] + 1.) +
				   (BBGT[:, 2] - BBGT[:, 0] + 1.) *
				   (BBGT[:, 3] - BBGT[:, 1] + 1.) - inters)

			overlaps = inters / uni
			ovmax = np.max(overlaps)
			jmax = np.argmax(overlaps)

		if ovmax > ovthresh:
			if not R['difficult'][jmax]:
				if not R['det'][jmax]:
					tp[d] = 1.
					R['det'][jmax] = 1
				else:
					fp[d] = 1.
		else:
			fp[d] = 1.

	# compute precision recall
	fp = np.cumsum(fp)
	tp = np.cumsum(tp)
	rec = tp / float(npos)
	# avoid divide by zero in case the first detection matches a difficult
	# ground truth
	prec = tp / np.maximum(tp + fp, np.finfo(np.float64).eps)
	ap = voc_ap(rec, prec, use_07_metric)

	return rec, prec, ap


if __name__ =='__main__':
	'''if len(sys.argv)<3:
		print 'error!!!'
		print 'the argv must be python 123.py [detpath] [testfile] [testname]'
	else:'''
	detpath= "/opt/zhangjing/darknet/results/10000_"  #改 #sys.argv[1]
	testfile= "/opt/zhangjing/darknet/data/VOCdevkit/2007_benchmark_349_mAP.txt"  #改 #sys.argv[2]
	confidence_threshold = 0.0 #改
	#confidence_threshold = sys.argv[3]
	#print confidence_threshold
	class_name_lst = ["autotruck", "crane", "digger", "mixerTruck", "forklift", "colorPlate", "pit", "bricksPile", "mound", "worker", "car"] #改
	all_mAP = 0.0
	mAP_f=open('mAP.txt','w')
	mAP_f.write(detpath + "\n")
	mAP_lst = []
	for i in range(len(class_name_lst)):
		testname=class_name_lst[i] #sys.argv[3]
		name_id=re.compile('.*/(.*)\.jpg')
		name_xml = re.compile('(.*/).*.jpg')
		#print(re.findall(name_id,'456/123.jpg'))
		with open(testfile, 'r') as f:
			lines = f.readlines()
		f=open('123_testname.txt','w')
		for i in lines:
			temp=re.findall(name_id,i)
			f.write(temp[0]+'\n')
		f.close()
		testfilepath=os.getcwd()+'/123_testname.txt'
		temp = re.findall(name_xml, lines[0])
		annopath=temp[0]+'{}.xml'
		temp_path = detpath+testname+".txt"
		print temp_path
		mAP = voc_eval(temp_path,annopath,testfilepath,testname,confidence_threshold)[2]
		all_mAP = all_mAP + mAP
		mAP_f.write(testname + ": " + str(mAP)[:5] + "\n")
		mAP_lst.append( str(mAP)[:5])
		print testname, mAP
		
	print ("mAP: ", all_mAP/len(class_name_lst))
	mAP_f.write("eval" + ": " + str(all_mAP/len(class_name_lst))[:5] + "\n")

	for i in range(len(class_name_lst)):
		testname=class_name_lst[i]
		print testname, ":",mAP_lst[i]
	print "eval=", str(all_mAP/len(class_name_lst))[:5]
