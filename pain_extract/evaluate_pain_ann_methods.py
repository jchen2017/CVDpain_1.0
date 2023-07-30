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
# evaluate output from pain extraction methods (e.g., rule-based and ctakes)
#

import os
from os import listdir
from os.path import isfile, join
import datetime
import random

import sys, getopt
import re
import string

from pain_util import *
from eval_util import *

def output_details(gold_ann, ann, sid):
    sent=gold_ann[sid]['sent']
    print(sent)

    try:
        print("crossSB up: %s"%(ann[sid]['crossSB_up']))
    except:
        pass

    try:
        print("crossSB down: %s"%(ann[sid]['crossSB_down']))
    except:
        pass

    try:
        cmt=gold_ann[sid]['comment']
        print("comment: ", cmt)
    except:
        pass


def drop_inferred_cases(ann_dict):
    for fname in ann_dict:
        ann=ann_dict[fname]['ann']
        sids=sorted(ann.keys())

        for sid in sids:
            if ann[sid]['hasPain'] == 1 and ann[sid]['inf'] == 1:
                sent=ann[sid]['sent']
                ''' method 1
                if not (kw_regex1.search(sent) or kw_regex2.search(sent)):
                        ann[sid]['hasPain']=0
                else:
                        print("***inferred cases to double check %s, %s***"%(fname, sid))
                        output_details(ann, ann, sid)
                '''

                if kw_regex1.search(sent) or kw_regex2.search(sent):
                    print("***inferred cases to double check %s, %s***"%(fname, sid))
                    output_details(ann, ann, sid)

                ann[sid]['hasPain']=0

def align_crossSB_cases(gold_ann_dict, ann_dict):
    for fname in gold_ann_dict:
        gold_ann=gold_ann_dict[fname]['ann']
        ann=ann_dict[fname]['ann']
        sids=sorted(ann.keys())
        i=0
        while i < len(sids):
            sid=sids[i]

            if ann[sid]['hasPain']==1 and gold_ann[sid]['hasPain'] != 1:
                try:
                    pos_str=ann[sid]['positions']
                except:
                    print("warning-6.1: removing label for %s (sent %s) that has only crossSB pain"%(fname, sid))
                    ann[sid]['hasPain'] = 0
                    continue

                if pos_str == "":
                    print("should not happend %s (sent %s)"%(fname, sid))
                    exit(0)
                

                pos_ls=pos_str.split(",")
                has_no_cross_pain=0
                up_posit=None
                up_term=None
                up_loc=None
                sid_up=ann[sid]['crossSB_up']
                sid_down=ann[sid]['crossSB_down']

                for posit in pos_ls:
                    if re.search(r"^\(\d+:\d+\)$", posit):
                        has_no_cross_pain=1
                        break
                    elif re.search(r"^\(0:[0-9\-]+\)\-\(\d+:\)", posit):
                        up_st=int(re.search(r"^\(0:[0-9\-]+\)\-\((\d+):\)", posit).group(1))
                        up_end=len(ann[sid_up]["sent"])
                        up_term=ann[sid_up]["sent"][up_st:]
                        up_posit="(%s:%s)"%(up_st, up_end)
                        up_loc=ann[sid]["loc"].split("|")[0]

                if has_no_cross_pain == 0:
                    cleanLabel=0
                    if sid_up > 0 and ann[sid_up]['hasPain'] == 1:
                        cleanLabel=1
                        if not 'positions' in ann[sid_up]:
                            ann[sid_up]['positions']=up_posit
                            ann[sid_up]['terms']=up_term
                            ann[sid_up]['loc']=up_loc
                        else:
                            ann[sid_up]['positions']+=","+up_posit
                            ann[sid_up]['terms']+="|"+up_term
                            ann[sid_up]['loc']+="|"+up_loc

                        print("warning-6.3: moving %s %s to sent %s (%s)"%(up_term, up_posit, sid_up, ann[sid_up]['sent']))
                    elif sid_down > 0 and ann[sid_down]['hasPain'] == 1:
                        cleanLabel=1
                        
                    if cleanLabel == 1:
                        ann[sid]['hasPain'] = 0
                        print("warning-6.2: removing label for %s (sent %s) that has only crossSB pain"%(fname, sid))

            i+=1

