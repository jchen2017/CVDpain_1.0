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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

#
# utility functions for analyzing pain extraction methods
#

import os
from os import listdir
from os.path import isfile, join
import datetime
import random

import sys, getopt
import re
import string

from month_abbrev import get_month_numeric
from trie import Trie
from nltk.stem.snowball import EnglishStemmer
from nltk import word_tokenize, sent_tokenize, pos_tag

head_info=["file name", "note type", "note was written on", "hospitalization date", "discharge date", "associated admission date"]


traceCore_id_mapping="/home/jinying/projects/CVDpain/Aim1_data/TraceCore_id_mapping.csv"
noteinfo_file="/home/jinying/projects/CVDpain/Aim1_data/ehr_notes_info_rf.txt"
pain_keywords="/home/jinying/projects/CVDpain/Aim1_NLP/keyword_pain_list1.txt"
pain_loc_file="/home/jinying/projects/CVDpain/Aim1_NLP/pain_location_mapping.txt"
ann_template_dir="/home/jinying/projects/CVDpain/Aim1_data/annotation_in/"
deid_info_file="/home/jinying/projects/CVDpain/Aim1_data/deid_info/filter_summary.txt"


stemmer=EnglishStemmer()

def import_id_map():
    id_map={}
    fin=open(traceCore_id_mapping)
    line=fin.readline()
    for line in fin.readlines():
        (patid,mrn,rehosp30,rehosp30date,rehosp30_sched)=line.strip().split(",")
        mrn=int(mrn)
        id_map["%s"%(mrn)]=(patid, "", rehosp30, rehosp30_sched)
        if rehosp30date != "":
            (d,m,y)=re.search(r"^(\d+)([a-z]+)(\d+)$", rehosp30date).groups()
            rehosp30date="%s-%s-%s"%(y,get_month_numeric(m),d)
            id_map["%s"%(mrn)]=(patid, datetime.datetime.strptime(rehosp30date, '%Y-%m-%d'), rehosp30, rehosp30_sched)

    return id_map


def import_pain_loc_map():
    pain_loc_map={}
    fin=open(pain_loc_file)
    for line in fin.readlines():
       
        (t,l)=line.strip().split("\t")
        pain_loc_map[t]=l

    return pain_loc_map


def import_deid_info():
    deid_info={}
    fin=open(deid_info_file)
    for line in fin.readlines():
        if re.search("\d+", line):
            info=line.split(" ")
            deid_info[info[0]]=info[2:]
    return deid_info

def import_keywords():
    pain_words=[]

    with open(pain_keywords, encoding='utf-8') as fin:
        line = fin.readline()
        while line != None:
            if re.search("^#Category 1:", line):
                line=fin.readline()
                while not re.search("^#Category 2:", line):
                    kword=line.strip()
                    if not (re.search("^\#",kword) or re.search("^\s*$",kword)):
                        pain_words.append(line.strip().lower())
                    line=fin.readline()

                break
            else:
                line=fin.readline()

    print(pain_words)
    return(pain_words)

