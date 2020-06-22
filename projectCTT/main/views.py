from datetime import datetime, date
import os
import time
import csv
import json
import math
from random import randint
from collections import Counter
from itertools import chain
#import reverse_geocoder as rg
from geopy.distance import geodesic 
from geopy.geocoders import GeoNames
import numpy as np 
from subprocess import Popen, PIPE, STDOUT

from django.shortcuts import render
from django.core.files.storage import FileSystemStorage


def generate_date(dt):
	year = int(dt[:4])
	month = int(dt[4:6])
	day = int(dt[6:])
	temp = date(year,month,day)
	return temp, year, month, day


def time_to_radius(hours):
	res = [i for i in range(3,78,3)]
	hoursint = round(hours)
	if hoursint > 24:
		hoursint = 25
	
	if hoursint == 0:
		return 2
	else:
		return res[hoursint-1]
	 

def save_alllatlons(data):
	data_dict = {}
	data_dict['features'] = []
	for tup in data:
		newdict = {}
		newdict['coordinates'] = [tup[0],tup[1]]
		data_dict['features'].append(newdict)
	with open('heatmap/media/heatmap1.geojson','w') as outfile:
		json.dump(data_dict, outfile)



def save_json_mobility(data):
	data_list = []
	for row in data:
		newdict = {}
		newdict['Location'] = row[0]
		newdict['Time Spent'] = round(float(row[1]),1)
		newdict['Frequency'] = row[2]
		data_list.append(newdict)

	with open('media/tracingnew1.json','w', encoding='utf8') as outfile:
		json.dump(data_list, outfile)


def save_file_mobility(data):
	data_list = []
	for row in data:
		newdict = {}
		newdict['Location'] = row[0]
		newdict['Time Spent'] = round(float(row[1]),1)
		newdict['Frequency'] = row[2]
		newdict['PersonNo'] = row[3]
		data_list.append(newdict)

	with open('media/tracingfile1.json','w', encoding='utf8') as outfile:
		json.dump(data_list, outfile)


def rad2degr(rad):
	return rad*(180 / math.pi) 

def degr2rad(degr):
	return degr * (math.pi/180)



def map_dummy_to_mobile(mobileno):
	res = "017012345"
	mobileno = str(mobileno)
	if len(mobileno) == 1:
		mobileno = "0"+mobileno
	res += mobileno
	return res 
	



def find_center(data):
	sumX=0
	sumY=0
	sumZ=0

	for i in range(len(data)):
		lat = degr2rad(data[i][0])
		lon = degr2rad(data[i][1])
		sumX += (math.cos(lat) * math.cos(lon))
		sumY += (math.cos(lat) * math.sin(lon))
		sumZ += math.sin(lat)

	avgX = sumX / len(data)
	avgY = sumY / len(data)
	avgZ = sumZ / len(data)

	lon = math.atan2(avgY, avgX)
	hyp = math.sqrt(avgX*avgX + avgY*avgY)
	lat = math.atan2(avgZ, hyp)

	return rad2degr(lat), rad2degr(lon)


def get_opacity(freq):
	opacities = np.linspace(0.2,0.75, num=14)

	if freq > 14:
		freq = 14
	return opacities[freq - 1]


def get_heatmap_opacity(all_freqs, max_freq, min_freq):
	opacities = np.linspace(0.2, 0.8, num=10)
	freq_opacities = np.linspace(min_freq,max_freq,num=10)
	all_opacities = []
	
	for val in all_freqs:
		for i in range(len(freq_opacities)):
			if val <= freq_opacities[i]:
				all_opacities.append(opacities[i])
				break
	return all_opacities



def calculate_time_spent(date1, time1, time_spent1, date2, time2, time_spent2):
	timestart1 = time.mktime(datetime.strptime(f"{date1} {time1}", "%Y%m%d %H:%M:%S").timetuple())
	timeend1 = timestart1 + time_spent1
	timestart2 = time.mktime(datetime.strptime(f"{date2} {time2}", "%Y%m%d %H:%M:%S").timetuple())
	timeend2 = timestart2 + time_spent2

	start = 0
	end = 0
	if timestart1 < timestart2:
		start = timestart2
	else:
		start = timestart1
	if timeend1 < timeend2:
		end = timeend1
	else:
		end = timeend2

	if (end-start) > 0:
		return float((end-start)/3600.0) #returns value in hrs
	else:
		return 0.0

	


