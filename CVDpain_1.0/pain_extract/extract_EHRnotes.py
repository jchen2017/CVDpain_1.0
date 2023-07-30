# coding=utf-8
#
# Released under MIT License
#
# Copyright (c) 2021, Jinying Chen
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

# -*- mode: Python; indent-tabs-mode: t; tab-width: 4 -*-
# vim: noet:ci:pi:sts=0:sw=4:ts=4

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os
import MySQLdb
import re
import string
import datetime

output_dir="/home/jinying/projects/CVDpain/Aim1_data/ehr_notes/"
noteinfo_file="/home/jinying/projects/CVDpain/Aim1_data/ehr_notes_info.txt"

notetype_dict={
"Discharge Summary": "ds",
"Patient Instructions": "pi",
"H&P": "hp",
"Telephone Encounter": "te",
"Clinic Note": "cn",
"Progress Notes": "pn",
"Nursing Note": "nn"    
}

def extract_aim1_notes ():
	""" extract record information from ade_annotation DB """

	# connnect to mysql DB
	db = MySQLdb.connect(host="localhost",  # your host, usually localhost
                      user="xxx",  # your username
                      passwd="xxx",  # your password
                      db="EHRnotes") # the database

	cur=db.cursor()
	
	# extract information from the EHR notes table
	rows = cur.execute("select * from RecordID213_Note")
	if rows:
		record_dict={}
		length_dict={}
		record_info_dict={}

		total_records=0
		data=cur.fetchall()  # This returns all the rows from the database as a list of tuples.
		
		for (mrn,admin_dt,note_date,dischg_dt,dischg30_dt, noteid, line_id, content, note_type) in data:
			date_note=note_date
			date_dischg=dischg_dt

			noteid="%s_%s"%(mrn,noteid)	
			try:
				record_dict[noteid][line_id]={}	
			except:
				record_dict[noteid]={}
				record_dict[noteid][line_id]={}
			
			note_len=len(content)	
			record_dict[noteid][line_id]['length']=note_len
			record_dict[noteid][line_id]['text']=content
			record_dict[noteid][line_id]['note_type']=notetype_dict[note_type]

			if not noteid in record_info_dict:
				record_info_dict[noteid]={}
				record_info_dict[noteid]['note_type'] = note_type
				record_info_dict[noteid]['date_note'] = date_note
				record_info_dict[noteid]['date_dischg'] = date_dischg
				record_info_dict[noteid]['admin_date']=admin_dt


			postdis_notes=0
			if date_note > date_dischg:
				postdis_notes=1	
			record_dict[noteid][line_id]['timing']=postdis_notes

	
			if note_len == 1950:
				print (noteid, line_id)	
				print (content)
				print ("==========================================\n")
				
			if not note_len in length_dict:
				length_dict[note_len]=1
			else:
				length_dict[note_len]+=1
	
			total_records+=1
			
	print ("total %d records"%(total_records))


	fout2=open(noteinfo_file,"w")
	fout2.write("file_name\tnote_type\tnote_date\thospitalization_date\tdischarge_date\n")
	for noteid in record_dict.keys():
		file_name="%s_%d_%s"%(record_dict[noteid][1]["note_type"], record_dict[noteid][1]["timing"], noteid)
		outfile=output_dir+"%s.txt"%(file_name)
		fout=open(outfile, "w")
		fout.write("noteid: %s\n"%(noteid))
		for line_id in sorted(record_dict[noteid].keys()):
			fout.write(record_dict[noteid][line_id]['text'])
            
		fout.close()

		fout2.write("%s\t%s\t%s\t%s\t%s\n"%(file_name, record_info_dict[noteid]['note_type'], record_info_dict[noteid]['date_note'], record_info_dict[noteid]['admin_date'], record_info_dict[noteid]['date_dischg']))

	fout2.close()			

	length_dict_sorted=sorted(length_dict.items(), key=lambda x: x[1], reverse=True)			
	for (note_len, freq) in length_dict_sorted:
		print (note_len, freq)
	
	sorted_length=sorted(length_dict.keys())
	print("max length: %d, min length: %d"%(sorted_length[-1], sorted_length[0]))

	if db:
		db.close()
	

if '__main__' == __name__:
	extract_aim1_notes ()
