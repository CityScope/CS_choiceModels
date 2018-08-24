#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 14:11:45 2018

@author: doorleyr



"""

from collections import OrderedDict    
import pandas as pd                   
import numpy as np  
import pickle
import pylogit as pl
import pyproj


utm19N=pyproj.Proj("+init=EPSG:32619")
wgs84=pyproj.Proj("+init=EPSG:4326")

annualCarCost=5635
annualBicycleCost=200
perKmCarCost=0.11
daysPerYear=221
costPT=2.25

geoidAttributes=pickle.load(open('./results/geoidAttributes.p', 'rb'))

##################### get the prepared simPop data and add region data ################################# 
simPop=pickle.load(open('./results/population.p', 'rb'))
travelCosts=pickle.load(open('./results/tractTravelCosts.p', 'rb'))

# get rid of rows with unknown work location- this is due to there being for example, a positive number of cyclists in a zone based on the single-zone data
# but zero cycling trips from that zone in the OD data- so cant probabilitically assign a destination
simPop=simPop.dropna(subset=['workGEOID']).reset_index(drop=True)

#get rid of work at home since this is exogenous to the model
#print(len(simPop.loc[simPop['simpleMode']==4]))
simPop=simPop.loc[simPop['simpleMode']<4].reset_index(drop=True)

simPop['homeGEOID']=simPop.apply(lambda row: str(int(row['homeGEOID'])), axis=1)
simPop['workGEOID']=simPop.apply(lambda row: str(int(row['workGEOID'])), axis=1)
simPop['ageQ3']=simPop.apply(lambda row: int(row['ageQ3']), axis=1)
simPop['incomeQ3']=simPop.apply(lambda row: int(row['incomeQ3']), axis=1)
simPop=pd.concat([simPop, pd.get_dummies(simPop['ageQ3'], prefix='ageQ')], axis=1) 


simPop['accessibleEmployment']=simPop.apply(lambda row: geoidAttributes[row['homeGEOID']]['accessibleEmployment'], axis=1)
simPop['housingDensity']=simPop.apply(lambda row: geoidAttributes[row['homeGEOID']]['housingDensity'], axis=1)
simPop['employmentDensity']=simPop.apply(lambda row: geoidAttributes[row['workGEOID']]['employment'], axis=1)

# add all travel times and costs to wide dataframe
simPop['tt_walk']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['walk']['time'], axis=1)
simPop['tt_cycle']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['cycle']['time'], axis=1)
simPop['tt_drive']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['drive']['time'], axis=1)
simPop['transitTime_PT']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['transit']['transitTime'], axis=1)
simPop['walkTime_PT']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['transit']['walkTime'], axis=1)
simPop['waitTime_PT']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['transit']['waitTime'], axis=1)
simPop['oovTime_PT']=simPop.apply(lambda row:row['walkTime_PT']+row['waitTime_PT'], axis=1)
simPop['dist_drive']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['drive']['distance'], axis=1)
simPop['cost_drive']= simPop.apply(lambda row: (row['dist_drive']/1000)*perKmCarCost + annualCarCost/(daysPerYear*2), axis=1)
simPop['cost_PT']=costPT
simPop['cost_walk']=0
simPop['cost_cycle']=annualBicycleCost/(daysPerYear*2)
#simPop['PT_Avail']= simPop.apply(lambda row: not np.isnan(row['transitTime_PT']), axis=1)

for i in range(len(simPop)):
    if np.isnan(simPop.iloc[i]['transitTime_PT']):
        simPop.at[i,'transitTime_PT'] =max(simPop['transitTime_PT']) 
        simPop.at[i,'walkTime_PT'] =max(simPop['walkTime_PT'])
        simPop.at[i,'waitTime_PT'] =max(simPop['waitTime_PT'])
        
## Delete small num of observations where transit directions not found but observed person takes PT
#simPop=simPop.loc[simPop['PT_Avail'] | ~(simPop['simpleMode']==3)].reset_index(drop=True)

#interact cost with income
for m in ['drive', 'PT', 'walk', 'cycle']:
    simPop['cost_'+m+'_by_personalIncome']=simPop.apply(lambda row: row['cost_'+m]/(max(row['incomePersonal'],10000)), axis=1) 
   
simPop=simPop.sort_values(by='simpleMode').reset_index(drop=True)

##################### Create Long Dataframe for max likelihood estimation ############################
ind_variables = ['ageQ_0', 'ageQ_1','ageQ_2', 'accessibleEmployment', 'housingDensity', 'employmentDensity', 'homeGEOID', 'workGEOID', 'incomeQ3', 'ageQ3', 'incomePersonal']
# Specify the variables that vary across individuals and some or all alternatives

# Specify the availability variables
simPop['carAvail']=1
simPop['cycleAvail']=1
simPop['walkAvail']=1
simPop['PT_Avail']=1

availability_variables = {0:'carAvail',
                          1:'cycleAvail',
                          2:'walkAvail',
                          3:'PT_Avail'}

# The 'custom_alt_id' is the name of a column to be created in the long-format data
# It will identify the alternative associated with each row.
custom_alt_id = "mode_id"
# Create a custom id column that ignores the fact that this is a 
# panel/repeated-observations dataset. Note the +1 ensures the id's start at one.
obs_id_column = "custom_id"
simPop[obs_id_column] = np.arange(simPop.shape[0],
                                            dtype=int) + 1

choice_column = "simpleMode"

alt_varying_variables = {u'walk_time': dict([(2, 'tt_walk'), (3, 'walkTime_PT')]),
                         u'vehicle_time': dict([(0, 'tt_drive'), (3, 'transitTime_PT')]),
                         u'wait_time': dict([(3, 'waitTime_PT')]),
                         u'cycle_time': dict([(1, 'tt_cycle')]),
                         u'cost_by_personalIncome': dict([(0, 'cost_drive_by_personalIncome'),
                                       (1, 'cost_cycle_by_personalIncome'),
                                       (2, 'cost_walk_by_personalIncome'),
                                       (3, 'cost_PT_by_personalIncome')])
                        }

longSimPop=pl.convert_wide_to_long(simPop, 
                                   ind_variables, 
                                   alt_varying_variables, 
                                   availability_variables, 
                                   obs_id_column, 
                                   choice_column,
                                   new_alt_id_name=custom_alt_id)


longSimPop['employmentDensity'] = longSimPop['employmentDensity'].astype('float64')
longSimPop['housingDensity'] = longSimPop['housingDensity'].astype('float64') 
longSimPop['accessibleEmployment'] = longSimPop['accessibleEmployment'].astype('float64') 
longSimPop['ageQ_0'] = longSimPop['ageQ_0'].astype('int') 
longSimPop['ageQ_2'] = longSimPop['ageQ_2'].astype('int')

#####################  Create the model specification ##################### 

basic_specification = OrderedDict()
basic_names = OrderedDict()

basic_specification["intercept"] = [1, 2, 3]
basic_names["intercept"] = ['ASC Walk',
                            'ASC Cycle',
                            'ASC Transit']
#only need N-1 vars for intercepts and individual variables

#basic_specification["accessibleEmployment"] = [1, 2, 3]
#basic_names["accessibleEmployment"] = [
#                          'accessibleEmployment (Cycle)',
#                          'accessibleEmployment (Walk)',
#                          'accessibleEmployment (Transit)']

basic_specification["housingDensity"] = [1, 2, 3]
basic_names["housingDensity"] = [
                          'homeHousingDensity (Cycle)',
                          'homeHousingDensity (Walk)',
                          'homeHousingDensity (Transit)']
basic_specification["employmentDensity"] = [1, 2, 3]
basic_names["employmentDensity"] = [
                          'powEmploymentDensity (Cycle)',
                          'powEmploymentDensity (Walk)',
                          'powEmploymentDensity (Transit)']

basic_specification["walk_time"] = [[2, 3]]
basic_names["walk_time"] = ['walking time']

basic_specification["vehicle_time"] = [[0,3]]
basic_names["vehicle_time"] = ['vehicle_time']

basic_specification["cycle_time"] = [1]
basic_names["cycle_time"] = ['cycling time']

basic_specification["wait_time"] = [3]
basic_names["wait_time"] = ['wait_time']


basic_specification["ageQ_0"] = [1, 2, 3]
basic_names["ageQ_0"] = [ 
                         'Age_young,  (Cycle)',
                          'Age_young, (Walk)',
                          'Age_young, (Transit)']

basic_specification["ageQ_2"] = [ 1, 2, 3]
basic_names["ageQ_2"] = [ 
                         'Age_old,  (Cycle)',
                          'Age_old, (Walk)',
                          'Age_old, (Transit)']

basic_specification["cost_by_personalIncome"] = [[0, 1, 2, 3]]
basic_names["cost_by_personalIncome"] = [ 'cost_by_personalIncome']


##################### Fit the model ##################### 
simPop_mnl = pl.create_choice_model(data=longSimPop,
                                        alt_id_col=custom_alt_id,
                                        obs_id_col=obs_id_column,
                                        choice_col=choice_column,
                                        specification=basic_specification,
                                        model_type="MNL",
                                        names=basic_names)

# Specify the initial values and method for the optimization.
numCoef=sum([len(basic_specification[s]) for s in basic_specification])
simPop_mnl.fit_mle(np.zeros(numCoef))
print(simPop_mnl.get_statsmodels_summary())

pickle.dump(simPop_mnl, open('./results/simPop_mnl.p', 'wb'))
pickle.dump(longSimPop, open('./results/longSimPop.p', 'wb'))

#prediction_df=longSimPop.loc[longSimPop['custom_id']==longSimPop.iloc[0]['custom_id']]

#create new json, one list entry for each person with:
#homeGEOID, workGEOID, probDrive, probWalk...
#derivatives on instantiation

#print('VoT Driving, Income of 30000:')
#print((-7.985e-05/(-671/30000))*3600)