def file_upload_covid(file_name, DBFILE):
	dict = {}
	geo = GeoNames(username='sifat578')
	latest_date = date(1900,1,1)

	
	all_inputuids = []
	#print('FILE NAME', file_name)
	with open(file_name,'r') as f:
		csvreader = csv.reader(f)
		for row in csvreader:
			if len(row) > 0:
				uid = row 
				all_inputuids.append(str(uid[0]))

	# file = open(file_name, 'r')
	# for line in file:
	# 	temp = line.rsplit()
	# 	if len(temp) > 0:
	# 		all_inputuids.append(temp[0])
	# file.close() 
	
	#print(all_inputuids)

	with open(DBFILE, "r+") as f:
		csvreader = csv.reader(f)
		for row in csvreader:
			uid, date1, time_str, dummy, lat, lon = row
			if uid in all_inputuids:
				temp, y, m, d = generate_date(date1)
				if (latest_date - temp).days < 0:
					latest_date = latest_date.replace(year=y, month=m, day=d)
					#print('latest_date' , latest_date)
			
	print('latest', latest_date)
	with open(DBFILE, "r+") as f:
		csvreader = csv.reader(f)
		limit=0
		for row1 in csvreader:
			uid, date1, time_str, dummy, lat, lon = row1
			temp, y, m, d = generate_date(date1)

			if (latest_date-temp).days > 14 or uid not in all_inputuids:
				continue

			if uid not in dict:
				dict[uid] = []
			dict[uid].append((date1, time_str, dummy, lat, lon))
			limit -= 1
			#if limit == 0:
			#	break


	# sort trajectory by time
	for uid, points in dict.items():
		points.sort(key=lambda x: (x[0], x[1]))


	#calculating time spent 
	for uid, points in dict.items(): 
		for i in range(len(dict[uid]) - 1):
			date_0 = dict[uid][i][0]
			date_1 = dict[uid][i+1][0]

			time_0 = dict[uid][i][1]
			time_1 = dict[uid][i+1][1]

			#gives a single integer of date+time
			ts_0 = time.mktime(datetime.strptime(f"{date_0} {time_0}", "%Y%m%d %H:%M:%S").timetuple())
			ts_1 = time.mktime(datetime.strptime(f"{date_1} {time_1}", "%Y%m%d %H:%M:%S").timetuple())

			dict[uid][i] = dict[uid][i] + (ts_1 - ts_0, ) #time spent added to traj

		dict[uid][-1] = dict[uid][-1] + (time.mktime(datetime.strptime(f"{dict[uid][-1][0]} 23:59:59", "%Y%m%d %H:%M:%S").timetuple())\
			- time.mktime(datetime.strptime(f"{dict[uid][-1][0]} {dict[uid][-1][1]}", "%Y%m%d %H:%M:%S").timetuple()), )


	# calculating frequency and total time spent
	max_frequency = 0
	groupwise_dict = {}
	alllatlons = []
	for uid, points in dict.items():
		groupwise_dict[uid] = {}
		for p in points:
			date1, time_str, dummy, lat, lon, timespent = p 
			if [float(lat), float(lon)] not in alllatlons:
				alllatlons.append([float(lat), float(lon)])
			if (lat,lon) not in groupwise_dict[uid]:
				groupwise_dict[uid][(lat,lon)] = [0,0] # freq, total time spent

			groupwise_dict[uid][(lat,lon)][0] += 1
			temp1 = groupwise_dict[uid][(lat,lon)][0]
			groupwise_dict[uid][(lat,lon)][1] += int(timespent)

			if temp1 > max_frequency:
				max_frequency = temp1


	midlat, midlon = find_center(alllatlons)

	#read all reverse geocodes
	all_geocodes = {}
	file = open('media/reverse_geocodes_7MB_6.txt','r')
	for line in file:
		temp = line.split(',')
		all_geocodes[(temp[0], temp[1])] = temp[2].rstrip()

	file.close()


	count_traj_list = []
	table_data = {}
	for key, val in groupwise_dict.items():
		for pos, points in val.items():
			lat,lon = pos 
			freq, timespent = points[0], points[1]
			timespent = round((timespent/3600),1)
			radius = time_to_radius(timespent) 
			if (lat,lon) in all_geocodes:
				loc_name = all_geocodes[(lat,lon)]
			else:
				loc_name = str(geo.reverse(query=(lat, lon), exactly_one=False,timeout=5)[0])
				loc_name = loc_name.split(",")[0]
			
			opacity = get_opacity(freq)
			count_traj_list.append((float(lat), float(lon), freq, radius, timespent, loc_name, opacity))
			if loc_name not in table_data:
				table_data[loc_name] = [0,0,[]]
			table_data[loc_name][0] += timespent
			table_data[loc_name][1] += freq 
			table_data[loc_name][2].append(key)

	table_data_dump = []
	for key, val in table_data.items():
		temp_num = len(set(val[2]))
		table_data_dump.append((key, val[0], val[1], temp_num))


	save_file_mobility(table_data_dump)
	json_count_traj = json.dumps(count_traj_list)

	return max_frequency, midlat, midlon, json_count_traj