pain_loc_map=import_pain_loc_map()
def compare_loc_ann(loc_gold,loc_ann):
    if loc_gold == loc_ann:
        return 1.0

    cor_loc=0
    loc_gold_set={}

    for loc in loc_gold.split(","):
        loc=re.sub("^ *","",loc)
        loc=re.sub(" *$","",loc)
        if re.search(r"[a-z]", loc):
            if loc == "right upper quadrant":
                loc = "ruq"
            loc=re.sub(r"(left *)|(upper *)|(right *)", "", loc)
            if re.search("(neck)|(arm)|(leg)|(muscle)|(shoulder)|(knee)|(migraine)|(abdomen)", loc):
                loc=re.search("((neck)|(arm)|(leg)|(muscle)|(shoulder)|(knee)|(migraine)|abdomen)", loc).group(1)

            if re.search(r"(everywhere)|(implied)|(incision)|(all)|(not specified)|(surgical)", loc):
                loc='unk'

            try:
                loc=pain_loc_map[loc]
            except:
                pass

            loc_ls=loc.split("|")
            for loc in loc_ls:
                loc_gold_set[stemmer.stem(loc)]=1

    if len(loc_gold_set.keys())>1 and 'unk' in loc_gold_set:
        del loc_gold_set['unk']

    loc_ann_set={}
    for loc in loc_ann.split("|"):
        loc=re.sub("^ *","",loc)
        loc=re.sub(" *$","",loc)

        if re.search(r"[a-z]", loc):
            if loc == "right upper quadrant":
                loc = "ruq"

            loc=re.sub(r"(left )|(upper )|(right *)", "", loc)
            if re.search("(neck)|(arm)|(leg)|(muscle)|(shoulder)|(knee)|(migraine)|(abdomen)", loc):
                loc=re.search("((neck)|(arm)|(leg)|(muscle)|(shoulder)|(knee)|(migraine)|abdomen)", loc).group(1)

            try:
                loc=pain_loc_map[loc]
            except:
                pass

            loc_ls=loc.split("|")
            for loc in loc_ls:
                loc_ann_set[stemmer.stem(loc)]=1

    if len(loc_ann_set.keys())>1 and 'unk' in loc_ann_set:
        del loc_ann_set['unk']
        
    print("pain location (NLP) ", loc_ann_set.keys(), " vs. (gold) ", loc_gold_set.keys())

    loc_com={}
    for loc in loc_ann_set:
        if loc in loc_gold_set:
            loc_com[loc]=1

    cor_loc_rate=2*len(loc_com.keys())/(len(loc_ann_set.keys())+len(loc_gold_set.keys()))

    if "chest" in loc_com:
        cor_loc_rate=1.0

    return cor_loc_rate

def trie_regex_from_words(words):
    trie = Trie()
    for word in words:
        trie.add(word)
    pattern1=trie.pattern()
    print(pattern1)
    return re.compile(r"\b" + pattern1 + r"\b", re.IGNORECASE)

def load_note_info():
    record_info_dict={}
    fin=open(noteinfo_file, 'r')
    for line in fin.readlines():        
        fileinfo=line.strip().split("\t")
        
        record_info_dict[fileinfo[0]]=fileinfo
    return record_info_dict

