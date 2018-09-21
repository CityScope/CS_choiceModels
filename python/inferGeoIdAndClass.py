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
from sklearn.metrics import accuracy_score
from IPython.display import Image
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
        print(node)
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
        
fractionSample=0.4
# the sample will first be narrowed down by (i) home loc in GBA, (ii) in thr work force and 
# (iii) the HH income could be identified
# a fraction of the remaining sample for ease of computation when fitting the logit model


#'TEN':'Tenure' 1 owned mort, 2 owned clear, 3 rented, 4 occupied no rent (cat)
# HHT; 'Household' type (cat)
# 'CIT': 1-4 citizen, 5 not citizen (cat)
#'COW' class of worker (cat)
# 'MAR': marraige status (cat)
#'MIG': migration status (live here a year ago or not? (cat)
# 'SCH' school enrollment (cat)
# 'SCHL' education level attained (cat)
#'WKHP': works hours per week (con)
#'JWAP' time of arrival at work (con)
#'WAOB': world area of birth

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

#dictionary of upper bounds of income bands to columns in the excel
ageColumnDict=OrderedDict()
ageColumnDict[20]= [12, 14, 60, 62]
ageColumnDict[30]= [16, 18, 20, 22, 64, 66, 68, 70]
ageColumnDict[40]= [24, 26, 72, 74, 72, 74]
ageColumnDict[50]= [38, 30, 76, 78 ]
ageColumnDict[60]= [32, 34, 80, 82]
ageColumnDict[70]= [36, 38, 40, 42, 84, 86, 88, 90]
ageColumnDict[80]= [44, 46, 92, 94]
ageColumnDict[200]= [48, 50, 96, 98]

#dict to reference PUMS modes to columns in the census modal split data
modeColumnDict=OrderedDict()
modeColumnDict[1]= 4
modeColumnDict[2]= 22
modeColumnDict[3]= 24
modeColumnDict[4]= 26
modeColumnDict[5]= 28
modeColumnDict[6]= 30
modeColumnDict[7]= 32
modeColumnDict[8]= 34
modeColumnDict[9]= 36
modeColumnDict[10]= 38
modeColumnDict[11]= 42
modeColumnDict[12]= 40
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
cpttModeDict=OrderedDict()
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

def getAgeBand(row):
    if np.isnan(row['age']):
        return np.nan
    for i in range(len(ageColumnDict.items())):
        if row['age']<list(ageColumnDict.items())[i][0]:
            return int(i)
    return len(ageColumnDict)

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
ageGender=pd.read_csv('./data/ACS_16_5YR_B01001/ACS_16_5YR_B01001_with_ann.csv', index_col='Id2', skiprows=1)
# TODO: for ageGender split, need to use worker population, not total poplation as universe
modalSplit=pd.read_csv('./data/ACS_16_5YR_B08301/ACS_16_5YR_B08301_with_ann.csv', index_col='Id2', skiprows=1)

commuting=pd.read_csv('./data/tract2tractCommutingAllMass.csv', skiprows=2)
commuting['RESIDENCE']=commuting.apply(lambda row: str(row['RESIDENCE']).split(',')[0], axis=1)
commuting['WORKPLACE']=commuting.apply(lambda row: str(row['WORKPLACE']).split(',')[0], axis=1)
commuting['Workers 16 and Over']=commuting.apply(lambda row: float(str(row['Workers 16 and Over']).replace(',',"")), axis=1)

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
            'JWMNP':'travelT','HINCP':'incomeH'}
indivWide=indiv[[c for c in colsToKeep]]
indivWide.columns=[colsToKeep[c] for c in colsToKeep]

indivWide['homePUMA']=indivWide.apply(lambda row: str(int(row['homePUMA']+1e10))[-5:], axis=1)
# convert PUMAs to strings of length 5 (with zeros at start)

#only keep records where puma is in the included zone (roughly GBA)
indivWideGBA=indivWide.loc[indivWide['homePUMA'].isin(pumasIncluded)].copy()

indivWorkWide=indivWideGBA[indivWideGBA['workPOWPUMA']>1].copy() # only keep people in the work force
#indivWorkWide['CA']=indivWorkWide['numCarsP']>0 #create binary for Cars Available

indivWorkWide.loc[indivWorkWide['mode'] == 11, 'travelT'] = 0 #replace nan with zero for people who work at home
indivWorkWide['mode-1']=indivWorkWide.apply(lambda row: int(row['mode'])-1, axis=1)

