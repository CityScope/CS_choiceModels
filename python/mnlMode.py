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

#get rid of work at home since this is exogenous to the model
#print(len(simPop.loc[simPop['simpleMode']==4]))
simPop=simPop.loc[simPop['simpleMode']<4].reset_index(drop=True)

simPop['homeGEOID']=simPop.apply(lambda row: str(int(row['homeGEOID'])), axis=1)
simPop['workGEOID']=simPop.apply(lambda row: str(int(row['workGEOID'])), axis=1)
simPop=pd.concat([simPop, pd.get_dummies(simPop['profile'], prefix='profile')], axis=1)

simPop['accessibleEmployment_home']=simPop.apply(lambda row: geoidAttributes[row['homeGEOID']]['accessibleEmployment'], axis=1)
simPop['totalHousing_home']=simPop.apply(lambda row: geoidAttributes[row['homeGEOID']]['housingDensity'], axis=1)

simPop['totalResidents_home']=simPop.apply(lambda row: geoidAttributes[row['homeGEOID']]['residents'], axis=1)
simPop['totalEmployment_pow']=simPop.apply(lambda row: geoidAttributes[row['workGEOID']]['employment'], axis=1)
simPop['totalResidents_pow']=simPop.apply(lambda row: geoidAttributes[row['workGEOID']]['residents'], axis=1)
simPop['totalEmployment_home']=simPop.apply(lambda row: geoidAttributes[row['homeGEOID']]['employment'], axis=1)

simPop['residentialDensity_home']=simPop.apply(lambda row: row['totalResidents_home']/geoidAttributes[row['homeGEOID']]['landArea'], axis=1)
simPop['employmentDensity_pow']=simPop.apply(lambda row: row['totalEmployment_pow']/geoidAttributes[row['workGEOID']]['landArea'], axis=1)
simPop['residentialDensity_pow']=simPop.apply(lambda row: row['totalResidents_pow']/geoidAttributes[row['workGEOID']]['landArea'], axis=1)
simPop['employmentDensity_home']=simPop.apply(lambda row: row['totalEmployment_home']/geoidAttributes[row['homeGEOID']]['landArea'], axis=1)

simPop['lwBalance_home']=simPop.apply(lambda row: -np.abs((row['residentialDensity_home']-row['employmentDensity_home']))/
      (4*(row['residentialDensity_home']+row['employmentDensity_home'])), axis=1)
simPop['lwBalance_pow']=simPop.apply(lambda row: -np.abs((row['residentialDensity_pow']-row['employmentDensity_pow']))/
      (4*(row['residentialDensity_pow']+row['employmentDensity_pow'])), axis=1)
#gini coef

simPop.at[simPop['lwBalance_pow'].isnull(),'lwBalance_pow']=0

# add all travel times and costs to wide dataframe
simPop['tt_walk']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['walk']['time'], axis=1)
simPop['tt_cycle']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['cycle']['time'], axis=1)
simPop['tt_drive']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['drive']['time'], axis=1)
simPop['transitTime_PT']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['transit']['transitTime'], axis=1)
simPop['walkTime_PT']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['transit']['walkTime'], axis=1)
simPop['waitTime_PT']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['transit']['waitTime'], axis=1)
simPop['transfers_PT']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['transit']['transfers'], axis=1)
simPop['dist_drive']= simPop.apply(lambda row: travelCosts[str(int(row['homeGEOID']))][str(int(row['workGEOID']))]['drive']['distance'], axis=1)
simPop['cost_drive']= simPop.apply(lambda row: (row['dist_drive']/1000)*perKmCarCost + annualCarCost/(daysPerYear*2), axis=1)
simPop['cost_PT']=costPT
simPop['cost_walk']=0
simPop['cost_cycle']=annualBicycleCost/(daysPerYear*2)
#simPop['PT_Avail']= simPop.apply(lambda row: not np.isnan(row['transitTime_PT']), axis=1)

# if no transit route found by OTP, assume transit cost same as the maximum
for i in range(len(simPop)):
    if np.isnan(simPop.iloc[i]['transitTime_PT']):
        simPop.at[i,'transitTime_PT'] =max(simPop['transitTime_PT']) 
        simPop.at[i,'walkTime_PT'] =max(simPop['walkTime_PT'])
        simPop.at[i,'waitTime_PT'] =max(simPop['waitTime_PT'])
        simPop.at[i,'transfers_PT'] =max(simPop['transfers_PT'])