def load_ann (file_list):
    annotation={}
    for infile in file_list:
        print(infile)
        fin=open(infile)
        line=fin.readline()
        while not re.search("^file name:", line):
            line=fin.readline()

        filename=re.search(r"file name: *([^ ]+)$", line.strip()).group(1)
        annotation[filename]={}
        annotation[filename]['fullname']=infile
        annotation[filename]['ann']={}
        annotation_2=annotation[filename]['ann']

        line=fin.readline()
        while not re.search("^=================", line):
            line=fin.readline()

        sid=None
        label=None
        timing=None
        lines=fin.readlines()
        i=0
        while i <  len(lines):
            line=lines[i]
            i+=1

            if re.search(r"^([0-9]+): *(.*)$", line):
                (sentid, sent)=re.search(r"^([0-9]+): *(.*)$", line).groups()
                sid=int(sentid)
                if not sid in annotation_2:
                    annotation_2[sid]={}
                annotation_2[sid]['sent']=sent
                label=0
                timing=None
                severity=None
                location=None
                position=None
                terms=None
                comment=""

            elif re.search(r"^#reported pain", line):
                if re.search(r"^#.*: *([yY])", line):
                    label=1
                    annotation_2[sid]['hasPain']=label

                    if re.search(r"^#.*: *[yY]\[", line):
                        (sid1,sid2)=re.search(r"^#.*: *[yY]\[([0-9]+),([0-9]+)\]", line).groups()
                        sid1=int(sid1)
                        sid2=int(sid2)
                        if sid2 - sid1 > 1:
                            print("warning-util-2: pain annotation cross more than two sentences (%s-%s)"%(sid1,sid2))
                            exit(0)

                        if sid2 == sid:
                            annotation_2[sid2]['crossSB_up']=sid1
                            annotation_2[sid2]['crossSB_down']=-1
                            if annotation_2[sid1]['hasPain'] == 0:
                                annotation_2[sid1]['hasPain']=1
                            annotation_2[sid1]['crossSB_down']=sid2
                        elif sid1 == sid:
                            annotation_2[sid1]['crossSB_down']=sid2
                            annotation_2[sid1]['crossSB_up']=-1
                            annotation_2[sid2]={}
                            annotation_2[sid2]['hasPain']=label
                            annotation_2[sid2]['crossSB_up']=sid1
                            annotation_2[sid2]['crossSB_down']=-1
                    else:
                        if not 'crossSB_up' in annotation_2[sid]:
                            annotation_2[sid]['crossSB_up']=-1
                        if not 'crossSB_down' in annotation_2[sid]:
                            annotation_2[sid]['crossSB_down']=-1
                        
                    line=lines[i]
                    i+=1
                    # timing of pain
                    if re.search(r"^#timing of pain.*: *([yY])", line):
                        timing="pd"   #pd: post-discharge pain
                    elif re.search(r"^#timing of pain.*: *([nN])", line):
                        timing="bd"   #bd: before-discharge pain
                    else:
                        print("warning-util-1: missing timing of pain for %s, sent %s, %s"%(filename, sid, line))
                     

                    annotation_2[sid]['timing']=timing

                    line=lines[i]
                    i+=1
                    #severity(1:not severe, 2:severe):
                    if re.search(r"^#severity.*: *([0-9]+)", line):
                        severity=re.search(r"^#severity.*: *([0-9]+)", line).group(1)
                    else:
                        print("warning-util-1: missing severity of pain for %s, sent %s"%(filename, sid))
                        severity=-1
                      
                    annotation_2[sid]['severity']=severity

                    line=lines[i].strip()
                    i+=1
                    #location:
                    if re.search(r"^#location: *[^ ]+", line):
                        location=re.search(r"^#location: *([^ ]+.*)", line).group(1).lower()
                    else:
                        print("warning-util-1: missing location of pain for %s, sent %s"%(filename, sid))
                     
                    annotation_2[sid]['loc']=location

                    line=lines[i]
                    i+=1
                    #comments:
                    annotation_2[sid]['inf']=0
                    if re.search(r"^#comments:", line):
                        comment=re.search(r"^#comments: *([^ ]+.*)$", line).group(1)
                        annotation_2[sid]['comment']=comment
                        if re.search(r"2", comment) or re.search(r"this refers to pain", comment):
                            annotation_2[sid]['inf']=1

                    if re.search(r"^#term positions:", lines[i]):
                        line=lines[i].strip()
                        i+=1
                        positions=re.search(r"^#term positions: *([^ ]+.*)$", line).group(1)
                        annotation_2[sid]['positions']=positions

                        line=lines[i].strip()
                        i+=1
                        terms=re.search(r"^#terms: *([^ ]+.*)$", line).group(1)
                        annotation_2[sid]['terms']=terms
                        
                else:
                    if not 'hasPain' in annotation_2[sid]:
                        annotation_2[sid]['hasPain']=label
                    i+=4

    return annotation