indivWorkWide['simpleMode']=indivWorkWide.apply(lambda row: simpleMode(row['mode']), axis=1)
indivWorkWide['incomeQ']=indivWorkWide.apply(lambda row: getIncomeBand(row), axis=1)
indivWorkWide=indivWorkWide.loc[indivWorkWide['incomeQ'].notnull()]
indivWorkWide['incomeQ']=indivWorkWide['incomeQ'].astype('int')
indivWorkWide['ageQ']=indivWorkWide.apply(lambda row: getAgeBand(row), axis=1)
indivWorkWide['ageQ3'], ageBins=pd.qcut(indivWorkWide['age'], 3, labels=range(3), retbins=True)  
indivWorkWide['incomeQ3'], incomeBins=pd.qcut(indivWorkWide['incomePersonal'], 3, labels=range(3), retbins=True) 
indivCommute=indivWorkWide.loc[indivWorkWide['simpleMode']<4].reset_index(drop=True)
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
features=features.drop(['travelT', 'workPOWPUMA', 'homePUMA', 'mode', 'mode-1', 'simpleMode',
            'incomeQ','ageQ', 'ageQ3', 'incomeQ3' ], axis=1)
l=5
clf = tree.DecisionTreeClassifier(max_leaf_nodes=l, class_weight='balanced')            
clf = clf.fit(np.array(features), np.array(indivCommute['simpleMode'])) 
#dot_data = tree.export_graphviz(clf, out_file='treeBalanced' +str(l)+'.dot',feature_names=features.columns,  
#                         class_names=['drive', 'cycle', 'walk', 'PT'],  
#                         filled=True, rounded=True,  
#                         special_characters=True) 
#with open('treeBalanced' +str(l)+'.dot') as f:
#    dot_graph = f.read()
#g=graphviz.Source(dot_graph)
#g.render(filename='treeBalanced' +str(l))
profiles, leaves2Profiles=getProfiles(clf, features.columns)

terminalLeaves=clf.apply(features)
indivCommute['profile']=[leaves2Profiles[l] for l in terminalLeaves]


# plot the profiles

# Data to plot
labels = ['drive', 'cycle', 'walk', 'PT']
cols=2
rows=math.ceil(len(profiles)/cols)
fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(3*rows, 3*cols))
for p in profiles: 
    row=p//2
    column=p%2      
    sizes = profiles[p]['prob']
    colors = [[0, 225/255, 51/255], [43/255, 209/255, 252/255], [25/2555, 0/255, 217/255], [227/255, 123/255, 64/255]]
    # explode = (0.1, 0, 0, 0)  # explode 1st slice
    # Plot
    axes[row,column].pie(sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=140)
    axes[row,column].axis('equal')
    axes[row,column].set_title(profiles[p]['conditions'], y=1.08)
#delete unused axes
for a in range(p%2+1, 2):
    fig.delaxes(axes[rows-1][a])
plt.show()

#for name, importance in zip(features.columns, clf.feature_importances_):
#    print(name, importance)

plt.figure()    
plt.bar(range(len(clf.feature_importances_)), clf.feature_importances_)
plt.xticks(range(len(clf.feature_importances_)), features.columns, rotation=45)

############################ Build the CPDs for the Naive Bayes Classifier #######################################
# 
totalHHsbyGeo=[hhIncome.loc[int(revGeoidDict[j])][2]for j in revGeoidDict]
probIncomeGivenGeoList=[]
for i in revGeoidDict:
    probIncomeGivenGeoList.append([hhIncome.loc[int(revGeoidDict[i])][list(incomeColumnDict.items())[j][1]]/totalHHsbyGeo[i] for j in range(len(incomeColumnDict))])
probIncomeGivenGeo=np.array(probIncomeGivenGeoList)
totalHHsbyIncomeBand=np.array([sum([hhIncome.loc[int(revGeoidDict[i])][list(incomeColumnDict.items())[j][1]] for i in revGeoidDict]) for j in range(len(incomeColumnDict))])
incomePrior=totalHHsbyIncomeBand/sum(totalHHsbyIncomeBand)

totalWorkersbyGeo=[modalSplit.loc[int(revGeoidDict[j])][2]for j in revGeoidDict]
geoIdPrior=[modalSplit.loc[int(revGeoidDict[i])][2]/sum(totalWorkersbyGeo) for i in revGeoidDict]
totalWorkersByMode=np.array([sum([modalSplit.loc[int(revGeoidDict[i])][list(modeColumnDict.items())[j][1]] for i in revGeoidDict]) for j in range(len(modeColumnDict))])
modePrior=totalWorkersByMode/sum(totalWorkersByMode)
probModeGivenGeo=np.array([[modalSplit.loc[int(revGeoidDict[i])][list(modeColumnDict.items())[j][1]]/totalWorkersbyGeo[i] for j in range(len(modeColumnDict))] for i in revGeoidDict])


