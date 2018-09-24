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
#import pylogit as pl
import pyproj
from sklearn import tree
from sklearn.cross_validation import train_test_split
from sklearn.tree import DecisionTreeClassifier
import math
import matplotlib.pyplot as plt
from shapely.geometry import Point, shape
import json
from numpy.random import choice

def getProfiles(clf, feature_names):
    leaves2Profiles={}
    n_nodes = clf.tree_.node_count
    children_left = clf.tree_.children_left
    children_right = clf.tree_.children_right
    feature = clf.tree_.feature
    threshold = clf.tree_.threshold 
    props=clf.tree_.value
    visited=np.zeros(n_nodes)
    node=0
    parents={}
    profiles={}
    conditions=[]
    while sum(visited)<n_nodes:
        visited[node]=1
        if children_left[node]>0: #we are at a decision node
            #add the left condition
            if visited[children_left[node]]==0:
                conditions.append(str(feature_names[feature[node]]) + '<= '+ str(threshold[node]))
                #note the parent of the left child (this node) and move to the left node
                parents[children_left[node]]=node
                node=children_left[node]
            elif visited[children_right[node]]==0:
                conditions.append(str(feature_names[feature[node]]) + '>= '+ str(threshold[node]))            
                # note the parent of the right child (this node) and move to the right node
                parents[children_right[node]]=node
                node=children_right[node] 
            else:
                node=parents[node]
                conditions=conditions[:-1]
        else: #we are at a leaf node
            # save the class
            profiles[len(profiles)]={'conditions':conditions.copy(), 'prob': [props[node][0][p]/sum(props[node][0]) for p in range(len(props[node][0]))]}
            leaves2Profiles[node]=len(profiles)
            # go back to the parent of this node and remove the last condition
            node=parents[node]
            conditions=conditions[:-1]
            # add the right condition
    return profiles, leaves2Profiles
        
fractionSample=0.35
# the sample will first be narrowed down by (i) home loc in GBA, (ii) in thr work force and 
# (iii) the HH income could be identified
# a fraction of the remaining sample for ease of computation when fitting the logit model


#dictionary of upper bounds of income bands to columns in the excel
# TODO: get this info directly from the column names
incomeColumnDict=OrderedDict()
incomeColumnDict[10000]= 4
incomeColumnDict[15000]= 6
incomeColumnDict[20000]= 8
incomeColumnDict[25000]= 10
incomeColumnDict[30000]= 12
incomeColumnDict[35000]= 14
incomeColumnDict[40000]= 16
incomeColumnDict[45000]= 18
incomeColumnDict[50000]= 20
incomeColumnDict[60000]= 22
incomeColumnDict[75000]= 24
incomeColumnDict[100000]= 26
incomeColumnDict[125000]= 28
incomeColumnDict[150000]= 30
incomeColumnDict[200000]= 32
incomeColumnDict[1e100]= 34

# PUMS modes
#01     .Car, truck, or van
#02     .Bus or trolley bus
#03 .Streetcar or trolley car (carro publico in Puerto Rico)
#04     .Subway or elevated
#05 .Railroad
#06     .Ferryboat
#07 .Taxicab
#08     .Motorcycle
#09 .Bicycle
#10 .Walked
#11     .Worked at home
#12     .Other method

#dict to reference  modes in CPTT commuting data to modes in PUMS:
cpttModeDict={}
cpttModeDict[1]=['Car, truck, or van -- Drove alone',
             'Car, truck, or van -- In a 2-person carpool',
            'Car, truck, or van -- In a 3-person carpool',
            'Car, truck, or van -- In a 4-person carpool',
            'Car, truck, or van -- In a 5-or-6-person carpool',
            'Car, truck, or van -- In a 7-or-more-person carpool']
cpttModeDict[2]=['Bus or trolley bus']
cpttModeDict[3]=['Streetcar or trolley car']
cpttModeDict[4]=['Subway or elevated']
cpttModeDict[5]=['Railroad']
cpttModeDict[6]=['Ferryboat']
cpttModeDict[7]=['Taxicab']
cpttModeDict[8]=['Motorcycle']
cpttModeDict[9]=['Bicycle']
cpttModeDict[10]=['Walked']
cpttModeDict[11]=['Worked at home']
cpttModeDict[12]=['Other method']


modeDict={0:'privateV', 1:'bike', 2:'walk', 3:'PT', 4:'home'}

def simpleMode(mode):
    # maps from the 12 mode categories in PUMS to a simpler categorisation
    if mode in [1,7,8]:
        return 0
    if mode ==9:
        return 1
    if mode ==10:
        return 2
    if mode ==11:
        return 4
    else:
        return 3    

def getIncomeBand(row):
    # Aggregated census data gives income in bands.
    # For each PUMS individual, this function finds the band they fall into
    if np.isnan(row['incomeH']):
        return np.nan
    for i in range(len(incomeColumnDict.items())):
        if row['incomeH']<list(incomeColumnDict.items())[i][0]:
            return int(i)
    return len(incomeColumnDict)