def find_pain_from_ann (fin):
    mention_pain=0
    pain_loc=set()
    lines = fin.readlines()
    pre_sent=None
    sent=None
    sidx=None
    i = 1
    while i < len(lines):
        line=lines[i]
        if re.search(r"^[0-9]+: *", line):
            (sidx, sent_orig)=re.search(r"^([0-9]+): *(.*)$", line).groups()
            sidx=int(sidx)
            preline=sent_orig.lower()
            sent=preline


        line=line.lower()
        if re.search(r"reported pain.*: *[Yy]", line):
            location=lines[i+3].lower()
            

            k=i
            while not re.search(r"positions:", lines[k]):
                k+=1

            pos_str=re.search(r"positions: *([^ ]+)", lines[k]).group(1)
            pos_ls=pos_str.split(",")
            terms=re.search(r"terms:(.*)$", lines[k+1]).group(1)
            tls=terms.split("|")
                            
            
            pain_loc2 = re.search(r"location:(.*)", location).group(1)
            pls=pain_loc2.split("|")
            

            tidx=0
            for pos_str in pos_ls:
                term=tls[tidx]
                if not "-" in pos_str:
                    (t_st, t_end)=re.search(r"\((\d+):(\d+)\)", pos_str).groups()
                    t_st=int(t_st)
                    t_end=int(t_end)
                    # check term & position match
                    term2=sent_orig[t_st:t_end]
                    if term2 != term:
                        if re.search(r"pain", term2.lower()):
                            print("warning-3.2: partial match (%s) vs. (%s)"%(term2, term))

                        else:
                            print("warning-3.1: mismatch (%s) vs. (%s)"%(term2, term))

                        
                    sent_lh=sent[0:t_st]
                    sent_lh_r=re.sub(r"^.*   ","",sent_lh)
                    sent_lh_r=re.sub(r"^.*(but)|(however) ", "", sent_lh)
                    
                else:
                    (t_st, t_end, t2_st)=re.search(r"\((\d+):([\-0-9]+)\)\-\((\d+):\)", pos_str).groups()
                    t_st=int(t_st)
                    t_end=int(t_end)
                    t2_st=int(t2_st)
                    # check term & position match
                    term2=sent_orig[t_st:t_end]
                    if not term2 in term:
                        print("warning-3.3: mismatch (%s) vs. (%s)"%(term2, term))
                     

                    sent_lh=pre_sent[0:t2_st]
                    sent_lh_r=re.sub(r"^.*   ","",sent_lh)
                    sent_lh_r=re.sub(r"^.*(but)|(however) ", "", sent_lh)
                    
                if re.search(r"c\/o ", sent_lh_r):
                    (p1, p2, p3) = re.search(r"^(.*)(c\/o )(.*)$", sent_lh_r).groups()
                    if re.search(r".*no $", p1):
                        sent_lh_r="no "+p2+p3
                    else:
                        sent_lh_r=p3
                        
                sent_rh=sent[t_end:]

                negation=0
                if re.search(r"(^| )((did not report)|(decline)|(deny)|(denie[sd])|(no)|(not having)|(negative for)) [-:]*[a-z,\- \/]*$", sent_lh_r.lower()) or re.search("(^| )(free)", sent_rh.lower()):
                    negation = 1

                
                if re.search(r"(^| )(if [^ ]+ ((has)|(have)|(develops?))) [-:]*[a-z,\- \/]*$", sent_lh_r.lower()):
                    negation = 1
                    
                if negation == 1:
                    print("warning-util-3: detected negation for %s. %s: %s [[%s]] %s"%(sidx, sent[t_st:t_end], sent_lh, sent[t_st:t_end], sent_rh.lower()))
                    
                else:
                    print("warning-util-4: detected pain for %s. %s: %s [[%s]] %s"%(sidx, sent[t_st:t_end], sent_lh, sent[t_st:t_end], sent_rh.lower()))
                    mention_pain=1
                    pl = pls[tidx]

                    if not pl in ['unk', 'ache', 'pain']:
                        pain_loc.add(pl)
                
                tidx+=1
                
        pre_sent=sent
        i+=1

    return(mention_pain, '|'.join(sorted(pain_loc)))

def find_pat_history_v3 (lines):
    history_dict={}
    inHistory=0
    #0: non-history
    #1: history by section title
    for line in lines:
        if re.search(r"^[0-9]+: *", line):
            (sidx, sent_orig)=re.search(r"^([0-9]+): *(.*)$", line).groups()
            sidx=int(sidx)
            sent=sent_orig.lower()
            history_dict[sidx]={}
            history_dict[sidx]["sent"]=sent_orig

            #check tense
            tokens = word_tokenize(sent_orig)
            postags = pos_tag(tokens)
            pasttense=0
            
            for (tok,pos) in postags:
                if re.search(r"^V", pos):
                    if pos == "VBD":
                        pasttense=1
            

            if inHistory == 0:
                if re.search(r"(history of present)|(interim history)|(past medical)", sent):
                    inHistory = 1
                elif pasttense == 1:
                    inHistory = 2
                elif re.search(r"(followup)|(hospitalization)|(admission)", sent):
                    inHistory = 3
            else:
                if not re.search(r"(history of present|(interim history)|(past medical))", sent):
                    sent2=re.sub(r"PHI_[^ ]+", "", sent_orig)
                    if re.search(r"[A-Z]{6}", sent2):
                        inHistory = 10 # section after patient history

            history_dict[sidx]["history"]=inHistory

    
    return history_dict
                                                                                
