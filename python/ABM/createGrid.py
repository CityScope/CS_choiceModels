#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 18 14:18:52 2018

@author: doorleyr
"""
import pyproj
import math
import numpy as np
import os
import json
import os
os.chdir('..')

topLeft=[42.365971, -71.085612]
topEdge=[42.365261, -71.082828]

gridMeters=100
numCols=2
numRows=2

utm31N=pyproj.Proj("+init=EPSG:25831")
wgs84=pyproj.Proj("+init=EPSG:4326")

topLeftXY=pyproj.transform(wgs84, utm31N, topLeft[1],  topLeft[0])
topEdgeXY=pyproj.transform(wgs84, utm31N, topEdge[1],  topEdge[0])

dydx=(topEdgeXY[1]-topLeftXY[1])/(topEdgeXY[0]-topLeftXY[0])
#dxdy=1/dydx

angle=math.atan((dydx))
xCosA=gridMeters*math.cos(angle)
xSinA=gridMeters*math.sin(angle)

np.sqrt(np.power(xCosA,2)+np.power(xSinA,2))


tlCells=[[[topLeftXY[0] + i*xCosA+j*xSinA, topLeftXY[1] - j*xCosA + i*xSinA] for j in range(numRows)] for i in range(numCols)]
trCells=[[[tlCells[i][j][0]+xCosA, tlCells[i][j][1]+xSinA] for j in range(numRows)] for i in range(numCols)]
blCells=[[[tlCells[i][j][0]+xSinA, tlCells[i][j][1]-xCosA] for j in range(numRows)] for i in range(numCols)]
brCells=[[[trCells[i][j][0]+xSinA, trCells[i][j][1]-xCosA] for j in range(numRows)] for i in range(numCols)]
cellsXY=[]
cellsXY_centroid=[]
cellsLL=[]
for i in range(numCols):
    for j in range(numRows):
        cellXY=[tlCells[i][j], trCells[i][j], brCells[i][j], blCells[i][j], tlCells[i][j]]
        cellLL=[pyproj.transform(utm31N, wgs84, p[0],  p[1]) for p in cellXY]
        cellsXY.append(cellXY)
        cellsLL.append(cellLL)
        
#TODO give random values to the interactive grid cells and create a geojson
featureArray=[]
for cLL in cellsLL:
    feat={'type':'Feature',
          'geometry':{'type':'Polygon','coordinates': cLL},
          'properties':{'type':str(np.random.choice(range(6)))}}
    featureArray.extend([feat])
gridGeoJ={'type':'FeatureCollection', 'features': featureArray,
          "crs": { "type": "name", "properties": { "name": "EPSG:4326" } }}
os.chdir('..')
json.dump(gridGeoJ, open('ABM/includes/bostonGrid2x2.geojson', 'w'))