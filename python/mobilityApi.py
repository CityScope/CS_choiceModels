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
from flask_cors import CORS
import logging
import numpy as np

def healthImpacts(refRR, refMets, addMets, baseMR, minRR, N):
    RR=refRR*(addMets/refMets)
    RR=min(RR, minRR)
    deltaF=(1-RR)*N*baseMR
    return deltaF

def allImpacts(longSimPop, len_orig):
    longSimPopDrive=longSimPop[longSimPop['mode_id']==0]
    longSimPopCycle=longSimPop[longSimPop['mode_id']==1]
    longSimPopWalk=longSimPop[(longSimPop['mode_id']==2)|(longSimPop['mode_id']==3)]
    longSimPopPT=longSimPop[longSimPop['mode_id']==3]
    co2Drive=co2EmmissionsDrivePerM*sampleMultiplier*  np.dot(np.array(longSimPopDrive['dist_drive']), np.array(longSimPopDrive['P']))
    co2PT=co2EmmissionsPTPerM*sampleMultiplier*  np.dot(np.array(longSimPopPT['dist_drive']), np.array(longSimPopPT['P']))
    N=len(longSimPop)/4
#    avgCycleTimePerWeek=sum(longSimPopCycle.apply(lambda row: row['cycle_time']*10/60 * row['P'], axis=1))/N
#    avgWalkTimePerWeek=sum(longSimPopWalk.apply(lambda row: row['walk_time']*10/60 * row['P'], axis=1))/N
    avgCycleTimePerWeek=10/60 *sum(np.multiply(np.array(longSimPopCycle['cycle_time']), np.array(longSimPopCycle['P'])))/N
    avgWalkTimePerWeek=10/60 *sum(np.multiply(np.array(longSimPopWalk['walk_time']), np.array(longSimPopWalk['P'])))/N
    deltaF_cycle=sampleMultiplier*healthImpacts(RR_cycle, refMinsPerWeek_cycle, avgCycleTimePerWeek, baseMR, minRR_cycle, N)*len(longSimPop)/len_orig
    deltaF_walk=sampleMultiplier*healthImpacts(RR_walk, refMinsPerWeek_walk, avgWalkTimePerWeek, baseMR, minRR_walk, N)*len(longSimPop)/len_orig
    co2=co2Drive+co2PT * 2 * 221 # work trips per year
    return {'avoided_mortality_walking':deltaF_walk, 'avoided_mortality_cycling':deltaF_cycle, 'CO2_emissions_year[tonnes]': co2}
    

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

logging.basicConfig(filename='./logs/'+datetime.datetime.now().strftime("%Y%d%m_%H%M%S" )+'.log',level=logging.DEBUG)

#Define some constants
POOL_TIME = 1 #Seconds
utm19N=pyproj.Proj("+init=EPSG:32619")
wgs84=pyproj.Proj("+init=EPSG:4326")
host='https://cityio.media.mit.edu/'
#host='http://localhost:8080/' # local port running cityio
cityIO_url='{}api/table/CityScopeJS'.format(host)
sampleMultiplier=int(1/(0.05*0.35)) # PUMS sampling * my subsampling
peoplePerFloor=50

#Health Impact Assessment parameters
baseMR= 0.0090421
RR_cycle=0.9
RR_walk=0.89
refMinsPerWeek_cycle=100
refMinsPerWeek_walk=168
minRR_walk=0.7
minRR_cycle=0.55
co2EmmissionsDrivePerM= 0.8708/(0.00162*2000) #from lbs/mile to US tonnes/m
co2EmmissionsPTPerM= 0.2359/(0.00162*2000)  #from lbs/mile to US tonnes/m
#scc=42*1.21  # correcting the 2007 dollars to 2018 dollars
## https://19january2017snapshot.epa.gov/climatechange/social-cost-carbon_.html
#vsl=9e6 
## https://www.nytimes.com/2011/02/17/business/economy/17regulation.html?_r=0&pagewanted=all


LU_types=["LIVE_1", "LIVE_2", "WORK_1", "WORK_2"] # the LU types we are interested in

lu_changes={}
landAreas={}
altRes={}
sliderHeights={lu:1 for lu in LU_types}

# TODO Dont use a constant here
topLeft_lonLat={'lat':42.367867,   'lon':  -71.087913}
topEdge_lonLat={'lat':42.367255,   'lon':  -71.083231}# Kendall Volpe area

# load the precalibrated models and data
geoIdAttributes=pickle.load( open( "./results/geoidAttributes.p", "rb" ) )
geoIdGeo_subset=pickle.load( open( "./results/tractsMassSubset.p", "rb" ) )
simPop_mnl=pickle.load( open('./results/simPop_mnl.p', 'rb'))
longSimPop=pickle.load( open('./results/longSimPop.p', 'rb'))


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
longSimPop['P']=simPop_mnl.predict(longSimPop)
longSimPop_combined=longSimPop.copy()
newPeople=pd.DataFrame(columns=longSimPop.columns)