def find_pat_history_v1 (lines):
    history_dict={}
    inHistory=0
    #0: non-history
    #1: history by section title
    for line in lines:
        if re.search(r"^[0-9]+: *", line):
            (sidx, sent_orig)=re.search(r"^([0-9]+): *(.*)$", line).groups()
            sidx=int(sidx)
            sent=sent_orig.lower()
            history_dict[sidx]={}
            history_dict[sidx]["sent"]=sent_orig

            #check tense
            tokens = word_tokenize(sent_orig)
            postags = pos_tag(tokens)
            pasttense=0
            
            for (tok,pos) in postags:
                if re.search(r"^V", pos):
                    if pos == "VBD":
                        pasttense=1
            
                    
            if inHistory == 0 :
                if re.search(r"(history of present)|(interim history)", sent):
                    inHistory = 1
            
            else:
                sent2=re.sub(r"PHI_[^ ]+", "", sent_orig)
                if re.search(r"[A-Z]{6}", sent2):
                    inHistory = 10 # section after patient history
            history_dict[sidx]["history"]=inHistory


    return history_dict

def find_pat_history_v2 (lines):
    history_dict={}
    inHistory=0
    #0: pre-history
    #1: history by section title
    #2: history by tense
    #3: history by cure words
    #10: after history
    #20: non-history by tense (within history section)
    for line in lines:
        if re.search(r"^[0-9]+: *", line):
            (sidx, sent_orig)=re.search(r"^([0-9]+): *(.*)$", line).groups()
            sidx=int(sidx)
            sent=sent_orig.lower()
            history_dict[sidx]={}
            history_dict[sidx]["sent"]=sent_orig

            #check tense
            tokens = word_tokenize(sent_orig)
            postags = pos_tag(tokens)
            pasttense=0
            
            for (tok,pos) in postags:
                if re.search(r"^V", pos):
                    if pos == "VBD":
                        pasttense=1
            

            if re.search(r"(history of present)|(interim history)", sent): 
                inHistory = 1
            elif inHistory != 10:
                if inHistory > 0:
                    sent2=re.sub(r"PHI_[^ ]+", "", sent_orig)
                    if re.search(r"[A-Z]{6}", sent2):
                        inHistory = 10 # section after patient history
                
                if inHistory >0 and inHistory < 10:
                    if pasttense == 0:
                        inHistory = 20 # current disease in history section
                elif inHistory != 10:
                    if pasttense == 1:
                        inHistory = 2
                    elif re.search(r"(followup)|(hospitalization)|(admission)", sent):
                        inHistory = 3
            
            history_dict[sidx]["history"]=inHistory

            
    return history_dict


