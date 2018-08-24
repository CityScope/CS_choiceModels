# Mobility Choice API for CityScope Platform
Predicts mobility choices of simulated individuals based on individual characteristics and land use. The choice models are calibrated based on census data and the individual choices are influenced by initial conditions and by user interactions, as captured by the cityIO server.

## Overview

This repo contains 2 main components:

### 1. Data Analysis and Model Calibration
A number of scripts are provided for analyzing data from sources including the US census, OpenStreetMap and OpenTripPlanner in order to develop a base population sample and to calibrate a multinomial logit model for mode choice prediction.

### 2. API
The mobilityApi.py script is an API based on a python Flask server. The server combines the analysis results, calibrated model and real-time updates from the cityIO server to make mode choice predictions for every individual in the population sample and simulate new individuals when appropriate.
