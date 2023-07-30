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

from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, precision_score, recall_score, accuracy_score
import numpy as np

def boostrap_estimate(Y, Y_gold, outfile, n=1000, rate=0.9):
	Y_idx=[i for i in range(0,len(Y))]
	nsample=int(rate*len(Y))
	print(len(Y),nsample)
	Y=np.array(Y)
	Y_gold=np.array(Y_gold)
	fout=open(outfile, "w")
	fout.write("rid\tprecision\trecall\tf1\n")
	for j in range(0,n):
		sel_Y_idx=np.random.choice(Y_idx,nsample,replace=True)
		y_true_ls=Y_gold[sel_Y_idx]
		y_hat_ls=Y[sel_Y_idx]
		prec=precision_score(y_true_ls, y_hat_ls)
		recall=recall_score(y_true_ls, y_hat_ls)
		f1=f1_score(y_true_ls, y_hat_ls)
		fout.write("%d\t%.6f\t%.6f\t%.6f\n"%(j, prec, recall, f1))
	fout.close()	
		
