#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 10 13:29:11 2018

@author: doorleyr
"""                   # For file input/output
import json  
import os                 # For vectorized math operations
import pickle
import urllib.request
from shapely.geometry import shape

tags={
      'food': ['amenity_restaurant', 'amenity_cafe' 'amenity_fast_food', 'amenity_pub'],
      'nightlife': ['amenity_bar' , 'amenity_pub' , 'amenity_nightclub', 'amenity_biergarten'],  #(according to OSM, pubs may provide food, bars dont)
      'groceries': ['shop_convenience', 'shop_grocer', 'shop_greengrocer', 'shop_food', 'shop_supermarket'], 
#      'education': ['amenity_school', 'amenity_university', 'amenity_college']
      }


os.chdir('..')
geoIdGeo_subset=pickle.load( open( "./results/tractsMassSubset.p", "rb" ) )

# get vounds of entire region
GBAarea=[shape(f['geometry']) for f in geoIdGeo_subset['features']]
bounds=[shp.bounds for shp in GBAarea]
boundsAll=[min([b[0] for b in bounds]), #W
               min([b[1] for b in bounds]), #S
               max([b[2] for b in bounds]), #E
               max([b[3] for b in bounds])] #N
# To get all amenity data
strBounds=str(boundsAll[0])+','+str(boundsAll[1])+','+str(boundsAll[2])+','+str(boundsAll[3])
boxOsmUrl='https://lz4.overpass-api.de/api/interpreter?data=[out:json][bbox];node[~"^(amenity|leisure|shop)$"~"."];out;&bbox='+strBounds
with urllib.request.urlopen(boxOsmUrl) as url:
    data=json.loads(url.read().decode())
    
features=[]
for a in range(len(data['elements'])):
    include=0
    for t in tags:
        data['elements'][a][t]=0
        for recordTag in list(data['elements'][a]['tags'].items()):
            if recordTag[0] +'_'+recordTag[1] in tags[t]:
                data['elements'][a][t]=1
                include=1
    if include==1:
        feature={"type": "Feature",
                 "geometry": {"type": "Point","coordinates": [data['elements'][a]['lon'], data['elements'][a]['lat']]},
                 "properties": {t: data['elements'][a][t] for t in tags}}
        feature["properties"]['osm_id']=data['elements'][a]['id']
        features.append(feature)
geoDict={"crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
         "type": "FeatureCollection","features":features} 
os.chdir('..')
json.dump(geoDict, open('ABM/includes/amenitiesGBA.geojson', "w"))