##interact cost with income
#for m in ['drive', 'PT', 'walk', 'cycle']:
#    simPop['cost_'+m+'_by_personalIncome']=simPop.apply(lambda row: row['cost_'+m]/(max(row['incomePersonal'],10000)), axis=1) 
   
simPop=simPop.sort_values(by='simpleMode').reset_index(drop=True)

##################### Create Long Dataframe for max likelihood estimation ############################
ind_variables = ['employmentDensity_pow', 'residentialDensity_home', 'residentialDensity_pow','employmentDensity_home','lwBalance_home','lwBalance_pow','homeGEOID', 'workGEOID',
                 'profile', 'profile_2', 'profile_3', 'profile_4', 'profile_5' ]
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
                         u'cycle_time': dict([(1, 'tt_cycle')]),
                         u'cost': dict([(0, 'cost_drive'),
                                       (1, 'cost_cycle'),
                                       (2, 'cost_walk'),
                                       (3, 'cost_PT')])                         
                        }

longSimPop=pl.convert_wide_to_long(simPop, 
                                   ind_variables, 
                                   alt_varying_variables, 
                                   availability_variables, 
                                   obs_id_column, 
                                   choice_column,
                                   new_alt_id_name=custom_alt_id)

#####################  Create the model specification ##################### 

basic_specification = OrderedDict()
basic_names = OrderedDict()

basic_specification["intercept"] = [1, 2, 3]
basic_names["intercept"] = ['ASC Walk',
                            'ASC Cycle',
                            'ASC Transit']

#basic_specification["lwBalance_home"] = [1, 2, 3]
#basic_names["lwBalance_home"] = [
#                          'lwBalance_home (Cycle)',
#                          'lwBalance_home (Walk)',
#                          'lwBalance_home (Transit)']
#basic_specification["lwBalance_pow"] = [ 1,2,3]
#basic_names["lwBalance_pow"] = [
#                          'lwBalance_pow (Cycle)',
#                          'lwBalance_pow (Walk)',
#                          'lwBalance_pow (Transit)'
#                          ]

basic_specification["employmentDensity_home"] = [1, 2, 3]
basic_names["employmentDensity_home"] = [
                          'employmentDensity_home (Cycle)',
                          'employmentDensity_home (Walk)',
                          'employmentDensity_home (Transit)']

basic_specification["employmentDensity_pow"] = [1, 2, 3]
basic_names["employmentDensity_pow"] = [
                          'employmentDensity_pow (Cycle)',
                          'employmentDensity_pow (Walk)',
                          'employmentDensity_pow (Transit)']

basic_specification["residentialDensity_home"] = [1, 2, 3]
basic_names["residentialDensity_home"] = [
                          'residentialDensity_home (Cycle)',
                          'residentialDensity_home (Walk)',
                          'residentialDensity_home (Transit)']

basic_specification["residentialDensity_pow"] = [1,  3]
basic_names["residentialDensity_pow"] = [
                          'residentialDensity_pow (Cycle)',
#                          'residentialDensity_pow (Walk)',
                          'residentialDensity_pow (Transit)']

basic_specification["walk_time"] = [[2, 3]]
basic_names["walk_time"] = ['walking time']

basic_specification["vehicle_time"] = [[0,3]]
basic_names["vehicle_time"] = ['vehicle_time']

basic_specification["cycle_time"] = [1]
basic_names["cycle_time"] = ['cycling time']

basic_specification["profile_2"] = [1, 2, 3]
basic_names["profile_2"] = [ 
                         'profile_2,  (Cycle)',
                          'profile_2, (Walk)',
                          'profile_2, (Transit)'
                          ]

basic_specification["profile_3"] = [1, 2, 3]
basic_names["profile_3"] = [ 
                         'profile_3,  (Cycle)',
                          'profile_3, (Walk)',
                          'profile_3, (Transit)']

basic_specification["profile_4"] = [1, 2, 3]
basic_names["profile_4"] = [ 
                         'profile_4,  (Cycle)',
                          'profile_4, (Walk)',
                          'profile_4, (Transit)']

basic_specification["profile_5"] = [1, 2, 3]
basic_names["profile_5"] = [ 
                         'profile_5,  (Cycle)',
                          'profile_5, (Walk)',
                          'profile_5, (Transit)']

basic_specification["cost"] = [[0, 1, 2, 3]]
basic_names["cost"] = [ 'cost']

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