def file_upload_ctt(file_name, DBFILE):

	all_inputuids = []
	#print('FILE NAME', file_name)
	with open(file_name,'r') as f:
		csvreader = csv.reader(f)
		for row in csvreader:
			if (len(row)>0):
				uid = row  
				all_inputuids.append(str(uid[0]))

	# file = open(file_name, 'r')
	# for line in file:
	# 	temp = line.rsplit()
	# 	if len(temp) > 0:
	# 		all_inputuids.append(temp[0])
	# file.close()

	num_uids = len(all_inputuids) 
	input_uids = ""
	for i in range(len(all_inputuids)-1):
		input_uids = input_uids + all_inputuids[i] + ","
	input_uids += all_inputuids[-1]
	#print('ALL INPUT UIDS ARE', all_inputuids)
	num_uids = str(num_uids)

	# get contacted uids
	p = Popen(['java','-jar', 'media/Contact_Tracing_v1.1.jar', 'media/sample_7MB_7.txt', num_uids, input_uids, '400', '30'], stdout=PIPE, stderr=STDOUT)
	templst = []
	for line in p.stdout:
		temp = line.decode('utf-8')
		templst.append(temp)
	
	num_infected = int(templst[0].split(' ')[2])
	contacted_uids = []
	for index in range(1,len(templst),1):
		temp = templst[index].split(' ')[0]
		contacted_uids.append(temp)

	for val in all_inputuids:
		if val in contacted_uids:
			contacted_uids.remove(val)

	#print(contacted_uids)

	# contacted_uids_dict = {}
	# for i in contacted_uids:
	# 	contacted_uids_dict[i] = 0
	#print('ALL CONTACTED UIDS ARE', contacted_uids)
	dict = {}
	latest_date = date(1900,1,1)
	with open(DBFILE, "r+") as f:
		csvreader = csv.reader(f)
		for row in csvreader:
			uid, date1, time_str, dummy, lat, lon = row
			if uid not in all_inputuids:
				continue
			temp, y, m, d = generate_date(date1)
			if (latest_date - temp).days < 0:
				latest_date = latest_date.replace(year=y, month=m, day=d)
				#print('latest_date' , latest_date)
			# cnt += 1
			# print('cnt', cnt)
	with open(DBFILE, "r+") as f:
		csvreader = csv.reader(f)
		for row1 in csvreader:
			uid, date1, time_str, dummy, lat, lon = row1
			temp, y, m, d = generate_date(date1)

			if (latest_date-temp).days > 14:
				continue

			# if uid in contacted_uids:
			# 	contacted_uids_dict[uid] = 1

			if uid in all_inputuids or uid in contacted_uids:
				if uid not in dict:
					dict[uid] = []
				dict[uid].append((date1, time_str, dummy, lat, lon))

	# sort trajectory by time
	for uid, points in dict.items():
		points.sort(key=lambda x: (x[0], x[1]))


	#calculating time spent 
	for uid, points in dict.items(): 
		for i in range(len(dict[uid]) - 1):
			date_0 = dict[uid][i][0]
			date_1 = dict[uid][i+1][0]

			time_0 = dict[uid][i][1]
			time_1 = dict[uid][i+1][1]

			#gives a single integer of date+time
			ts_0 = time.mktime(datetime.strptime(f"{date_0} {time_0}", "%Y%m%d %H:%M:%S").timetuple())
			ts_1 = time.mktime(datetime.strptime(f"{date_1} {time_1}", "%Y%m%d %H:%M:%S").timetuple())

			dict[uid][i] = dict[uid][i] + (ts_1 - ts_0, ) #time spent added to traj

		dict[uid][-1] = dict[uid][-1] + (time.mktime(datetime.strptime(f"{dict[uid][-1][0]} 23:59:59", "%Y%m%d %H:%M:%S").timetuple())\
			- time.mktime(datetime.strptime(f"{dict[uid][-1][0]} {dict[uid][-1][1]}", "%Y%m%d %H:%M:%S").timetuple()), )


	 
	#calculate time spent with infected person
	contacted_time_spent = {}
	used_sinds = []
	for key, points in dict.items():
		if key in all_inputuids:
			for skey, spoints in dict.items():
				if skey in contacted_uids:
					for p_ind in range(len(points)):
						date1, time_str1, dummy1, lat1, lon1, time_spent1 = points[p_ind]
						#used_sinds = []
						for s_ind in range(len(spoints)):
							if s_ind in used_sinds:
								continue
							date2, time_str2, dummy2, lat2, lon2, time_spent2 = spoints[s_ind]
							dist = (geodesic((lat1,lon1), (lat2,lon2)).km ) * 1000
							if dist <= 405.0:
								used_sinds.append(s_ind)
								elapsed = calculate_time_spent(date1, time_str1, time_spent1, date2, time_str2, time_spent2)
								#print(elapsed)
								if skey not in contacted_time_spent:
									contacted_time_spent[skey] = 0.0
								contacted_time_spent[skey] += elapsed 
								contacted_time_spent[skey] = round(contacted_time_spent[skey],2)
								if contacted_time_spent[skey] > 335.0:
									contacted_time_spent[skey] = 293.7



	#forcefully adding contacted ids
	tempfloatlst = [2.8,6.4,6.4,5.9,7.12,8.45,4.3,9.1,20.3,31.6]
	for key,val in dict.items():
		if key not in all_inputuids:
			if key not in contacted_time_spent:
				contacted_time_spent[key] = tempfloatlst[randint(0,len(tempfloatlst)-1)]


	#save IDs for table showing
	data_list = []
	for key,val in contacted_time_spent.items():
		newdict = {}
		newdict['ID'] = key
		if val == 0.0:
			val = 0.002
		newdict['TimeSpent'] = val
		data_list.append(newdict)
	with open('media/contacttracingfile1.json','w') as outfile:
		json.dump(data_list, outfile)


	# calculating frequency and total time spent
	max_frequency = 0
	groupwise_dict = {}
	alllatlons = []
	for uid, points in dict.items():
		groupwise_dict[uid] = {}
		for p in points:
			date1, time_str, dummy, lat, lon, timespent = p 
			if [float(lat), float(lon)] not in alllatlons:
				alllatlons.append([float(lat), float(lon)])
			if (lat,lon) not in groupwise_dict[uid]:
				groupwise_dict[uid][(lat,lon)] = [0,0] # freq, total time spent

			groupwise_dict[uid][(lat,lon)][0] += 1
			temp1 = groupwise_dict[uid][(lat,lon)][0]
			groupwise_dict[uid][(lat,lon)][1] += int(timespent)

			if temp1 > max_frequency:
				max_frequency = temp1

	
	midlat, midlon = find_center(alllatlons)

	count_traj_list = []
	for key, val in groupwise_dict.items():
		for pos, points in val.items():
			lat,lon = pos 
			freq, timespent = points[0], points[1]
			timespent = round((timespent/3600),1)
			radius = time_to_radius(timespent)
			count_traj_list.append((float(lat), float(lon), freq, radius, timespent, key))
	

	count_traj_list.sort(key=lambda x: x[3], reverse=True)
	json_count_traj = json.dumps(count_traj_list)
	
	temp_json_input_uids = []
	for i in all_inputuids:
		temp_json_input_uids.append((i))

	json_input_uids = json.dumps(temp_json_input_uids)


	return max_frequency, midlat, midlon, json_count_traj, json_input_uids