def find_pain_from_ann_v2(fin, note_type):
    mention_pain=0
    pain_loc=set()
    lines = fin.readlines()

    history_dict=find_pat_history_v3 (lines)
    
    pre_sent=None
    
    i = 1
    while i < len(lines):
        line=lines[i]
        if re.search(r"^[0-9]+: *", line):
            (sidx, sent_orig)=re.search(r"^([0-9]+): *(.*)$", line).groups()
            sidx=int(sidx)
            sent=sent_orig.lower()
            if sidx > 1:
                pre_sent= history_dict[sidx-1]["sent"]

            if history_dict[sidx]["history"] > 0 and history_dict[sidx]["history"] <10:
                i+=3
                continue
        
        line=line.lower()
        if re.search(r"reported pain.*: *[Yy]", line):
            location=lines[i+3].lower()
            

            k=i
            while not re.search(r"positions:", lines[k]):
                k+=1

            pos_str=re.search(r"positions: *([^ ]+)", lines[k]).group(1)
            pos_ls=pos_str.split(",")
            terms=re.search(r"terms:(.*)$", lines[k+1]).group(1)
            tls=terms.split("|")
                        
            pain_loc2 = re.search(r"location:(.*)", location).group(1)
            pls=pain_loc2.split("|")

            
            tidx=0
            for pos_str in pos_ls:
                term=tls[tidx]
                if not "-" in pos_str:
                    (t_st, t_end)=re.search(r"\((\d+):(\d+)\)", pos_str).groups()
                    t_st=int(t_st)
                    t_end=int(t_end)
                    # check term & position match
                    term2=sent_orig[t_st:t_end]
                    if term2 != term:
                        if re.search(r"pain", term2.lower()):
                            print("warning-3.2: partial match (%s) vs. (%s)"%(term2, term))
                            ##loc="unk"
                        else:
                            print("warning-3.1: mismatch (%s) vs. (%s)"%(term2, term))
                            ##continue

                    sent_lh=sent[0:t_st]
                    sent_lh_r=re.sub(r"^.*   ","",sent_lh)
                    sent_lh_r=re.sub(r"^.*(but)|(however) ", "", sent_lh)

                else:
                    (t_st, t_end, t2_st)=re.search(r"\((\d+):([\-0-9]+)\)\-\((\d+):\)", pos_str).groups()
                    t_st=int(t_st)
                    t_end=int(t_end)
                    t2_st=int(t2_st)
                    # check term & position match
                    term2=sent_orig[t_st:t_end]
                    if not term2 in term:
                        print("warning-3.3: mismatch (%s) vs. (%s)"%(term2, term))

                                            
                    sent_lh=pre_sent[0:t2_st]
                    sent_lh_r=re.sub(r"^.*   ","",sent_lh)
                    sent_lh_r=re.sub(r"^.*(but)|(however) ", "", sent_lh)
                    
                if re.search(r"c\/o ", sent_lh_r):
                    (p1, p2, p3) = re.search(r"^(.*)(c\/o )(.*)$", sent_lh_r).groups()
                    if re.search(r".*no $", p1):
                        sent_lh_r="no "+p2+p3
                    else:
                        sent_lh_r=p3
                        
                sent_rh=sent[t_end:]

                
                negation=0
                if re.search(r"(^| )((did not report)|(decline)|(deny)|(denie[sd])|(no)|(not having)|(negative for)) [-:]*[a-z,\- \/]*$", sent_lh_r.lower()) or re.search("(^| )(free)", sent_rh.lower()):
                    negation = 1


                if re.search(r"(^| )(if [^ ]+ ((has)|(have)|(develops?))) [-:]*[a-z,\- \/]*$", sent_lh_r.lower()):
                    negation = 1

                if negation == 1:
                    print("warning-util-3: detected negation for %s. %s: %s [[%s]] %s"%(sidx, sent[t_st:t_end], sent_lh, sent[t_st:t_end], sent_rh.lower()))
                    
                else:
                    print("warning-util-4: detected pain for %s. %s: %s [[%s]] %s"%(sidx, sent[t_st:t_end], sent_lh, sent[t_st:t_end], sent_rh.lower()))
                    mention_pain=1
                    pl = pls[tidx]

                    if not pl in ['unk', 'ache', 'pain']:
                        pain_loc.add(pl)
                    
                tidx+=1

        i+=1
        
    return(mention_pain, '|'.join(sorted(pain_loc)))

