#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 14:11:45 2018

@author: doorleyr



"""

import pandas as pd
import json
import pickle
from time import sleep
import urllib.request
import pyproj
from shapely.ops import transform
from shapely.geometry import shape
from functools import partial

utm19N=pyproj.Proj("+init=EPSG:32619")
wgs84=pyproj.Proj("+init=EPSG:4326")

project = partial(
    pyproj.transform,
    wgs84, # source coordinate system
    utm19N) # destination coordinate system

geoIdGeo=json.load(open('./data/tractsMass.geojson'))
housingUnits=pd.read_csv('./data/ACS_16_5YR_B25001/ACS_16_5YR_B25001_with_ann.csv', skiprows=1, index_col='Id2')
geoId2puma=pickle.load(open('./results/tract2puma.p', 'rb'))

# get commuting data
commuting=pd.read_csv('./data/tract2tractCommutingAllMass.csv', skiprows=2)
commuting['RESIDENCE']=commuting.apply(lambda row: str(row['RESIDENCE']).split(',')[0], axis=1)
commuting['WORKPLACE']=commuting.apply(lambda row: str(row['WORKPLACE']).split(',')[0], axis=1)

commuting['Workers 16 and Over']=commuting.apply(lambda row: float(str(row['Workers 16 and Over']).replace(',',"")), axis=1)
workersByWorkPlace=commuting.groupby('WORKPLACE').sum()

############################################ Basic properties of each geoid  ############################################

geoIdList=[g for g in geoId2puma]
geoIdAttributes={geoIdList[i]:{} for i in range(len(geoIdList))}
geoidOrderGeojson=[geoIdGeo['features'][i]['properties']['GEOID10'] for i in range(len(geoIdGeo['features']))]

count=0
for geoId in geoIdAttributes:
    count+=1
    if str(geoId) in geoidOrderGeojson:
        ind=geoidOrderGeojson.index(geoId)
        geoIdName=geoIdGeo['features'][ind]['properties']['NAMELSAD10']
        try:
            totalWorkers=workersByWorkPlace.loc[geoIdName]['Workers 16 and Over']
        except:
            print(geoIdName+' Area not in commuting data')
            totalWorkers=0
        props=geoIdGeo['features'][ind]['properties']
        geoidShape=shape(geoIdGeo['features'][ind]['geometry']) #get rectangular bounds as they are needed for OSM
#        amenities=getOsmAmenities(geoidShape)
        geoIdAttributes[geoId]={'landArea': props['ALAND10'],
                    'waterArea': props['AWATER10'],                    
                    'housingDensity': housingUnits.loc[int(geoId)][2],
                    'employment': totalWorkers                       
                    }
    else:
        print(geoId + ': geoId id not in geojson')


############################################ Accessibility of each geoid ############################################
# for each geoid, find walkable geoIds
# walkable employment for geoid_A = employment in A + employment in geoids walkable from A

# to cut down on requests to the directions API, check the straight line distance first
maxStraightLineDist=0.3*4800
for geoId in geoIdList: 
    print(geoId)
    ind=geoidOrderGeojson.index(geoId)
    geoIdAttributes[geoId]['accessibleGeoids']=[]
    geoIdAttributes[geoId]['accessibleEmployment']=geoIdAttributes[geoId]['employment']
    geoidShape=shape(geoIdGeo['features'][ind]['geometry'])
    geoidShapeProj = transform(project, geoidShape)  # apply projection
    otherGeo= [g for g in geoIdList if not g==geoId]
    for og in otherGeo:
        indO=geoidOrderGeojson.index(og)
        #in rder to reduce api calls, first check if the straight line distance is within range
        oGeoidShape=shape(geoIdGeo['features'][indO]['geometry'])
        oGeoidShapeProj = transform(project, oGeoidShape)  # apply projection
        dist=geoidShapeProj.centroid.distance(oGeoidShapeProj.centroid)
        if dist<maxStraightLineDist:
            strLL=str(geoidShape.centroid.x) + ','+str(geoidShape.centroid.y)+';'+str(oGeoidShape.centroid.x)+ ','+str(oGeoidShape.centroid.y)
            #with urllib.request.urlopen('http://router.project-osrm.org/route/v1/walking/13.388860,52.517037;13.397634,52.529407;13.428555,52.523219?overview=false') as url:
            try:
                with urllib.request.urlopen('http://router.project-osrm.org/route/v1/walking/'+strLL+'?overview=false') as url:
                    data=json.loads(url.read().decode())
                # if the call request is unsuccessful, wait and try again- usually works
            except:
                print('Sleeping')
                sleep(5)
                with urllib.request.urlopen('http://router.project-osrm.org/route/v1/walking/'+strLL+'?overview=false') as url:
                    data=json.loads(url.read().decode())                    
            if data['routes'][0]['distance']<maxStraightLineDist:
                geoIdAttributes[geoId]['accessibleGeoids'].extend([og])
                geoIdAttributes[geoId]['accessibleEmployment']+=geoIdAttributes[og]['employment']

geoIdGeo_subset=geoIdGeo.copy()
geoIdGeo_subset['features'] = [f for f in geoIdGeo['features'] if f['properties']['GEOID10'] in geoIdAttributes]

pickle.dump(geoIdAttributes, open('./results/geoidAttributes.p', 'wb'))
pickle.dump(geoIdGeo_subset, open('./results/tractsMassSubset.p', 'wb'))
