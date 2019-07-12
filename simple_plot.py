# -*- coding: utf-8 -*-
"""
Created on Mon May 13 17:33:09 2019

@author: nleder
"""

import os
# Load the Pandas libraries with alias 'pd' 
import pandas as pd 

import matplotlib.pyplot as plt
import numpy as np

log_file = 'log.txt'
log_location = 'C:\\Users\\burgstaller\\Desktop\\Python\\CAN-PYTHON\\'

# Read data from file 'filename.csv' 
# (in the same directory that your python process is based)
# Control delimiters, rows, column names with read_csv (see later) 
data = pd.read_csv(log_location + log_file,header=None,sep='\(|ms\)|\s+|;',skiprows=10, engine='python', skipfooter=50, error_bad_lines=False) 
# Preview the first 5 lines of the loaded data 
data.head()

try:
    data_clean = data.drop([0,2,3,5,6,8,9,11,12,14],axis=1)
    nr_of_axis=3
except:
    try:
        data_clean = data.drop([0,2,3,5,6,8,9,11],axis=1)
        nr_of_axis=2
    except:
        data_clean = data.drop([0,2,3,5,6,8],axis=1)
        nr_of_axis=1

data_clean.head()


if(nr_of_axis==1):
    col_names = ['time','msg_cnt','acc']       
elif(nr_of_axis==3):
    col_names = ['time','msg_cnt','accx','accy','accz']
else:
    col_names = ['time','msg_cnt','acc1','acc2']
data_clean.columns = col_names                     

if(nr_of_axis==1):
    data_clean.plot(y=['acc'],x='time',grid=True,figsize=(20,10))                       
elif(nr_of_axis==3):
    data_clean.plot(y=['accx','accy','accz'],x='time',grid=True,figsize=(20,10))     
else:
    data_clean.plot(y=['acc1','acc2'],x='time',grid=True,figsize=(20,10))

stats = data_clean.describe()

if(nr_of_axis==1):
    std_dev = stats.loc['std',['acc']]                      
elif(nr_of_axis==3):
    std_dev = stats.loc['std',['accx','accy','accz']]
else:
    std_dev = stats.loc['std',['acc1','acc2']]
SNR = 20*np.log10(std_dev/(np.power(2,16)-1))

n_points = data_clean.loc[:,'time'].size

f_sample = n_points/(data_clean.loc[n_points-1,'time']-data_clean.loc[1,'time'])*1000

print("SNR of this file is : {:.2f} dB and {:.2f} dB @ {:.2f} kHz".format(min(SNR),max(SNR),f_sample/1000))