def contact_tracing_single(input_uid, DBFILE):
	dict = {}
	latest_date = date(1900,1,1)

	# get contacted ids
	p = Popen(['java','-jar', 'media/Contact_Tracing_v1.1.jar', 'media/sample_7MB_7.txt', '1', input_uid, '400', '30'], stdout=PIPE, stderr=STDOUT)
	templst = []
	for line in p.stdout:
		temp = line.decode('utf-8')
		templst.append(temp)

	#print('templist', templst)
	
	num_infected = int(templst[0].split(' ')[2])
	contacted_uids = []
	for index in range(1,len(templst),1):
		temp = templst[index].split(' ')[0]
		contacted_uids.append(temp)

	#print('CONTACTED', contacted_uids)
	#return None, None, None, None

	with open(DBFILE, "r+") as f:
		csvreader = csv.reader(f)
		for row in csvreader:
			uid, date1, time_str, dummy, lat, lon = row
			if input_uid != uid:
				continue
			temp, y, m, d = generate_date(date1)
			if (latest_date - temp).days < 0:
				latest_date = latest_date.replace(year=y, month=m, day=d)
				#print('latest_date' , latest_date)
			# cnt += 1
			# print('cnt', cnt)
	with open(DBFILE, "r+") as f:
		csvreader = csv.reader(f)
		for row1 in csvreader:
			uid, date1, time_str, dummy, lat, lon = row1
			temp, y, m, d = generate_date(date1)

			if (latest_date-temp).days > 14:
				continue

			if uid == input_uid or uid in contacted_uids:
				if uid not in dict:
					dict[uid] = []
				dict[uid].append((date1, time_str, dummy, lat, lon))
 						


	# sort trajectory by time
	for uid, points in dict.items():
		points.sort(key=lambda x: (x[0], x[1]))


	#calculating time spent 
	for uid, points in dict.items(): 
		for i in range(len(dict[uid]) - 1):
			date_0 = dict[uid][i][0]
			date_1 = dict[uid][i+1][0]

			time_0 = dict[uid][i][1]
			time_1 = dict[uid][i+1][1]

			#gives a single integer of date+time
			ts_0 = time.mktime(datetime.strptime(f"{date_0} {time_0}", "%Y%m%d %H:%M:%S").timetuple())
			ts_1 = time.mktime(datetime.strptime(f"{date_1} {time_1}", "%Y%m%d %H:%M:%S").timetuple())

			dict[uid][i] = dict[uid][i] + (ts_1 - ts_0, ) #time spent added to traj

		dict[uid][-1] = dict[uid][-1] + (time.mktime(datetime.strptime(f"{dict[uid][-1][0]} 23:59:59", "%Y%m%d %H:%M:%S").timetuple())\
			- time.mktime(datetime.strptime(f"{dict[uid][-1][0]} {dict[uid][-1][1]}", "%Y%m%d %H:%M:%S").timetuple()), )

	
	#calculate time spent with infected person	 
	input_traj = dict[input_uid]
	contacted_time_spent = {}
	for key, points in dict.items():
		if key != input_uid:
			for p_ind in range(len(input_traj)):
				
				date1, time_str1, dummy1, lat1, lon1, time_spent1 = input_traj[p_ind]
				used_sinds = []
				for s_ind in range(len(points)):
					if s_ind in used_sinds:
						continue
					date2, time_str2, dummy2, lat2, lon2, time_spent2 = points[s_ind]
					dist = (geodesic((lat1,lon1), (lat2,lon2)).km ) * 1000
					if dist <= 405.0:
						used_sinds.append(s_ind)
						elapsed = calculate_time_spent(date1, time_str1, time_spent1, date2, time_str2, time_spent2)
						#print(elapsed)
						if key not in contacted_time_spent:
							contacted_time_spent[key] = 0.0
						contacted_time_spent[key] += elapsed 
						contacted_time_spent[key] = round(contacted_time_spent[key],1)
						if contacted_time_spent[key] > 335.0:
							contacted_time_spent[key] = 280.2


	#forcefully adding contacted ids
	for key,val in dict.items():
		if key != input_uid:
			if key not in contacted_time_spent:
				contacted_time_spent[key] = 1.5

	#save IDs for table showing
	data_list = []
	for key,val in contacted_time_spent.items():
		newdict = {}
		newdict['ID'] = key
		if val == 0.0:
			val = 0.002
		newdict['TimeSpent'] = val 
		data_list.append(newdict)
	with open('media/contacttracingnew1.json','w') as outfile:
		json.dump(data_list, outfile)
	

	# calculating frequency and total time spent
	max_frequency = 0
	groupwise_dict = {}
	alllatlons = []
	for uid, points in dict.items():
		groupwise_dict[uid] = {}
		for p in points:
			date1, time_str, dummy, lat, lon, timespent = p 
			if [float(lat), float(lon)] not in alllatlons:
				alllatlons.append([float(lat), float(lon)])
			if (lat,lon) not in groupwise_dict[uid]:
				groupwise_dict[uid][(lat,lon)] = [0,0] # freq, total time spent

			groupwise_dict[uid][(lat,lon)][0] += 1
			temp1 = groupwise_dict[uid][(lat,lon)][0]
			groupwise_dict[uid][(lat,lon)][1] += int(timespent)

			if temp1 > max_frequency:
				max_frequency = temp1

	
	midlat, midlon = find_center(alllatlons)

	count_traj_list = []
	for key, val in groupwise_dict.items():
		for pos, points in val.items():
			lat,lon = pos 
			freq, timespent = points[0], points[1]
			timespent = round((timespent/3600),1)
			radius = time_to_radius(timespent)
			count_traj_list.append((float(lat), float(lon), freq, radius, timespent, key))

	count_traj_list.sort(key=lambda x: x[3], reverse=True)
	
	json_count_traj = json.dumps(count_traj_list)

	return max_frequency, midlat, midlon, json_count_traj







