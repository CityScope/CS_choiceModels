#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 14:11:45 2018

Gets all OSM data for the region of interst.
This (along with GTFS files) is required for the OTP server which returns the travel costs

@author: doorleyr



"""
import json
import pickle
import requests
from shapely.geometry import shape

# get the geojson file of all the geoIds
geoIdGeo=json.load(open('./data/tractsMass.geojson'))
# get the pre-prepared dict which relates the included geoIds to PUMAs
geoId2puma=pickle.load(open('./results/tract2puma.p', 'rb'))
#create a list representing the index of each geoId as it appears in the geojson
geoidOrderGeojson=[geoIdGeo['features'][i]['properties']['GEOID10'] for i in range(len(geoIdGeo['features']))]
# get bounds of entire region
inds=[geoidOrderGeojson.index(geoId) for geoId in geoId2puma]
GBAarea=[shape(geoIdGeo['features'][ind]['geometry']) for ind in inds]
bounds=[shp.bounds for shp in GBAarea]
boundsAll=[min([b[0] for b in bounds]), #W
               min([b[1] for b in bounds]), #S
               max([b[2] for b in bounds]), #E
               max([b[3] for b in bounds])] #N

# To get ALL data ( for use by the OTP server)
strBounds=str(boundsAll[1])+','+str(boundsAll[0])+','+str(boundsAll[3])+','+str(boundsAll[2])
boxOsmUrl='http://overpass-api.de/api/interpreter?data=[out:xml];(node('+strBounds+');<;);out meta;'
# should be S, W, N, E
#with urllib.request.urlopen(boxOsmUrl) as urlopen:
#    data=urlopen.read()
response = requests.get(boxOsmUrl)
with open('./results/regionalOSM.xml', 'wb') as file:
    file.write(response.content)