def get_location(longitude, latitude, regions_json, name): 
    # for a given lat and lon, and a given geojson, find the name of the feature into which the latLon falls
    point = Point(longitude, latitude)
    for record in regions_json['features']:
        polygon = shape(record['geometry'])
        if polygon.contains(point):
            return record['properties'][name]
    return 'None'

##############################Spatial Data #########################################
    
utm19N=pyproj.Proj("+init=EPSG:32619")
wgs84=pyproj.Proj("+init=EPSG:4326")    

pumasIncluded=['00507', '03306', '03304',
               '02800', '00506', '03305',
               '00704', '03603', '03400', 
               '03302', '03301', '00505',
               '03303', '00508']

tractGeo=json.load(open('./data/tractsMass.geojson'))
pumaGeo=json.load(open('./data/PUMS/puma2016Mass.geojson'))
hhIncome=pd.read_csv('./data/ACS_16_5YR_B19001/ACS_16_5YR_B19001_with_ann.csv', index_col='Id2', skiprows=1)

# create dict to map geoids to pumas
# only keep geoids for which we have both geojson and income information
geoidList=[tractGeo['features'][i]['properties']['GEOID10']
           for i in range(len(tractGeo['features'])) if 
           int(tractGeo['features'][i]['properties']['GEOID10']) in list(hhIncome.index)]
geoJsonGeoIdList=[tractGeo['features'][i]['properties']['GEOID10'] for i in range(len(tractGeo['features']))]
geoid2puma={}
for geoId in geoidList:
    geojsonInd=geoJsonGeoIdList.index(geoId)
    med=shape(tractGeo['features'][geojsonInd]['geometry']).centroid
    inPuma=get_location(med.x, med.y, pumaGeo, 'PUMACE10')
    if inPuma in pumasIncluded:
        geoid2puma[geoId]=inPuma

# Create a dict of geoids to unique integer identifiers
# This is needed because the CPDs must be defined as arrays
geoidDict={list(geoid2puma.items())[i][0]:i for i in range(len(list(geoid2puma.items())))}
# create similar dict for PUMAs
pumaDict={pumasIncluded[i]: i for i in range(len(pumasIncluded))}

#create reverse dicts to map back to the ids:
revGeoidDict={v:k for k,v in geoidDict.items()}
revPUMADict={v:k for k,v in pumaDict.items()}

############################ Aggregate commuting data ################################
commuting=pd.read_csv('./data/tract2tractCommutingAllMass.csv', skiprows=2)
commuting['RESIDENCE']=commuting.apply(lambda row: str(row['RESIDENCE']).split(',')[0], axis=1)
commuting['WORKPLACE']=commuting.apply(lambda row: str(row['WORKPLACE']).split(',')[0], axis=1)
commuting['Workers 16 and Over']=commuting.apply(lambda row: float(str(row['Workers 16 and Over']).replace(',',"")), axis=1)
#first need to reference commuting data to geoIds
names2GeoIds={f['properties']['NAMELSAD10']:f['properties']['GEOID10'] for f in tractGeo['features']}
commuting['homeGEOID']=commuting.apply(lambda row: names2GeoIds[row['RESIDENCE']] if row['RESIDENCE'] in names2GeoIds else float('nan'), axis=1)
commuting['workGEOID']=commuting.apply(lambda row: names2GeoIds[row['WORKPLACE']] if row['WORKPLACE'] in names2GeoIds else float('nan'), axis=1)
#################################### PUMS Data #################################### 
#get the individual and household data
indiv=pd.read_csv('./data/PUMS/csv_pma/ss16pma.csv')
hh=pd.read_csv('./data/PUMS/csv_hma/ss16hma.csv')
# look up the HH income for each individual
#indiv=indiv.merge(hh[[ 'GRNTP', 'VEH', 'TEN', 'HHT']], left_index=True, right_index=True, how='left')
indiv=indiv.merge(hh[[ 'GRNTP', 'VEH', 'TEN', 'HHT', 'SERIALNO', 'HINCP']], on='SERIALNO', how='left')


colsToKeep={ 'PUMA':'homePUMA', 'POWPUMA':'workPOWPUMA', 'AGEP':'age',  'CIT':'citizen_status', 'MAR':'marraige_status','TEN':'Tenure', 'HHT': 'Household_type',
            'COW':'class_worker','MIG':'migration_status', 'SCH':'school_status', 'SCHL':'school_level', 'WAOB':'world_area_birth',
            'JWTR':'mode',  'JWAP':'arrivalT',   
            'PINCP':'incomePersonal', 'SEX':'sex',
            'JWMNP':'travelT','HINCP':'incomeH',
            'PWGTP':'weighting'}
indivWide=indiv[[c for c in colsToKeep]]
indivWide.columns=[colsToKeep[c] for c in colsToKeep]

indivWide['homePUMA']=indivWide.apply(lambda row: str(int(row['homePUMA']+1e10))[-5:], axis=1)
# convert PUMAs to strings of length 5 (with zeros at start)