lastId='0'
lastTimestamp=0
spatialData=[]
revTypeMap=[]
sliderMap=[]
interactionZones=[]
grid2Geo=[]
baselineImpacts={}


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
        global lastTimestamp
        global longSimPop
        global longSimPop_combined
        global newPeople
        global spatialData
        global revTypeMap
        global sliderMap
        global interactionZones
        global grid2Geo
        global altRes
        with dataLock:
            try:
                with urllib.request.urlopen(cityIO_url) as url:
                    #get the latest json data
                    cityIO_data=json.loads(url.read().decode())
                if spatialData:
                    pass
                else:
                    # if this is the first time the grid data has been retrived, need to set up the grid spatially
                    spatialData=cityIO_data['header']['spatial']
                    typeMap=cityIO_data['header']['mapping']['type']
                    revTypeMap={v:int(k) for k,v in typeMap.items()}
                    #create the slider
                    slider=cityIO_data['objects']['sliders'][0]
                    sliderRange=list(reversed(range(slider['0'], slider['1']+1, spatialData['ncols'])))
                    sliderMap={sliderRange[i]:i+1 for i in range(len(sliderRange))}
                    #create the grid
                    lon_grid, lat_grid=createGrid(topLeft_lonLat, topEdge_lonLat, utm19N, wgs84, spatialData)
                    #find the incidency relationship between grid cells and zones
                    iZones=set()
                    grid2Geo={}
                    for i in range(len(lon_grid)):
                        # updating the list of interaction zones found so far to make next search faster- these are checked first
                        grid2Geo[i], iZones =get_geoId(lon_grid[i], lat_grid[i], geoIdGeo_subset, iZones)
                    interactionZones=set([grid2Geo[g] for g in grid2Geo])                   
                    #initialise the changes in land use
                    for iz in interactionZones:
                        lu_changes[iz]={}
                        for lu in LU_types:
                            lu_changes[iz][lu]=0
                            lu_changes[iz][lu+'_last']=0
                        landAreas[iz]=geoIdAttributes[geoIdOrderGeojson[iz]]['landArea']                       
                if cityIO_data['meta']['id']==lastId:
                    pass
                else:
                    logging.info('change at '+str(startBg))
                    lastId=cityIO_data['meta']['id']
                    #find grids of this LU and the add to the corresponding zone
                    for lu in LU_types:
                        lu_gridCells=[g for g in range(len(cityIO_data['grid'])) if cityIO_data['grid'][g] ==revTypeMap[lu]]
                        lu_sliderCells=[g for g in lu_gridCells if g in sliderMap]
                        lu_gridCells=[g for g in lu_gridCells if g not in sliderMap]
                        if lu_sliderCells:
                            sliderValue=sliderMap[lu_sliderCells[-1]] # in case there are ever more than 1, take the higher one
#                            print(lu+': '+str(sliderValue))
                            sliderHeights[lu]=sliderValue
                        lu_zones=[grid2Geo[gc] for gc in lu_gridCells]
                        for iz in interactionZones:
                            lu_changes[iz][lu]=sum([sliderHeights[lu] for luz in lu_zones if luz==iz])
                     # for each interaction zone, for rows in simPop with home in this zone
                    for iz in interactionZones:                
                        # update lwBalance home and pow
                        o_increase=peoplePerFloor*(lu_changes[iz]['WORK_1']-lu_changes[iz]['WORK_1_last'])+2*peoplePerFloor*(lu_changes[iz]['WORK_2']-lu_changes[iz]['WORK_2_last'])
                        r_increase=peoplePerFloor*(lu_changes[iz]['LIVE_1']-lu_changes[iz]['LIVE_1_last'])+2*peoplePerFloor*(lu_changes[iz]['LIVE_2']-lu_changes[iz]['LIVE_2_last'])
                        newODensity=longSimPop.loc[longSimPop['o']==iz].iloc[0]['employmentDensity_home']+o_increase/landAreas[iz]
                        newRDensity=longSimPop.loc[longSimPop['o']==iz].iloc[0]['residentialDensity_home']+r_increase/landAreas[iz]
                        newLWBalance=-abs((newRDensity-newODensity))/(4*(newRDensity+newODensity))
                        longSimPop.loc[longSimPop['o']==iz, 'employmentDensity_home']=newODensity
                        longSimPop.loc[longSimPop['d']==iz, 'employmentDensity_pow']=newODensity
                        longSimPop.loc[longSimPop['o']==iz, 'residentialDensity_home']=newRDensity
                        longSimPop.loc[longSimPop['d']==iz, 'residentialDensity_pow']=newRDensity
                        longSimPop.loc[longSimPop['o']==iz, 'lwBalance_home']=newLWBalance
                        longSimPop.loc[longSimPop['d']==iz, 'lwBalance_pow']=newLWBalance