#CPD of PUMA, conditioned on home location (determnistic)
probPumaGivenGeo=np.array([[0 for i in range(len(pumaDict))] for j in range(len(geoidDict))])
for geoId in geoidDict:
    inPuma=geoid2puma[geoId]
    probPumaGivenGeo[geoidDict[geoId]][pumaDict[inPuma]]=1
pumaPrior=np.array([1/len(pumaDict) for i in range(len(pumaDict))])

#cpd of work location conditioned on mode and home location
#first need to reference the geoIds to the tract names in the commuting data
geoIdIndToNameDict={}
nameToIndDict={}
for geoId in geoidDict:
    geojsonInd=geoJsonGeoIdList.index(geoId)
    # find the name and the int 
    geoIdName=tractGeo['features'][geojsonInd]['properties']['NAMELSAD10']
    geoIdIndToNameDict[geoidDict[geoId]]=geoIdName # put in a dict. ind to name
    nameToIndDict[geoIdName]=geoidDict[geoId]


probsByMode=[]
commutingByMode=[]
#list for each mode except home
for m in cpttModeDict:
    odMode=np.empty([len(geoidDict), len(geoidDict)])
    #get mode names in cptt data that correspond to this mode ind
    cpptModes=cpttModeDict[m]
    #get subset of commuting dataframe for this mode and crosstab by res and workplace
    commutingThisMode=commuting.loc[commuting['Means of Transportation 18'].isin(cpptModes)]
    commutingByMode.append(commutingThisMode)
    odModeDf=pd.crosstab(commutingThisMode['RESIDENCE'], commutingThisMode['WORKPLACE'], commutingThisMode['Workers 16 and Over'], aggfunc='sum')    
    for oInd in range(len(geoidDict)):
        for dInd in range(len(geoidDict)):
            try:
                odMode[oInd, dInd]=odModeDf[geoIdIndToNameDict[oInd]][geoIdIndToNameDict[dInd]]
            except KeyError:
                odMode[oInd, dInd]=0
    odMode=np.nan_to_num(odMode)
    row_sums = odMode.sum(axis=1)
#    odMode[np.where(row_sums==0),:]=1
#    row_sums = odMode.sum(axis=1)
    probDest = odMode / row_sums[:, np.newaxis]
    probDest =np.nan_to_num(probDest)
    probsByMode.append(probDest)
    
#divide by row totals
#check that work at home is identity matrix

################ Sample most plausible home and work geoIDs using Naive Bayes

pickle.dump(geoid2puma, open('./results/tract2puma.p', 'wb'))

indivCommute['homeGEOID']=np.nan
indivCommute['workGEOID']=np.nan
indivCommuteOut=indivCommute.sample(frac=fractionSample).copy()
# shuffle the dataframe (in case theere's some ordering in the PUMS data)
indivCommuteOut=indivCommuteOut.reset_index(drop=True)

for i in range(len(indivCommuteOut)):
    if i%1000==0:
        print(i)
    samplePUMA=pumaDict[indivCommuteOut.iloc[i]['homePUMA']]
    sampleIncome=indivCommuteOut.iloc[i]['incomeQ']
    sampleMode=indivCommuteOut.iloc[i]['mode-1']
    postProbGeo_numerator=np.multiply(geoIdPrior, probModeGivenGeo[:,sampleMode])
    postProbGeo_numerator=np.multiply(postProbGeo_numerator,probIncomeGivenGeo[:,sampleIncome])
    postProbGeo_numerator=np.multiply(postProbGeo_numerator,probPumaGivenGeo[:,samplePUMA])
    postProbGeo=postProbGeo_numerator/np.nansum(postProbGeo_numerator) 
    postProbGeo[np.isnan(postProbGeo)]=0
    #choode the ind, not the name
    homeDrawInd = choice([g for g in revGeoidDict], 1, p=postProbGeo)[0]
    homeDraw=revGeoidDict[homeDrawInd]
    postProbWorkGeo=probsByMode[sampleMode][homeDrawInd,:]
    try:
        workDrawInd = choice([g for g in revGeoidDict], 1, p=postProbWorkGeo)[0]
        workDraw=revGeoidDict[workDrawInd]
        indivCommuteOut.at[i, 'workGEOID']= workDraw
    except:
        pass
    #postProbWorkGeo=get row of mode OD matrix corresponding to the selected home geoId
#    indivWorkWideOut.set_value(i, 'homeGEOID', homeDraw) 
    indivCommuteOut.at[i, 'homeGEOID']= homeDraw

pickle.dump(indivCommuteOut, open('./results/population.p', 'wb'))



