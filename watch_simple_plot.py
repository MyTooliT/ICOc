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

#log_file = 'unicorn_3A_rbal_rot_1000.txt'
log_file = 'log.txt'
#log_location = 'C:\\Users\\burgstaller\\Desktop\\Python\\MyTooliT_Watch\\'
log_location = 'C:\\Users\\burgstaller\\Desktop\\MyTooliTWatch\\'

lookup="Start"

with open(log_location + log_file) as myFile:
    for num, line in enumerate(myFile, 0):
        if lookup in line:
            print('found at line:'+str(num))
            skip=num+5
myFile.close()

# Read data from file 'filename.csv' 
# (in the same directory that your python process is based)
# Control delimiters, rows, column names with read_csv (see later) 
data = pd.read_csv(log_location + log_file,header=None,sep='\(|ms\)|\s+|;',skiprows=skip, engine='python', skipfooter=50, error_bad_lines=False) 
# Preview the first 5 lines of the loaded data 
data.head()

if skip > 10:   #as long as less than 8 holders are there the old ones are lesser then 10, new always about 40+
    try:
        data_clean = data.drop([0,2,3,5,6,8,9,11,12,14,15,17],axis=1)
        nr_of_axis=3
    except:
        try:
            data_clean = data.drop([0,2,3,5,6,8,9,11,12,14],axis=1)
            nr_of_axis=2
        except:
            data_clean = data.drop([0,2,3,5,6,8,9,11],axis=1)
            nr_of_axis=1

#    data_clean = data.drop([0,2,3,5,6,8,9,11],axis=1)
#    nr_of_axis=1
    data_clean.head()
    if(nr_of_axis==1):
        col_names = ['time','msg_cnt','timestamp','acc']       
    elif(nr_of_axis==3):
        col_names = ['time','msg_cnt','timestamp','accx','accy','accz']
    else:
        col_names = ['time','msg_cnt','timestamp','acc1','acc2']
    #print(data_clean)
#    col_names = ['time','msg_cnt','timestamp','acc']
else:
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

# this line can select data based on time stamps
#data_clean = data_clean[data_clean.loc[:,'time'].between(1000, 18000, inclusive=True)]


n_points = data_clean.loc[:,'time'].size

#n_points = data_clean.size


f_sample = n_points/(data_clean["time"].iloc[-1]-data_clean["time"].iloc[0])*1000
#f_sample = n_points/(data_clean.loc[n_points-1,'time']-data_clean.loc[1,'time'])*1000

stats = data_clean.describe()

if(nr_of_axis==1):
    std_dev = stats.loc['std',['acc']]     
    means = stats.loc['mean',['acc']]                      
elif(nr_of_axis==3):
    std_dev = stats.loc['std',['accx','accy','accz']]
    means = stats.loc['mean',['accx','accy','accz']] 
    print("Avg  X: %d Y: %d Z: %d" % (stats.loc['mean',['accx']],
                                                    stats.loc['mean',['accy']],
                                                    stats.loc['mean',['accz']]))
else:
    std_dev = stats.loc['std',['acc1','acc2']]

SNR = 20*np.log10(std_dev/(np.power(2,16)-1))

print("SNR of this file is : {:.2f} dB and {:.2f} dB @ {:.2f} kHz".format(min(SNR),max(SNR),f_sample/1000))



if(nr_of_axis==1):
    #data_clean.plot(y=['acc'],x='time',grid=True,figsize=(20,10))   
    f, axs = plt.subplots(2,1,figsize=(20,10))
    plt.subplot(211)
    plt.plot(data_clean['time'], data_clean[['acc']])
    #plt.plot(data_clean['time'], data_clean[['accx','accy','accz']])
    plt.subplot(212)
    plt.psd(data_clean['acc']-data_clean['acc'].mean(), 512, f_sample)
    plt.show()
                        
elif(nr_of_axis==3):
        #data_clean.plot(y=['acc'],x='time',grid=True,figsize=(20,10))   
    f, axs = plt.subplots(2,1,figsize=(20,10))
    plt.subplot(211)
    plt.plot(data_clean['time']/1000, data_clean[['accx','accy','accz']])
    plt.subplot(212)
    plt.psd(data_clean['accx']-data_clean['accx'].mean(), 512, f_sample)
    plt.show()    
else:
    data_clean.plot(y=['acc1','acc2'],x='time',grid=True,figsize=(20,10))