#                        sampleWorkerIncrease=round(o_increase/sampleMultiplier)
#                        sampleHousingIncrease=round(r_increase/sampleMultiplier)
                        employmentSampleIZ=round(peoplePerFloor*(lu_changes[iz]['WORK_1']+2*lu_changes[iz]['WORK_2'])/sampleMultiplier)
                        housingSampleIZ=round(peoplePerFloor*(lu_changes[iz]['LIVE_1']+2*lu_changes[iz]['LIVE_2'])/sampleMultiplier)
                        # for N workers in iz, sample workers from with work zone ==iz  with replacement:
                        candidates=set(longSimPop[longSimPop['d']==iz]['custom_id'].values) #candidates for cloning
                        newPeople=pd.DataFrame()
                        for i in range(employmentSampleIZ):
                            newPeople=newPeople.append(longSimPop[longSimPop['custom_id']==random.sample(candidates,1)])
                        # if workers>residences, assign first M to IZ
                        if not newPeople.empty:
                            newPeople.o.iloc[0:4*min(housingSampleIZ,employmentSampleIZ)]=iz
#                            TODO: calculate costs properly
                            newPeople.vehicle_time.iloc[0:4*min(housingSampleIZ,employmentSampleIZ)]=0
                            newPeople.cycle_time.iloc[0:4*min(housingSampleIZ,employmentSampleIZ)]=0
                            newPeople.walk_time.iloc[0:4*min(housingSampleIZ,employmentSampleIZ)]=0
                        # if residences>workers, assign all new worker to live in IZ
                        # and clone new people with home in iz
                        if housingSampleIZ>employmentSampleIZ:
                            candidates=set(longSimPop[longSimPop['o']==iz]['custom_id'].values) #candidates for cloning
                            for i in range(housingSampleIZ-employmentSampleIZ):
                                newPeople=newPeople.append(longSimPop[longSimPop['custom_id']==random.sample(candidates,1)])
                        newPeople['custom_id']=[longSimPop.iloc[len(longSimPop)-1]['custom_id']+1+i for i in range(max(housingSampleIZ,employmentSampleIZ)) for j in range(4)]
                        if newPeople.empty:
                            longSimPop_combined=longSimPop
                        else:
                            longSimPop_combined=longSimPop.append(newPeople, sort=False).reset_index(drop=True)                                    
                        for lu in LU_types:
                            lu_changes[iz][lu+'_last']=lu_changes[iz][lu]
                    longSimPop_combined['P']=simPop_mnl.predict(longSimPop_combined)
                    print('Living in IZ: ' + str(sum(longSimPop_combined['o']==193)/4))
                    print('Working in IZ: ' + str(sum(longSimPop_combined['d']==193)/4))
                    print('updating ts')
                    lastTimestamp=cityIO_data['meta']['timestamp']
                    logging.info('BG thread took: '+str(((datetime.datetime.now()-startBg).microseconds)/1e6)+' seconds')
            except urllib.error.HTTPError:
                print("HTTP error when getting cityIO updates")
        yourThread = threading.Timer(POOL_TIME, background, args=())
        yourThread.start()        

    def initialise():
        # Perform initial data processing
        global baselineImpacts
        baselineImpacts=allImpacts(longSimPop_combined, len(longSimPop))
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
CORS(app)

@app.route('/choiceModels/volpe', methods=['GET'])
def return_versions():
    return jsonify({'Version 1.0': '/choiceModels/volpe/v1.0'})

@app.route('/choiceModels/volpe/v1.0', methods=['GET'])
def return_endPoints():
    return jsonify({'get O-D matrix': '/choiceModels/volpe/v1.0/od',
                    'get agents': '/choiceModels/volpe/v1.0/agents',
                    'get geojson of regions': '/choiceModels/volpe/v1.0/geo',
                    'get health and environmental impacts': '/choiceModels/volpe/v1.0/impacts'})

@app.route('/choiceModels/volpe/v1.0/od', methods=['GET'])
def get_od():
    # return a cross-tabulation of trips oriented by origin
#    logging.info('Received O-D request.')
    ct = longSimPop_combined.groupby(['o', 'd', 'mode_id'], as_index=False).P.sum()
    ct['P']=ct.apply(lambda row: row['P']*sampleMultiplier, axis=1)
    ct=ct.rename(columns={"mode_id": "m"})