def post_process_amia2020 (ann_dict):
    for fname in ann_dict:
        ann=ann_dict[fname]['ann']
        sids=sorted(ann.keys())

        for sid in sids:
            if ann[sid]['hasPain'] == 1:
                sent=ann[sid]['sent'].lower()
                if re.search(r"(^| )((did not report)|(declined)|(denies)|(denied)|(no[t]*)) .*((pain)|(angina)|(tenderness)|(headache))",sent) or re.search(r"pain free", sent):
                    ann[sid]['hasPain']=0
                    del ann[sid]['timing']
                    del ann[sid]['severity']
                    del ann[sid]['comment']
                    print("warning-2: change label for (%s)"%(sent))

# enhanced post processing, added on 2020-11-09
def post_process (ann_dict):
    for fname in ann_dict:
        ann=ann_dict[fname]['ann']
        sids=sorted(ann.keys())

        i=0
        for sid in sids:
            if ann[sid]['hasPain'] == 1:
                sent_orig=ann[sid]['sent']
                sent=sent_orig.lower()
                if sid > 1:
                    pre_sent=ann[sid-1]['sent'].lower()

                try:
                    pos_str=ann[sid]['positions']
                except:
                    print("warning-5.1: missing positions: %s (sent %s)"%(fname, sid))
                    continue

                pos_ls=pos_str.split(",")
                new_pos_ls=[]

                try:
                    pain_loc=ann[sid]['loc']
                except:
                    print("warning-5.2: missing location: %s (sent %s)"%(fname, sid))
                    continue

                pls=pain_loc.split("|")
                new_pls=[]

                terms=ann[sid]['terms']
                tls=terms.split("|")
                new_tls=[]


                tidx=0
                for pos_str in pos_ls:
                    loc=pls[tidx]
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
                                loc="unk"
                            else:
                                print("warning-3.1: mismatch (%s) vs. (%s)"%(term2, term))

                                continue

                        sent_lh=sent[0:t_st]
                        sent_lh_r=re.sub(r"^.*   ","",sent_lh)
                        sent_lh_r=re.sub(r"^.*(but)|(however) ", "", sent_lh)
                    else:
                        (t_st, t_end, t2_st)=re.search(r"\((\d+):(\d+)\)\-\((\d+):\)", pos_str).groups()
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
                    negation = 0
                    if re.search(r"(^| )((did not report)|(decline)|(deny)|(denie[sd])|(no)|(not having)|(negative for)) [-:]*[a-z,\- \/]*$", sent_lh_r.lower()) or re.search("(^| )(free)", sent_rh.lower()):
                        negation = 1

                    if re.search(r"(^| )((as needed for)|(prn)) [-:]*[a-z,\- \/]*$", sent_lh_r.lower()):
                        negation = 1
                    
                    if re.search(r"(^| )(if [^ ]+ ((has)|(have)|(develops?))) [-:]*[a-z,\- \/]*$", sent_lh_r.lower()):
                        negation = 1

                    if negation == 1:
                        print("warning-4: detected negation for %s: %s [[%s]] %s"%(term2, sent_lh, term2, sent_rh.lower()))
                        
                    else:
                        new_pos_ls.append(pos_str)
                        new_pls.append(loc)
                        new_tls.append(term)

                    tidx+=1
                     

                if len(new_pos_ls) == 0:
                    ann[sid]['hasPain']=0
                    del ann[sid]['timing']
                    del ann[sid]['severity']
                    del ann[sid]['comment']
                    del ann[sid]['positions']
                    del ann[sid]['terms']
                    print("warning-2: change label for (%s)"%(sent))
                else:
                    ann[sid]['positions']=",".join(new_pos_ls)
                    ann[sid]['terms']="|".join(new_tls)
                   
                    ann[sid]['loc']="|".join(new_pls)
                    
def evaluate_doc (ann_dict, gold_ann_dict):
    Y=[]
    Y_gold=[]
    tp=0
    fp=0
    tn=0
    fn=0
    for fname in gold_ann_dict:
        gold_ann=gold_ann_dict[fname]['ann']
        ann=ann_dict[fname]['ann']
        sids=sorted(gold_ann.keys())
        gold_has_pain=0
        ann_has_pain=0
        gold_pain_loc=set()
        ann_pain_loc=set()

        if len(ann.keys()) != len(sids):
            print ("warning-1: %s has mismatched # of sentences"%(fname))
            exit(0)

        for sid in sids:
            if gold_ann[sid]['hasPain'] == 1:
                gold_has_pain=1
                gold_pain_loc.add(gold_ann[sid]['loc'])
            if ann[sid]['hasPain'] == 1:
                ann_has_pain=1
                try:
                    ann_pain_loc.add(ann[sid]['loc'])
                except:
                    pass

        Y.append(ann_has_pain)
        Y_gold.append(gold_has_pain)
        if gold_has_pain == 1:
            if ann_has_pain == 1:
                tp+=1
            else:
                fn+=1
                try:
                    print("***false negative: %s (gold: %s) ***"%(fname, "|".join(sorted(gold_pain_loc))))
                except:
                    print("***false negative: %s ***"%(fname))
        else:
            if ann_has_pain == 1:
                fp+=1
                try:
                    print("***false positive: %s (ann: %s) ***"%(fname, "|".join(sorted(ann_pain_loc))))
                except:
                    print("***false positive: %s ***"%(fname))
            else:
                tn+=1

    total_inst=tp+fp+tn+fn
    total_pos=tp+fn
    total_neg=tn+fp
    prec=tp/(tp+fp)
    recall=tp/(tp+fn)
    f=prec*recall*2/(prec+recall)
    return(total_inst,total_pos, total_neg, prec,recall,f, Y, Y_gold)