#only keep records where puma is in the included zone (roughly GBA)
indivWideGBA=indivWide.loc[indivWide['homePUMA'].isin(pumasIncluded)].copy()

indivWorkWide=indivWideGBA[indivWideGBA['workPOWPUMA']>1].copy() # only keep people in the work force
#indivWorkWide['CA']=indivWorkWide['numCarsP']>0 #create binary for Cars Available

indivWorkWide.loc[indivWorkWide['mode'] == 11, 'travelT'] = 0 #replace nan with zero for people who work at home

indivWorkWide['simpleMode']=indivWorkWide.apply(lambda row: simpleMode(row['mode']), axis=1)
indivWorkWide['incomeQ']=indivWorkWide.apply(lambda row: getIncomeBand(row), axis=1)
indivWorkWide=indivWorkWide.loc[indivWorkWide['incomeQ'].notnull()]
indivWorkWide['incomeQ']=indivWorkWide['incomeQ'].astype('int')
indivWorkWide['ageQ3'], ageBins=pd.qcut(indivWorkWide['age'], 3, labels=range(3), retbins=True)  
indivWorkWide['incomeQ3'], incomeBins=pd.qcut(indivWorkWide['incomePersonal'], 3, labels=range(3), retbins=True) 
indivCommute=indivWorkWide.loc[indivWorkWide['simpleMode']<4].reset_index(drop=True) # work at home is exogeneous to the model
#create new variables
indivCommute['collegeDegree']=indivCommute.apply(lambda row: row['school_level']>20, axis=1)
indivCommute['gradDegree']=indivCommute.apply(lambda row: row['school_level']>21, axis=1)
indivCommute['Renter']=indivCommute.apply(lambda row: row['Tenure']==3, axis=1)
indivCommute['1PersonFemaleHH']=indivCommute.apply(lambda row: row['Household_type']==6, axis=1)
indivCommute['nonProfitWorker']=indivCommute.apply(lambda row: row['class_worker']==2, axis=1)
indivCommute['female']=indivCommute.apply(lambda row: row['sex']==2, axis=1)

catVars=[ 'citizen_status', 'marraige_status', 'migration_status', 'school_status', 'world_area_birth']
for col in catVars:
    indivCommute=pd.concat([indivCommute, pd.get_dummies(indivCommute[col], prefix=col)],  axis=1) 
indivCommute=indivCommute.drop(catVars, axis=1)

indivCommute=indivCommute.drop(['school_level', 'Tenure', 'Household_type', 'class_worker', 'sex'], axis=1)

############################ Find the profile of each person ############################

features=indivCommute.copy()
features=features.drop(['travelT', 'workPOWPUMA', 'homePUMA', 'mode', 'simpleMode',
            'incomeQ', 'ageQ3', 'incomeQ3' , 'weighting'], axis=1)
l=5
clf = tree.DecisionTreeClassifier(max_leaf_nodes=l, class_weight='balanced')            
clf = clf.fit(np.array(features), np.array(indivCommute['simpleMode'])) 
profiles, leaves2Profiles=getProfiles(clf, features.columns)

terminalLeaves=clf.apply(features)
indivCommute['profile']=[leaves2Profiles[l] for l in terminalLeaves]

############################# Sample home and work geoIds based on Naive Bayes approach #######################################

pickle.dump(geoid2puma, open('./results/tract2puma.p', 'wb'))

indivCommute['homeGEOID']=np.nan
indivCommute['workGEOID']=np.nan
indivCommuteOut=indivCommute.sample(frac=fractionSample, weights=indivCommute['weighting'], random_state=0).copy()
# shuffle the dataframe (in case theere's some ordering in the PUMS data)
indivCommuteOut=indivCommuteOut.reset_index(drop=True)

for i in range(len(indivCommuteOut)):
    if i%1000==0:
        print(i)
    samplePUMA=indivCommuteOut.iloc[i]['homePUMA']
#    sampleIncome=indivCommuteOut.iloc[i]['incomeQ']
    sampleMode=indivCommuteOut.iloc[i]['mode']
    potentialHomeGeos=[g for g in geoid2puma if geoid2puma[g]==samplePUMA]
    commutingSubset=commuting[commuting['homeGEOID'].isin(potentialHomeGeos)
        &commuting['Means of Transportation 18'].isin(cpttModeDict[sampleMode]) 
        &commuting['workGEOID'].isin(geoid2puma)]
    if len(commutingSubset)>0:
        sampleRow=commutingSubset.sample(n=1, weights=commutingSubset['Workers 16 and Over'])       
    [sampleHomeGeoId, sampleWorkGeoId]=sampleRow['homeGEOID'].values[0], sampleRow['workGEOID'].values[0]
    indivCommuteOut.at[i, 'homeGEOID']= sampleHomeGeoId
    indivCommuteOut.at[i, 'workGEOID']= sampleWorkGeoId

indivCommuteOut=indivCommuteOut[~indivCommuteOut['homeGEOID'].isna()].reset_index(drop=True)    
pickle.dump(indivCommuteOut, open('./results/population.p', 'wb'))