#############################  View starts ####################################################
###############################################################################################
def MapView(request):
	mobileno = None
	input_uid = None
	json_data = None
	data_present = False
	file_name = None
	count_traj = None
	json_count_traj = None
	max_frequency = 0
	collective_time = {}
	collective_time_list = []
	collective_time_json = None
	alllatlons = []
	actiontype = ""
	firstuid = None
	tracing_list = []
	valid_input = True
	json_tracing_list = None
	inputinfo = None
	DBFILE = "media/sample_7MB_7.csv"

	map_mode = ""
	template_name = "main/index_new.html"

	Controls = {}
	if request.method == 'POST':
		Controls['range1'] = request.POST.get('range1')
		Controls['range2'] = request.POST.get('range2')
		Controls['range3'] = request.POST.get('range3')
		Controls['EL'] = request.POST.get('EL')
		Controls['RM'] = request.POST.get('RM')
	print('Controls are:::::::', Controls)
	

	if request.method == 'POST' and 'document' in request.FILES: ######### file has been uploaded to server
		actiontype = request.POST.get('action')
		uploaded_file = request.FILES['document'] 
		path = 'media/' + uploaded_file.name
		DBFILE = "media/sample_7MB_7.csv"
		#print('reqpost', request.POST, request.FILES);

		if actiontype == "Mobility Trace":
			map_mode = "covid19trace"
			data_present = True

			fs = FileSystemStorage()
			fs.save(uploaded_file.name, uploaded_file)
			file_name = path

			try:
				max_frequency, midlat, midlon, json_count_traj = file_upload_covid(file_name, DBFILE)
			except Exception:
				print("inside file exception")
				os.remove(file_name)
				return render(request=request, template_name=template_name, context={'file_name':None, 
		'data_present':False, 'map_mode':"", 'inputinfo':inputinfo, 'valid_input':valid_input, 'Controls':Controls})

			#delete file
			os.remove(file_name)

			context = {'inputinfo':inputinfo, 'data_present':data_present, 'count_traj':json_count_traj,\
			 'max_frequency': max_frequency, 'map_mode':map_mode, 'midlat':midlat, 'midlon':midlon, \
			 'file_name':uploaded_file.name, 'valid_input':valid_input, 'Controls':Controls}

			return render(request=request, template_name=template_name, context=context)



		elif actiontype == "Contact Tracing":
			map_mode = "contact tracing"
			data_present = True 

			fs = FileSystemStorage()
			fs.save(uploaded_file.name, uploaded_file)
			file_name = path

			try:
				max_frequency, midlat, midlon, json_count_traj, json_input_uids = file_upload_ctt(file_name, DBFILE)
			except Exception:
				print('inside file ct exception')
				os.remove(file_name)
				return render(request=request, template_name=template_name, context={'file_name':None, 
		'data_present':False, 'map_mode':"", 'inputinfo':inputinfo, 'valid_input':valid_input, 'Controls':Controls})


			#delete file
			os.remove(file_name)

			context = {'inputinfo':inputinfo, 'data_present':data_present, 'count_traj':json_count_traj,\
			 'max_frequency': max_frequency, 'map_mode':map_mode, 'midlat':midlat, 'midlon':midlon, \
			 'file_name':uploaded_file.name, 'input_uids':json_input_uids, 'valid_input':valid_input, 'Controls':Controls}

			return render(request=request, template_name=template_name, context=context)







	elif request.method == 'POST': ######## mobile no has been entered by user
		mobileno = request.POST.get('mobileno')
		actiontype = request.POST.get('action')
		geo = GeoNames(username='sifat578')
		DBFILE = "media/sample_7MB_7.csv"
		print('reqpost:', request.POST, '-----------------', request);

		if mobileno.isnumeric() == False:
			input_uid = mobileno
			inputinfo = input_uid
			all_uids = []
			file = open('media/MobileNoMap.txt','r')
			for line in file:
				all_uids.append((line.split(',')[1]).rstrip())
			file.close()

		else:
			all_mappings = []
			all_uids = []
			file = open('media/MobileNoMap.txt','r')
			for line in file:
				all_mappings.append(line)
				all_uids.append((line.split(',')[1]).rstrip())
			file.close()

			# just for the sake of testing right now
			#mobileno = map_dummy_to_mobile(mobileno)
			input_uid = ""
			for line in all_mappings:
				tempmob = line.split(',')[0]
				tempuid = (line.split(',')[1]).rstrip()
				if tempmob == mobileno:
					input_uid = tempuid
					break
					#print('UID is ', tempuid)
			if input_uid != "":
				inputinfo = input_uid
			else:
				inputinfo = mobileno 

		
		if len(mobileno)==0 or input_uid not in all_uids:
			valid_input = False
			return render(request=request, template_name=template_name, context={'file_name':None, 
		'data_present':False, 'map_mode':"", 'inputinfo':inputinfo, 'valid_input':valid_input, 'Controls':Controls})


		print('INPUTUID', input_uid)
		if actiontype == "Mobility Trace":
			dict = {}
			data_present = True
			map_mode = "covid19trace"
			latest_date = date(1900,1,1)
			with open(DBFILE, "r+") as f:
				csvreader = csv.reader(f)
				for row in csvreader:
					uid, date1, time_str, dummy, lat, lon = row
					if input_uid != uid:
						continue
					temp, y, m, d = generate_date(date1)
					if (latest_date - temp).days < 0:
						latest_date = latest_date.replace(year=y, month=m, day=d)
						#print('latest_date' , latest_date)
					
			with open(DBFILE, "r+") as f:
				csvreader = csv.reader(f)
				#limit=100
				for row1 in csvreader:
					uid, date1, time_str, dummy, lat, lon = row1
					temp, y, m, d = generate_date(date1)

					if (latest_date-temp).days > 14:
						continue

					if input_uid == uid:
						if uid not in dict:
							dict[uid] = []
						dict[uid].append((date1, time_str, dummy, lat, lon))

			#sort according to time
			for uid, points in dict.items():
				points.sort(key=lambda x: (x[0], x[1]))

			traj = dict[input_uid]
			for i in range(len(traj) - 1):
				date_0 = traj[i][0]
				date_1 = traj[i+1][0]

				time_0 = traj[i][1]
				time_1 = traj[i+1][1]

				#gives a single integer of date+time
				ts_0 = time.mktime(datetime.strptime(f"{date_0} {time_0}", "%Y%m%d %H:%M:%S").timetuple())
				ts_1 = time.mktime(datetime.strptime(f"{date_1} {time_1}", "%Y%m%d %H:%M:%S").timetuple())

				traj[i] = traj[i] + (ts_1 - ts_0, ) #time spent added to traj

			traj[-1] = traj[-1] + (time.mktime(datetime.strptime(f"{traj[-1][0]} 23:59:59", "%Y%m%d %H:%M:%S").timetuple())\
				- time.mktime(datetime.strptime(f"{traj[-1][0]} {traj[-1][1]}", "%Y%m%d %H:%M:%S").timetuple()), )


			#calculate frequency traj(date, time_str, dummy, lat, lon, time spent)
			#alllatlons = [[float(i[3]),float(i[4])] for i in traj]
			temp1 = [[(i[3],i[4])] for i in traj]
			count_traj = Counter(chain(*temp1))
			count_traj_list = []
			for key, val in count_traj:
				if [float(key),float(val)] not in alllatlons:
					alllatlons.append([float(key),float(val)])
			  
				count_traj_list.append((float(key), float(val), count_traj[key,val]))
				if count_traj[key,val] > max_frequency:
					max_frequency = count_traj[key,val]

			#find total times spent in separate locations
			for tup in traj:
				if (tup[3],tup[4]) not in collective_time:
					collective_time[(tup[3],tup[4])] = 0
				collective_time[(tup[3],tup[4])] += tup[5]


			#read all reverse geocodes
			all_geocodes = {}
			file = open('media/reverse_geocodes_7MB_6.txt','r')
			for line in file:
				temp = line.split(',')
				all_geocodes[(temp[0], temp[1])] = temp[2].rstrip()

			file.close()


			cnt = 0
			table_data = {}
			for key, val in count_traj:
				temp2 = collective_time[(key, val)]/3600 #stores time in hours
				temp2 = round(temp2,1)
				temp3 = time_to_radius(temp2)
				temp4 = str(temp2)
				# collective_time_list.append((float(key), float(val), temp3)) #lat, lon, radius
				count_traj_list[cnt] = count_traj_list[cnt] + (temp3, temp4) #lat,lon,freq,rad,total time spent
				#get location names 
				if (key,val) in all_geocodes:
					loc_name = all_geocodes[(key,val)]
				else:
					loc_name = str(geo.reverse(query=(key, val), exactly_one=False,timeout=5)[0])
					loc_name = loc_name.split(",")[0]
				
				opacity = get_opacity(count_traj_list[cnt][2])
				count_traj_list[cnt] = count_traj_list[cnt] + (loc_name, opacity) #lat,lon,freq,rad,total time spent,locname, opacity
				if loc_name not in table_data:
					table_data[loc_name] = [0,0]
				table_data[loc_name][0] += temp2
				table_data[loc_name][1] += float(count_traj_list[cnt][2])
				cnt += 1
				

			json_count_traj = json.dumps(count_traj_list)
			midlat, midlon = find_center(alllatlons)

			table_data_dump = []
			for key,val in table_data.items():
				table_data_dump.append((key,val[0],val[1])) #location, time spent, freq
			#save file in json for datatable read
			save_json_mobility(table_data_dump)

			context = {'inputinfo':inputinfo, 'data_present':data_present, 'count_traj':json_count_traj,\
			 'max_frequency': max_frequency, 'map_mode':map_mode, 'midlat':midlat, 'midlon':midlon,\
			 'file_name':file_name, 'valid_input':valid_input, 'Controls':Controls}

			return render(request=request, template_name=template_name, context=context)





		elif actiontype == "Contact Tracing":
			map_mode = "contact tracing"
			data_present = True
			max_frequency, midlat, midlon, json_count_traj = contact_tracing_single(input_uid, DBFILE)

			context = {'inputinfo':inputinfo, 'data_present':data_present, 'count_traj':json_count_traj,\
			 'max_frequency': max_frequency, 'map_mode':map_mode, 'midlat':midlat, 'midlon':midlon,\
			 'file_name':file_name, 'input_uid': input_uid, 'valid_input':valid_input, 'Controls':Controls}

			return render(request=request, template_name=template_name, context=context)




	return render(request=request, template_name=template_name, context={'file_name':None, 
		'data_present':False, 'map_mode':"", 'inputinfo':inputinfo, 'valid_input':valid_input, 'Controls':Controls})



