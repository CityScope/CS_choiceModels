#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 15 11:00:58 2018
Creates a csv with a sample of agents to use for the baseline population in the GAMA simulation
@author: doorleyr
"""

import pickle
import json
import pandas as pd
import os
os.chdir('..')
modeDict={0:'car', 1:'bike', 2:'walk', 3:'PT'}
N=1000
simPop=pickle.load(open('./results/population.p', 'rb'))
geoIdGeo_subset=pickle.load( open( "./results/tractsMassSubset.p", "rb" ) )
geoIdOrderGeojson=[f['properties']['GEOID10'] for f in geoIdGeo_subset['features']]

geoId2Int={geoIdOrderGeojson[i]:i for i in range(len(geoIdOrderGeojson))}
simPop['o']=simPop.apply(lambda row: geoId2Int[str(int(row['homeGEOID']))], axis=1)
simPop['d']=simPop.apply(lambda row: geoId2Int[str(int(row['workGEOID']))], axis=1)
simPop['mode']=simPop.apply(lambda row:modeDict[row['simpleMode']], axis=1)

simPop=simPop[['o', 'd', 'mode']]
simPopSample=simPop.sample( n=N)

#add simple id to geojson
for i in range(len(geoIdGeo_subset['features'])):
    geoIdGeo_subset['features'][i]['properties']['id']=i

geoIdGeo_subset['crs']['properties']['name']='epsg:4326'
  
os.chdir('..')
simPopSample.to_csv('ABM/includes/agents.csv')
json.dump(geoIdGeo_subset, open('ABM/includes/geoIdsGAMA.geojson', 'w'))