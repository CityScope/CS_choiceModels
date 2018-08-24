#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 16 14:50:11 2018

@author: doorleyr
"""

#!flask/bin/python
from flask import Flask, jsonify, make_response
import threading
import atexit
import pickle
import json
import random
import urllib
import pyproj
import math
from shapely.geometry import Point, shape
import datetime
import pandas as pd


def createGrid(topLeft_lonLat, topEdge_lonLat, utm19N, wgs84, spatialData):
    #retuns the top left coordinate of each grid cell from left to right, top to bottom
    topLeftXY=pyproj.transform(wgs84, utm19N,topLeft_lonLat['lon'], topLeft_lonLat['lat'])
    topEdgeXY=pyproj.transform(wgs84, utm19N,topEdge_lonLat['lon'], topEdge_lonLat['lat'])
    dydx=(topEdgeXY[1]-topLeftXY[1])/(topEdgeXY[0]-topLeftXY[0])
    theta=math.atan((dydx))
    cosTheta=math.cos(theta)
    sinTheta=math.sin(theta)
    x_unRot=[j*spatialData['cellSize'] for i in range(spatialData['nrows']) for j in range(spatialData['ncols'])]
    y_unRot=[-i*spatialData['cellSize'] for i in range(spatialData['nrows']) for j in range(spatialData['ncols'])]
    # use the rotation matrix to rotate around the origin
    x_rot=[x_unRot[i]*cosTheta -y_unRot[i]*sinTheta for i in range(len(x_unRot))]
    y_rot=[x_unRot[i]*sinTheta +y_unRot[i]*cosTheta for i in range(len(x_unRot))]
    x_rot_trans=[topLeftXY[0]+x_rot[i] for i in range(len(x_rot))]
    y_rot_trans=[topLeftXY[1]+y_rot[i] for i in range(len(x_rot))]
    lon_grid, lat_grid=pyproj.transform(utm19N,wgs84,x_rot_trans, y_rot_trans)
    return lon_grid, lat_grid

def get_geoId(longitude, latitude, regions_json, iZones):
    # takes a point and returns the index of the containing geoId
    # Since there will be a small number of zones containing all the grid cells
    # we should first check the zones already identified
    point = Point(longitude, latitude)
    for iz in iZones:
        polygon = shape(regions_json['features'][iz]['geometry'])
        if polygon.contains(point):
            return iz, iZones
    for r in range(len(regions_json['features'])):
        polygon = shape(regions_json['features'][r]['geometry'])
        if polygon.contains(point):
            iZones.add(r)
            return r, iZones
    return float('nan')

#Define some constants
POOL_TIME = 1 #Seconds
utm19N=pyproj.Proj("+init=EPSG:32619")
wgs84=pyproj.Proj("+init=EPSG:4326")
cityIO_url='https://cityio.media.mit.edu/api/table/cityscopeJSwalk'
sampleMultiplier=20 # each person in PUMS corresponds to about 20 actual people

LU_types=['L', 'W'] # the LU types we are interested in

# TODO Dont use a constant here
topLeft_lonLat={'lat':42.367867,   'lon':  -71.087913}
topEdge_lonLat={'lat':42.367255,   'lon':  -71.083231}# Kendall Volpe area

# load the precalibrated models and data
geoIdAttributes=pickle.load( open( "./results/geoidAttributes.p", "rb" ) )
geoIdGeo_subset=pickle.load( open( "./results/tractsMassSubset.p", "rb" ) )
simPop_mnl=pickle.load( open('./results/simPop_mnl.p', 'rb'))
longSimPop=pickle.load( open('./results/longSimPop.p', 'rb'))
#simPop_mnl=pd.read_pickle('./results/simPop_mnl.p')
#longSimPop=pd.read_pickle('./results/longSimPop.p')
print(len(longSimPop)/4)

#add centroids
for f in geoIdGeo_subset['features']:
    c=shape(f['geometry']).centroid
    f['properties']['centroid']=[c.x, c.y]
#get the ordering of the geoIds in the geojson
geoIdOrderGeojson=[f['properties']['GEOID10'] for f in geoIdGeo_subset['features']]
# in longSimPop, replace all geoIDs with ints
geoId2Int={g:int(geoIdOrderGeojson.index(g)) for g in geoIdAttributes}
longSimPop['o']=longSimPop.apply(lambda row: geoId2Int[row['homeGEOID']], axis=1).astype(object)
longSimPop['d']=longSimPop.apply(lambda row: geoId2Int[row['workGEOID']], axis=1).astype(object)

# Get the initial cityIO data from the API
with urllib.request.urlopen(cityIO_url) as url:
    cityIO_data=json.loads(url.read().decode()) 

lastId='0'
spatialData=cityIO_data['header']['spatial']
typeMap=cityIO_data['header']['mapping']['type']
revTypeMap={v:int(k) for k,v in typeMap.items()}
#create the grid
lon_grid, lat_grid=createGrid(topLeft_lonLat, topEdge_lonLat, utm19N, wgs84, spatialData)
#find the incidency relationship between grid cells and zones
iZones=set()
grid2Geo={}
for i in range(len(lon_grid)):
    # updating the list of interaction zones found so far to make next search faster- these are checked first
    grid2Geo[i], iZones =get_geoId(lon_grid[i], lat_grid[i], geoIdGeo_subset, iZones)
interactionZones=set([grid2Geo[g] for g in grid2Geo])

lu_changes={}
#initialise the changes in land use
for iz in interactionZones:
    lu_changes[iz]={}
    for lu in LU_types:
        lu_changes[iz][lu]=0
        lu_changes[iz][lu+'_last']=0
    
# lock to control access to variable
dataLock = threading.Lock()
# thread handler
yourThread = threading.Thread()

def create_app():
    app = Flask(__name__)

    def interrupt():
        global yourThread
        yourThread.cancel()

    def background():
        startBg=datetime.datetime.now()
        global yourThread
        global lastId
        global longSimPop
        with dataLock:
            with urllib.request.urlopen(cityIO_url) as url:
                #get the latest json data
                try:
                    cityIO_data=json.loads(url.read().decode())
                except:
                    print("Couldn't get cityIO updates")
            if cityIO_data['meta']['id']==lastId:
                pass
            else:
                print('change')
                lastId=cityIO_data['meta']['id']
                #find grids of this LU and the add to the corresponding zone
                for lu in LU_types:
                    lu_gridCells=[g for g in range(len(cityIO_data['grid'])) if cityIO_data['grid'][g] ==revTypeMap[lu]]
                    lu_zones=[grid2Geo[gc] for gc in lu_gridCells]
                    for iz in interactionZones:
                        lu_changes[iz][lu]=sum([100 for luz in lu_zones if luz==iz])
                 # for each interaction zone, for rows in simPop with home in this zone
                for iz in interactionZones:                
                    # TODO update accessible zones too
                    o_increase=lu_changes[iz]['W']-lu_changes[iz]['W_last']
                    r_increase=lu_changes[iz]['L']-lu_changes[iz]['L_last']
                    longSimPop.loc[longSimPop['o']==iz, 'housingDensity']+=r_increase
                    longSimPop.loc[longSimPop['o']==iz, 'accessibleEmployment']+=o_increase
                    longSimPop.loc[longSimPop['d']==iz, 'employmentDensity']+=o_increase
                    sampleWorkerIncrease=o_increase//sampleMultiplier
                    sampleHousingIncrease=r_increase//sampleMultiplier
                    # add new people for new employment capacity
                        # if N>0, randomly duplictae N rows in longSimPop with workplace of iz- add to END
                        # if N<0, delete LAST with this iz
                    if sampleWorkerIncrease>0:
#                        print('O increased')
                        candidates=set(longSimPop[longSimPop['d']==iz]['custom_id'].values)
                        newPeople=pd.DataFrame()
                        for i in range(sampleWorkerIncrease):
                            newPeople=newPeople.append(longSimPop[longSimPop['custom_id']==random.sample(candidates,1)])
                        newPeople['custom_id']=[longSimPop.iloc[len(longSimPop)-1]['custom_id']+1+i for i in range(sampleWorkerIncrease) for j in range(4)]
                            # new person ids
                        longSimPop=longSimPop.append(newPeople).reset_index(drop=True)
                    elif sampleWorkerIncrease<0:
#                        print('O decreased')
                        candidates=set(longSimPop[longSimPop['d']==iz]['custom_id'].values)
                        killList=random.sample(candidates,-sampleWorkerIncrease)
                        longSimPop=longSimPop[~longSimPop['custom_id'].isin(killList)].reset_index(drop=True)                    
                    # redistribute people based on res capacity
                    if sampleHousingIncrease>0:
#                        print('R increased')
                        # find candidate who lives in iz, copy their work location and all home and commute data
                        # find someone who doesnt live in iz but works in the same place as the candidate. update their home and commute variables
                        # this ensures the probability of a person to be selected for moving here is in proportion to their liklihood of living here- given their workplace
                        candidatesDf=longSimPop.loc[longSimPop['o']==iz]
                        for i in range(sampleHousingIncrease):
                            candidateDf=candidatesDf[candidatesDf['custom_id']==candidatesDf['custom_id'].sample(n=1).values[0]]
                            mover=longSimPop.loc[(longSimPop['d']==candidateDf.iloc[0]['d']) & (longSimPop['o']!=iz)]['custom_id'].sample(n=1).values[0]
                            mask=longSimPop['custom_id']==mover
                            # TODO income normalisation of cost
                            for col in ['accessibleEmployment', 'housingDensity', 'homeGEOID', 'cycle_time','cost_by_personalIncome', 'vehicle_time', 'wait_time', 'walk_time', 'o']:
                                longSimPop.loc[mask, col]=candidateDf[col].values                       
                    elif sampleHousingIncrease<0:
#                        print('R decreased')
                        #find list of possible movers that live in iz
                        possibleMovers=longSimPop.loc[(longSimPop['o']==iz)]['custom_id'].tolist()
                        movers=random.sample(possibleMovers, -sampleHousingIncrease)
                        for i in range(-sampleHousingIncrease):
                            #pick  a mover from the list
                            mover=movers[i]
                            # find someone else who works in same place as mover but doesnt live in iz
                            # eensures that the probability of a location being picked as the new home location is in proportion to the lilihood someone living there given- their workplace
                            candidatesDf=longSimPop.loc[(longSimPop['o']!=iz)&(longSimPop['d']==longSimPop.loc[longSimPop['custom_id']==mover]['d'].tolist()[0])]
                            candidateDf=candidatesDf[candidatesDf['custom_id']==candidatesDf['custom_id'].sample(n=1).values[0]]
                            #copy other persons details to the mover
                            mask=longSimPop['custom_id']==mover
                            for col in ['accessibleEmployment', 'housingDensity', 'homeGEOID', 'cycle_time','cost_by_personalIncome', 'vehicle_time', 'wait_time', 'walk_time', 'o']:
                                longSimPop.loc[mask, col]=candidateDf[col].values                            
                    for lu in LU_types:
                        lu_changes[iz][lu+'_last']=lu_changes[iz][lu]
                longSimPop['P']=simPop_mnl.predict(longSimPop)
                print(len(longSimPop)/4)
                print('BG thread took: '+str(((datetime.datetime.now()-startBg).microseconds)/1e6)+' seconds')
        yourThread = threading.Timer(POOL_TIME, background, args=())
        yourThread.start()        

    def initialise():
        # Perform initial data processing
        longSimPop['P']=simPop_mnl.predict(longSimPop)
        global yourThread
        # Create the initial background thread
        yourThread = threading.Timer(POOL_TIME, background, args=())
        yourThread.start()

    # Initiate
    initialise()
    # When you kill Flask (SIGTERM), clear the trigger for the next thread
    atexit.register(interrupt)
    return app

app = create_app()

@app.route('/choiceModels/volpe', methods=['GET'])
def return_versions():
    return jsonify({'Version 1.0': '/choiceModels/volpe/v1.0'})

@app.route('/choiceModels/volpe/v1.0', methods=['GET'])
def return_endPoints():
    return jsonify({'get O-D matrix': '/choiceModels/volpe/v1.0/od',
                    'get agents': '/choiceModels/volpe/v1.0/agents',
                    'get geojson of regions': '/choiceModels/volpe/v1.0/geo'})

@app.route('/choiceModels/volpe/v1.0/od', methods=['GET'])
def get_od():
    # return a cross-tabulation of trips oriented by origin
    ct = longSimPop.groupby(['o', 'd', 'mode_id'], as_index=False).P.sum()
    ct=ct.loc[ct['P']>0.5]
    ct['P']=ct['P'].round(2)
    ct=ct.rename(columns={"mode_id": "m"})
    return '['+",".join([ct.loc[ct['o']==o].to_json(orient='records') for o in range(len(geoIdOrderGeojson))])+']'

@app.route('/choiceModels/volpe/v1.0/agents', methods=['GET'])    
def get_agents():
    random.seed(0)
    # return a cross-tabulation oriented by agents
    ct = longSimPop.groupby(['o', 'd', 'ageQ3','mode_id'], as_index=False).P.sum()
    ct['P']=[int(p)+(random.random()<(p-int(p))) for p in ct['P']] #probabilistic round-up so no fractions of people
    ct=ct.loc[ct['P']>0]
    ct=ct.rename(columns={"mode_id": "m", "ageQ3": "a"})
    return ct.to_json(orient='records')
    print(len(ct.loc[ct['d']==193]))

@app.route('/choiceModels/volpe/v1.0/geo', methods=['GET'])
def get_geo():
    #return the subsetted geojson data
    return jsonify(geoIdGeo_subset)

@app.errorhandler(404)
# standard error is html message- we need to ensure that the response is always json
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(port=3030, debug=False, use_reloader=False, threaded=True)
    # if reloader is Trye, it starts the background thread twice
    
#test=[ct.loc[ct['o']==o].to_json(orient='records') for o in range(417)]    