def summarize_pain_for_ehr_notes(opt, method, EHR_notes_dict):
    total_notes=0
    total_postnotes=0
    total_pain_notes=0
    total_noncard_pain_notes=0
    total_chest_pain_notes=0
    total_post_pain_notes=0
    total_post_noncard_pain_notes=0
    total_post_chest_pain_notes=0
    pts_with_pain={}
    pts_with_post_pain={}
    pts_with_post_noncard_pain={}
    pts_with_post_chest_pain={}
    pts_with_chest_pain={}
    pts_with_noncard_pain={}

    noteinfo_file2=re.sub(r"\.txt", "_%s_%s.txt"%(opt,methods), noteinfo_file)
    print ("write to %s"%(noteinfo_file2))
    outf=open(noteinfo_file2, "w")

    outf.write("filename\tpatid\tmrn\tdischarge date\tnote date\tnote type\tpostdischarge note\treporting pain\tlocation of pain\n")

    for mrn in EHR_notes_dict.keys():
        stop=0
        pref=""
        (patid, rehosp30date, rehosp30, rehosp30_sched)=id_map[mrn]
        date_dischg=EHR_notes_dict[mrn]['date_dischg']
        for date_note in sorted(EHR_notes_dict[mrn]['notes'].keys()):
            if rehosp30date != "" and date_note >= rehosp30date:
                if opt == "pdra":
                    stop=1
                    break
                elif opt == "pd":
                    pref="***"

            for note_type in EHR_notes_dict[mrn]['notes'][date_note].keys():
                if note_type == "pi":
                    continue

                for fname in EHR_notes_dict[mrn]['notes'][date_note][note_type].keys():
                    post_note=EHR_notes_dict[mrn]['notes'][date_note][note_type][fname]['post_note']
                    mention_pain=EHR_notes_dict[mrn]['notes'][date_note][note_type][fname]['mention_pain']
                    pain_loc=EHR_notes_dict[mrn]['notes'][date_note][note_type][fname]['pain_loc']

                    if post_note == 1:
                        total_postnotes+=1

                    if mention_pain == 1:
                        total_pain_notes+=1
                        pts_with_pain[mrn]=1

                        if re.search(r"\|", pain_loc) and  (not pain_loc in ["unk", "chest"]):
                            total_noncard_pain_notes+=1
                            pts_with_noncard_pain[mrn]=1
                            if post_note == 1:
                                total_post_noncard_pain_notes+=1
                                pts_with_post_noncard_pain[mrn]=1

                        if re.search(r"chest", pain_loc):
                            total_chest_pain_notes+=1
                            pts_with_chest_pain[mrn]=1
                            if post_note == 1:
                                total_post_chest_pain_notes+=1
                                pts_with_post_chest_pain[mrn]=1

                        if post_note == 1:
                            total_post_pain_notes+=1
                            pts_with_post_pain[mrn]=1

                    total_notes+=1

                    outf.write(pref+"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(fname, patid, mrn, date_dischg, date_note, note_type, post_note, mention_pain, pain_loc))

    outf.write("************ summary ************\n")
    outf.write("total %d notes: %d postdischg, %d pain (%d noncardiac, %d chest), %d postdischg pain (%d noncardiac, %d chest)\n"%(total_notes, total_postnotes, total_pain_notes, total_noncard_pain_notes, total_chest_pain_notes, total_post_pain_notes, total_post_noncard_pain_notes, total_post_chest_pain_notes))
    outf.write("total %d patients: %d pain (%d noncardic, %d chest), %d postdischg pain (%d noncardiac, %d chest)\n"%(len(EHR_notes_dict.keys()), len(pts_with_pain.keys()), len(pts_with_noncard_pain.keys()), len(pts_with_chest_pain.keys()), len(pts_with_post_pain.keys()), len(pts_with_post_noncard_pain.keys()), len(pts_with_post_chest_pain.keys())))
    outf.close()

    noteinfo_file3=re.sub(r"\.txt", "_%s_pat_%s.txt"%(opt,method), noteinfo_file)
    print ("write to %s"%(noteinfo_file3))
    outf=open(noteinfo_file3, "w")
    outf.write("patid\tdischarge date\tpostdischarge pain\tchest pain\tnoncardiac pain\n")
    for mrn in EHR_notes_dict:
        date_dischg=EHR_notes_dict[mrn]['date_dischg']
        (patid,rehosp30date,rehosp30,rehosp30_sched)=id_map[mrn]
        outstr="%s\t%s\t"%(patid, date_dischg)
        if mrn in pts_with_post_pain:
            outstr+="1\t"
        else:
            outstr+="0\t"

        if mrn in pts_with_post_chest_pain:
            outstr+="1\t"
        else:
            outstr+="0\t"

        if mrn in pts_with_post_noncard_pain:
            outstr+="1"
        else:
            outstr+="0"
        outf.write(outstr+"\n")

    outf.close()
