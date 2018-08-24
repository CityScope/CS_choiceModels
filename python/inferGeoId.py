#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 13:10:07 2018

@author: doorleyr
"""
import pandas as pd
from collections import OrderedDict 
import numpy as np
import pyproj
from shapely.geometry import Point, shape
import json
import pickle
from numpy.random import choice

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

utm19N=pyproj.Proj("+init=EPSG:32619")
wgs84=pyproj.Proj("+init=EPSG:4326")

#################################### Regions########################################
# Dont include every PUMA in the state

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
indiv=indiv.merge(hh[['HINCP', 'GRNTP', 'VEH']], left_index=True, right_index=True, how='left')

colsToKeep={'PUMA':'homePUMA', 'POWPUMA':'workPOWPUMA', 'AGEP':'age', 'JWMNP':'travelT', 
            'JWTR':'mode', 'HINCP':'incomeH', 'JWAP':'arrivalT', 'JWDP':'departureT', 'VEH': 'numCarsP', 'PINCP':'incomePersonal'}
indivWide=indiv[[c for c in colsToKeep]]
indivWide.columns=[colsToKeep[c] for c in colsToKeep]

indivWide['homePUMA']=indivWide.apply(lambda row: str(int(row['homePUMA']+1e10))[-5:], axis=1)
# convert PUMAs to strings of length 5 (with zeros at start)

#only keep records where puma is in the included zone (roughly GBA)
indivWideGBA=indivWide.loc[indivWide['homePUMA'].isin(pumasIncluded)].copy()

indivWorkWide=indivWideGBA[indivWideGBA['workPOWPUMA']>1].copy() # only keep people in the work force
indivWorkWide['CA']=indivWorkWide['numCarsP']>0 #create binary for Cars Available
indivWorkWide.loc[indivWorkWide['mode'] == 11, 'travelT'] = 0 #replace nan with zero for people who work at home
indivWorkWide['mode-1']=indivWorkWide.apply(lambda row: int(row['mode'])-1, axis=1)

#indivWorkWide['homePUMA']=indivWorkWide.apply(lambda row: int(row['homePUMA']), axis=1)
#indivWorkWide['workPOWPUMA']=indivWorkWide.apply(lambda row: int(row['workPOWPUMA']), axis=1)
#
indivWorkWide['simpleMode']=indivWorkWide.apply(lambda row: simpleMode(row['mode']), axis=1)
indivWorkWide['incomeQ']=indivWorkWide.apply(lambda row: getIncomeBand(row), axis=1).astype(int)
indivWorkWide['ageQ']=indivWorkWide.apply(lambda row: getAgeBand(row), axis=1)
indivWorkWide['ageQ3'], ageBins=pd.qcut(indivWorkWide['age'], 3, labels=range(3), retbins=True)  
indivWorkWide['incomeQ3'], incomeBins=pd.qcut(indivWorkWide['incomePersonal'], 3, labels=range(3), retbins=True)  

indivWorkWide=indivWorkWide.loc[indivWorkWide['incomeQ'].notnull()]

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

################ Sample most plausible home locations using the Bayes Net

pickle.dump(geoid2puma, open('./results/tract2puma.p', 'wb'))

indivWorkWide['homeGEOID']=np.nan
indivWorkWide['workGEOID']=np.nan
indivWorkWideOut=indivWorkWide.sample(frac=1).copy()
# shuffle the dataframe (in case theere's some ordering in the PUMS data)
indivWorkWideOut=indivWorkWideOut.reset_index(drop=True)

for i in range(len(indivWorkWideOut)):
    if i%1000==0:
        print(i)
    samplePUMA=pumaDict[indivWorkWideOut.iloc[i]['homePUMA']]
    sampleIncome=indivWorkWideOut.iloc[i]['incomeQ']
    sampleMode=indivWorkWideOut.iloc[i]['mode-1']
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
        indivWorkWideOut.at[i, 'workGEOID']= workDraw
    except:
        pass
    #postProbWorkGeo=get row of mode OD matrix corresponding to the selected home geoId
#    indivWorkWideOut.set_value(i, 'homeGEOID', homeDraw) 
    indivWorkWideOut.at[i, 'homeGEOID']= homeDraw
     
pickle.dump(indivWorkWideOut, open('./results/population.p', 'wb'))  