#    byOrigin=ct.groupby(['o', 'm'], as_index=False).P.sum()
#    originJson='['+",".join([byOrigin.loc[ct['o']==o].to_json(orient='records') for o in range(len(geoIdOrderGeojson))])+']'
    ct=ct.loc[ct['P']>1]
    ct['P']=ct['P'].astype('int')
    print('Received O-D request')
    print('Drive: '+str(sum(ct.loc[((ct['d']==193)  &(ct['m']==0)),'P'])))
    print('Cycle: '+str(sum(ct.loc[((ct['d']==193) &(ct['m']==1)),'P'])))
    print('Walk: '+str(sum(ct.loc[((ct['d']==193) &(ct['m']==2)),'P'])))
    print('PT: '+str(sum(ct.loc[((ct['d']==193) &(ct['m']==3)),'P'])))
#    Excluding internal trips
#    print('Drive: '+str(sum(ct.loc[((ct['d']==193) &(ct['o']!=193) &(ct['m']==0)),'P'])))
#    print('Cycle: '+str(sum(ct.loc[((ct['d']==193) &(ct['o']!=193)&(ct['m']==1)),'P'])))
#    print('Walk: '+str(sum(ct.loc[((ct['d']==193) &(ct['o']!=193)&(ct['m']==2)),'P'])))
#    print('PT: '+str(sum(ct.loc[((ct['d']==193) &(ct['o']!=193)&(ct['m']==3)),'P'])))
    return '['+",".join([ct.loc[ct['o']==o].to_json(orient='records') for o in range(len(geoIdOrderGeojson))])+']'
#    return "{"+",".join('"'+str(o)+'":'+ct.loc[ct['o']==o, ['d', 'm', 'P']].to_json(orient='records') for o in range(len(geoId2Int)))+"}"
#    return '{"OD": '+odJson+', "origins": '+originJson+'}'

@app.route('/choiceModels/volpe/v1.0/one_od/<int:zone_id>', methods=['GET'])
def get_od1(zone_id):
    longSimPop_zone=longSimPop_combined[longSimPop_combined['d']==zone_id]
    ct = longSimPop_zone.groupby(['o', 'd', 'mode_id'], as_index=False).P.sum()
    ct['P']=ct.apply(lambda row: row['P']*sampleMultiplier, axis=1)
    ct=ct.rename(columns={"mode_id": "m"})
#    byOrigin=ct.groupby(['o', 'm'], as_index=False).P.sum()
#    originJson='['+",".join([byOrigin.loc[ct['o']==o].to_json(orient='records') for o in range(len(geoIdOrderGeojson))])+']'
    ct=ct.loc[ct['P']>1]
    ct['P']=ct['P'].astype('int')
    return ct.to_json(orient='records')

@app.route('/choiceModels/volpe/v1.0/agents', methods=['GET'])    
def get_agents():
#    logging.info('Received agents request.')
    random.seed(0)
    # return a cross-tabulation oriented by agents
    if len(newPeople)>0:
        ct = newPeople.groupby(['o', 'd', 'profile','mode_id'], as_index=False).P.sum()
        ct['P']=ct.apply(lambda row: row['P']*sampleMultiplier/10, axis=1)
#        ct['P']=[int(p)+(random.random()<(p-int(p))) for p in ct['P']] #probabilistic round-up so no fractions of people
        ct['P']=ct.apply(lambda row: int(row['P']), axis=1) #simpler than above and ok for larger numbers
        ct=ct.loc[ct['P']>0]
        print('Num Agents: '+str(sum(ct.P)))
        ct=ct.rename(columns={"mode_id": "m", "profile": "pr"})
        return ct.to_json(orient='records')
    else:
        return '[]'

@app.route('/choiceModels/volpe/v1.0/geo', methods=['GET'])
def get_geo():
#    logging.info('Received geo request.')
    #return the subsetted geojson data
    return jsonify(geoIdGeo_subset)

@app.route('/choiceModels/volpe/v1.0/impacts', methods=['GET'])
def get_impacts():   
#    deltaF_cycle=sum(longSimPop.apply(lambda row: healthImpacts(RR_cycle, refMinsPerWeek_cycle, row['cycle_time']*10/60, baseMR, minRR_cycle, 1)*row['P'], axis=1))
    impacts=allImpacts(longSimPop_combined, len(longSimPop))
    return jsonify({'current':impacts, 'baseline':baselineImpacts})

@app.route('/choiceModels/volpe/v1.0/ts', methods=['GET'])
def get_ts():
    tsObj={'Last timestamp from grid: ': datetime.datetime.fromtimestamp(int(lastTimestamp/1000)).isoformat(), 'ts': lastTimestamp}
    return jsonify(tsObj)

@app.errorhandler(404)
# standard error is html message- we need to ensure that the response is always json
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(port=3030, debug=False, use_reloader=False, threaded=True)
    # if reloader is True, it starts the background thread twice