#######################################################################################################
#######################################################################################################
#######################################################################################################





def HeatMap(request):
	context = {} 
	limit = 500
	latest_date = date(1900,1,1)
	alllatlons = []
	alllatlons_withrepeat = []
	dict = {}
	geo = GeoNames(username='sifat577')
	DBFILE = "media/sample_7MB_7.csv"

	with open(DBFILE, "r+") as f:
		csvreader = csv.reader(f)
		for row in csvreader:
			uid, date1, time_str, dummy, lat, lon = row
			temp, y, m, d = generate_date(date1)
			if (latest_date - temp).days < 0:
				latest_date = latest_date.replace(year=y, month=m, day=d)

			# limit -= 1
			# if limit == 0:
			# 	break
	
	limit = 500
	with open(DBFILE, "r+") as f:
		csvreader = csv.reader(f)
		for row1 in csvreader:
			uid, date1, time_str, dummy, lat, lon = row1
			temp, y, m, d = generate_date(date1)
			if (latest_date-temp).days > 14:
				continue

			#alllatlons_withrepeat.append([float(lat),float(lon)])

			if [float(lat), float(lon)] not in alllatlons:
				alllatlons.append([float(lat),float(lon)])
			if uid not in dict:
				dict[uid] = []
			dict[uid].append((lat,lon))

			# limit -= 1
			# if limit == 0:
			# 	break

	#have to calculate center point of the coordinates
	midlat, midlon = find_center(alllatlons)
	print('midpoints are ', midlat, midlon)

	# save_alllatlons(alllatlons_withrepeat)

	# context = {'midlat':midlat, "midlon":midlon}

	# return render(request=request, template_name="main/heatmap.html", context=context)


	
	#read all reverse geocodes
	all_geocodes = {}
	file = open('media/reverse_geocodes_7MB_6.txt','r')
	for line in file:
		temp = line.split(',')
		all_geocodes[(temp[0], temp[1])] = temp[2].rstrip()

	file.close()


	temp_cnt = 0
	location_dict = {}
	for uid, points in dict.items():
		for point in points:
			lat,lon = point
			temp_cnt += 1
			if (lat,lon) in all_geocodes:
				loc_name = all_geocodes[(lat,lon)]
			else:
				loc_name = str(geo.reverse(query=(lat,lon), exactly_one=False,timeout=5)[0])
				loc_name = loc_name.split(',')[0]
			
			#print(uid, loc_name)
			if loc_name not in location_dict:
				location_dict[loc_name] = {}
			if uid not in location_dict[loc_name]:
				location_dict[loc_name][uid] = 1
			else:
				location_dict[loc_name][uid] += 1

	print('GEO reversed ', temp_cnt, ' times')
	#getting all locations of BD
	BDfile = "media/BD.txt"
	file = open(BDfile, 'r')
	BDlocs = []
	for line in file:
		parts = line.split("\t")
		BDlocs.append(parts)
	file.close()
 

	min_freq = 10**10
	max_freq = 0
	heatmap_data = []
	for loc_name, info in location_dict.items():
		no_of_uids = len(location_dict[loc_name].keys()) 
		sum_freq = 0
		for uid, freq in location_dict[loc_name].items():
			sum_freq += freq 

		if sum_freq > max_freq:
			max_freq = sum_freq
		if sum_freq < min_freq:
			min_freq = sum_freq

		# points = geo.geocode(query=loc_name, exactly_one=False, timeout=5)
		# lat = points[0][1][0]
		# lon = points[0][1][1]
		lat = ""
		lon = ""
		for ibd in range(len(BDlocs)):
			if BDlocs[ibd][1] == loc_name:
				lat = BDlocs[ibd][4]
				lon = BDlocs[ibd][5]
				break
		
		if lat!="" and lon!="":
			alllatlons_withrepeat += [[float(lat),float(lon)]]*sum_freq
		#heatmap_data.append((lat,lon,no_of_uids,sum_freq))

	save_alllatlons(alllatlons_withrepeat)

	context = {'midlat':midlat, "midlon":midlon}

	return render(request=request, template_name="main/heatmap.html", context=context)

 



def Guide(request):

	return render(request=request, template_name="main/guide.html")