def evaluate_sent (ann_dict, gold_ann_dict):
    Y=[]
    Y_gold=[]
    tp=0
    fp=0
    tn=0
    fn=0
    correct_loc=0
    total_loc=0
    adj_total_loc=0
    for fname in gold_ann_dict:
        sids_for_loc=[]
        gold_ann=gold_ann_dict[fname]['ann']
        ann=ann_dict[fname]['ann']
        sids=sorted(gold_ann.keys())
        if len(ann.keys()) != len(sids):
            print ("warning-1: %s has mismatched # of sentences"%(fname))
            exit(0)

        for sid in sids:
            Y.append(ann[sid]['hasPain'])
            Y_gold.append(gold_ann[sid]['hasPain'])

            if gold_ann[sid]['hasPain'] == 1:
                if ann[sid]['hasPain'] == 1:
                    tp+=1
                    sids_for_loc.append(sid)
                else:
                    fn+=1
                    print("***false negative %s, %s***"%(fname, sid))
                    output_details(gold_ann, ann, sid)
            else:
                if ann[sid]['hasPain'] == 1:
                    fp+=1
                    
                    print("***false positive %s, %s***"%(fname, sid))
                    output_details(gold_ann, ann, sid)
                else:
                    tn+=1

        for sid in sids_for_loc:
            try:
                loc_ann=ann[sid]['loc']
                if loc_ann is None:
                    loc_ann='unk'
            except:
                loc_ann='unk'

            try:
                loc_gold=gold_ann[sid]['loc']
                if loc_gold is None:
                    loc_gold='unk'
            except:
                loc_gold='unk'

            cor_loc_rate=compare_loc_ann(loc_gold,loc_ann)
            if cor_loc_rate > 0.5:
                correct_loc+=1
                print("correct location (%s, %s): %s vs. %s"%(fname, sid, loc_ann, loc_gold))
                adj_total_loc+=1
            else:
                print("error location (%s, %s): %s vs. %s"%(fname, sid, loc_ann, loc_gold))
                output_details(gold_ann, ann, sid)
                pls=list(set(loc_ann.split("|")))
                if not (len(pls) == 1 and pls[0] == 'unk'):
                    adj_total_loc+=1
                                    
            total_loc+=1

    total_inst=tp+fp+tn+fn
    total_pos=tp+fn
    total_neg=tn+fp
    prec=tp/(tp+fp)
    recall=tp/(tp+fn)
    f=prec*recall*2/(prec+recall)

    acc_loc=1.0*correct_loc/total_loc
    adj_acc_loc=1.0*correct_loc/adj_total_loc
    
    return(total_inst,total_pos,total_neg,prec,recall,f,acc_loc, adj_acc_loc, Y, Y_gold)

