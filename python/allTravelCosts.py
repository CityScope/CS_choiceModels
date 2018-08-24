#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  2 15:51:25 2018

@author: doorleyr
"""
    
import json 
import pickle
from time import sleep
import urllib.request
from shapely.geometry import shape

###################### Must have a OTP server running locally for this script to work ##################
# http://docs.opentripplanner.org/en/latest/Basic-Tutorial/

def getOSRMDirections(mode, startLat, startLon, endLat, endLon):
    strLL=str(startLon) + ','+str(startLat)+';'+str(endLon)+ ','+str(endLat)
    try:
        with urllib.request.urlopen('http://router.project-osrm.org/route/v1/'+str(mode)+'/'+strLL+'?overview=false') as url:
            data=json.loads(url.read().decode())
            #in meters and seconds
        return data['routes']
        # if the call request is unsuccessful, wait and try again
    except:
        print('Sleeping')
        sleep(10)
        data=getOSRMDirections(mode, startLat, startLon, endLat, endLon)
        return data['routes']
    
def getOTPDirections(startLat, startLon, endLat, endLon, maxWalk, toGeoId):
    # TODO keep a list of geoIds unreachable by transit to avoid repeated checks
    # TODO keep a list of the alternate locations for geoIds where no transit could be found to/from the centroid
    #, but transit could be found from another close location
    
    data=[]
    tries=0
    while tries<8:  
    # if we dont get a route the first time, may because of OTP error- make a small deviation to the start and end points and try again
        strUrl='http://localhost:8080/otp/routers/default/plan?fromPlace='+str(startLat)+','+ str(startLon)+'&toPlace='+str(endLat)+','+ str(endLon)+'&time=9:00am&date=08-02-2018&mode=TRANSIT,WALK&maxWalkDistance='+str(maxWalk)+'&arriveBy=true'
        try:
            with urllib.request.urlopen(strUrl) as url:
                data=json.loads(url.read().decode())
                #in meters and seconds
            return data['plan']['itineraries'][0]
        except:
            tries+=1
            startLat+=0.001
            startLon+=0.001
            endLat+=0.001
            endLon+=0.001
    print('Found no transit to '+str(toGeoId))
    return []
    
walkSpeed_mps=4/3.6 # convert 4km/hr to m/s
cycleSpeed_mps=12/3.6
maxWalk=1500 # meters

geoIdGeo=json.load(open('./data/tractsMass.geojson'))
geoId2puma=pickle.load(open('./results/tract2puma.p', 'rb'))
geoIdList=[g for g in geoId2puma]

# get the centroid of each geoId
geoidOrderGeojson=[geoIdGeo['features'][i]['properties']['GEOID10'] for i in range(len(geoIdGeo['features']))]
geoidCentroids={}
for geoId in geoIdList:
    ind=geoidOrderGeojson.index(geoId)
    c=shape(geoIdGeo['features'][ind]['geometry']).centroid
    geoidCentroids[geoId]={'lat':c.y, 'lon':c.x}
    


travelCosts={fromGeoId:{toGeoId:{} for toGeoId in geoIdList} for fromGeoId in geoIdList}

for fromGeoId in geoIdList:
    print(fromGeoId)
    for toGeoId in geoIdList:
        travelCosts[fromGeoId][toGeoId] ={'drive': {'time':0, 'distance':0},
        'walk': {'time':0, 'distance':0},
        'cycle': {'time':0, 'distance':0},
        'transit': {'walkTime':0, 'waitingTime':0, 'transitTime':0, 'transfers':0}}
        if not fromGeoId==toGeoId:
            #get driving directions
            startLat, startLon, endLat, endLon=[geoidCentroids[fromGeoId]['lat'], geoidCentroids[fromGeoId]['lon'],
                                                geoidCentroids[toGeoId]['lat'], geoidCentroids[toGeoId]['lon']]
            driveData=getOSRMDirections('driving', startLat, startLon, endLat, endLon)
            travelCosts[fromGeoId][toGeoId]['drive']['distance']=driveData[0]['distance']
            travelCosts[fromGeoId][toGeoId]['drive']['time']=driveData[0]['duration']
            # TODO find a better service for walking and cycling directions
            # get walking directions
            travelCosts[fromGeoId][toGeoId]['walk']['distance']=driveData[0]['distance']
            travelCosts[fromGeoId][toGeoId]['walk']['time']=driveData[0]['distance']/walkSpeed_mps
            # get cycling directions
            travelCosts[fromGeoId][toGeoId]['cycle']['distance']=driveData[0]['distance']
            travelCosts[fromGeoId][toGeoId]['cycle']['time']=driveData[0]['distance']/cycleSpeed_mps
             get transit directions
            transitData=getOTPDirections(startLat, startLon, endLat, endLon, maxWalk, toGeoId)
            for te in ['walkTime', 'waitingTime', 'transitTime', 'transfers']:
                if transitData:
                    travelCosts[fromGeoId][toGeoId]['transit'][te]=transitData[te]
                else:
                    travelCosts[fromGeoId][toGeoId]['transit'][te]=float('nan')
    pickle.dump(travelCosts, open('./results/tractTravelCosts.p', 'wb'))