if '__main__' == __name__:
    if (len(sys.argv) < 3):
        print (sys.argv[0], "opt goldanndir anndir")
        print ("opt: 1 -- normal evaluation, 2 [AMIA], 3 [new] -- evaluation w/ postprocessing")
        exit (1)
    else:
        opt=sys.argv[1]
        goldanndir=sys.argv[2]
        anndir=sys.argv[3]

    #id map
    id_map=import_id_map()

    #pain keywords
    pain_words=import_keywords()
    kw_regex1=trie_regex_from_words(pain_words)
    kw_regex2=re.compile(r"\b" + "[a-z]+algia" + r"\b", re.IGNORECASE)

    #pain location map
    pain_loc_map=import_pain_loc_map()


    # EHR notes info
    note_info_dict=load_note_info()

    # load gold annotation
    file_list=[]
    file_dict={}
    inputdir=goldanndir
    for f in listdir(inputdir):
        if re.search("\.txt", f):
            infile=join(inputdir,f)
            print(infile)
            file_list.append(infile)
            file_dict[f]=1

    gold_ann_dict=load_ann(file_list)

    file_list=[]
    inputdir=anndir
    for f in listdir(inputdir):
        if re.search("\.txt", f) and f in file_dict:
            infile=join(inputdir,f)
            file_list.append(infile)

    ann_dict=load_ann(file_list)

    align_crossSB_cases(gold_ann_dict, ann_dict)

    if opt == "1":
        print("===== not drop inferred cases =====")
        print("*** sentence level ***")
        (total_inst,total_pos,total_neg,prec,recall,f, acc_loc, adj_acc_loc, Y, Y_gold)=evaluate_sent(ann_dict, gold_ann_dict)
        print("*** note level ***")
        (total_inst_d,total_pos_d,total_neg_d,prec_d,recall_d,f_d, Yd, Yd_gold)=evaluate_doc(ann_dict, gold_ann_dict)

        print("===== drop inferred cases =====")
        drop_inferred_cases(gold_ann_dict)


        print("*** sentence level ***")
        (total_inst2,total_pos2,total_neg2,prec2,recall2,f2, acc_loc2, adj_acc_loc2, Y2, Y2_gold)=evaluate_sent(ann_dict, gold_ann_dict)
        print("*** note level ***")
        (total_inst_d2,total_pos_d2,total_neg_d2,prec_d2,recall_d2,f_d2, Yd2, Yd2_gold)=evaluate_doc(ann_dict, gold_ann_dict)

    elif opt == "2" or opt == "3":
        if opt == "2":
            post_process_amia2020(ann_dict)
        elif opt == "3":
            post_process(ann_dict)

        print("===== not drop inferred cases =====")
        print("*** sentence level ***")
        (total_inst,total_pos,total_neg,prec,recall,f, acc_loc, adj_acc_loc, Y, Y_gold)=evaluate_sent(ann_dict, gold_ann_dict)
        print("*** note level ***")
        (total_inst_d,total_pos_d,total_neg_d,prec_d,recall_d,f_d, Yd, Yd_gold)=evaluate_doc (ann_dict, gold_ann_dict)

        print("===== drop inferred cases =====")
        drop_inferred_cases(gold_ann_dict)
        print("*** sentence level ***")
        (total_inst2,total_pos2,total_neg2,prec2,recall2,f2, acc_loc2, adj_acc_loc2, Y2, Y2_gold)=evaluate_sent(ann_dict, gold_ann_dict)
        print("*** note level ***")
        (total_inst_d2,total_pos_d2,total_neg_d2,prec_d2,recall_d2,f_d2, Yd2, Yd2_gold)=evaluate_doc(ann_dict, gold_ann_dict)


    print("============ sent level evaluation ==========")
    print("total %s instances (pos=%s, neg=%s), prec=%.2f recall=%.2f f-score=%.2f"%((total_inst,total_pos,total_neg,prec,recall,f)))
    print("acc_loc: %.2f, adjusted acc_loc: %.2f"%(acc_loc, adj_acc_loc))
    print("excluding inferred cases:")
    print("total %s instances (pos=%s, neg=%s), prec=%.2f recall=%.2f f-score=%.2f"%((total_inst2,total_pos2,total_neg2,prec2,recall2,f2)))
    print("acc_loc: %.2f, adjusted acc_loc: %.2f"%(acc_loc2, adj_acc_loc2))


    print("============ note level evaluation ==========")
    print("total %s instances (pos=%s, neg=%s), prec=%.2f recall=%.2f f-score=%.2f"%((total_inst_d,total_pos_d,total_neg_d,prec_d,recall_d,f_d)))
    print("excluding inferred cases:")
    print("total %s instances (pos=%s, neg=%s), prec=%.2f recall=%.2f f-score=%.2f"%((total_inst_d2,total_pos_d2,total_neg_d2,prec_d2,recall_d2,f_d2)))


    print("============ bootstrap estimation of evaluation results ===========")
    n=1000
    rate=0.9
    outfile="boostrap_eval%s_n%d_sent.tsv"%(opt,n)
    boostrap_estimate(Y2, Y2_gold, outfile, n, 0.9)

    outfile="boostrap_eval%s_n%d_note.tsv"%(opt,n)
    boostrap_estimate(Yd2, Yd2_gold, outfile, n, 0.9)
