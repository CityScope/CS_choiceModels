#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 30 11:26:38 2018

PUMS Codes Households:

    FES: family type and employment status
    FINCP: family income, last 12 months
    HINCP: household income, last 12 months
    GRNTP: gross rent
    WORKSTAT: work status of householder or spouse in family households
    
@author: doorleyr
"""

from pgmpy.models import BayesianModel
from pgmpy.estimators import MaximumLikelihoodEstimator, BayesianEstimator
from pgmpy.factors.discrete import TabularCPD, State
from pgmpy.sampling import BayesianModelSampling
from pgmpy.inference import VariableElimination
import networkx as nx
import pandas as pd
import pickle
import os
os.chdir('..')

def incomeToNHTSBands(income):
    if income<10000:
        return 1
    elif income<15000:
        return 2
    elif income<25000:
        return 3
    elif income<35000:
        return 4
    elif income<50000:
        return 5
    elif income<75000:
        return 6
    elif income<100000:
        return 7
    elif income<125000:
        return 8
    elif income<150000:
        return 9
    elif income<200000:
        return 10
    else:
        return 11

hh=pd.read_csv('data/PUMS/csv_hma/ss16hma.csv')


colsToKeep={'HINCP':'HhIncome', 'GRNTP':'Rent', 'NP':'HhSize', 'BDSP': 'Bedrooms'}
hh=hh[[c for c in colsToKeep]]
hh.columns=[colsToKeep[c] for c in colsToKeep]

hh=hh[~hh['Rent'].isnull()]
hh=hh[~hh['HhIncome'].isnull()]
hh=hh[hh['HhSize']>0] # get rid of vacant units


hh.loc[hh['Bedrooms']>2, 'Bedrooms']=3
hh.loc[hh['Bedrooms']<1, 'Bedrooms']=1
#hh['IncomeQ'], incomeBins=pd.qcut(hh['HhIncome'], 5, range(5), True)

# get quantiles of rent dependend on the num bedrooms
hh['RentQ']=float('nan')
for nb in range(1,4):
    hh.loc[hh['Bedrooms']==nb, 'RentQ'], rentBins=pd.qcut(hh.loc[hh['Bedrooms']==nb,'Rent'], 3, range(3), True)

hh['IncomeQ']=hh.apply(lambda row: incomeToNHTSBands(row['HhIncome']), axis=1)
hh.loc[hh['HhSize']>5, 'HhSize']=6

#need to start the ordinal variables at zero
hh['Bedrooms']=hh.apply(lambda row: row['Bedrooms']-1, axis=1)
hh['HhSize']=hh.apply(lambda row: row['HhSize']-1, axis=1)
hh['IncomeQ']=hh.apply(lambda row: row['IncomeQ']-1, axis=1)


model = BayesianModel([('IncomeQ', 'Bedrooms'), 
                       ('HhSize', 'Bedrooms'),
                       ('IncomeQ', 'RentQ'),
                       ('Bedrooms', 'RentQ')])
#nx.draw_networkx(model, with_labels=True)
                      
modelData=hh[model.nodes()].copy()
testData=modelData.iloc[int(0.85 * modelData.shape[0]) : int(modelData.shape[0])].copy()
trainData=modelData.iloc[0 : int(0.85 * modelData.shape[0])].copy()
    
model.fit(trainData, estimator=MaximumLikelihoodEstimator)
#for cpd in model.get_cpds():
#    print("CPD of {variable}:".format(variable=cpd.variable))
#    print(cpd)

model_sample = BayesianModelSampling(model)
pickle.dump(model_sample, open('results/sampler.p', 'wb'))


# open the nhts sample and add the inferred resType requirements
nhtsSample=pd.read_csv('results/nhtsSample.csv')
resType=[]
for ind, row in nhtsSample.iterrows():
    evidence = [State('IncomeQ', min(row['hh_income']-1, 10)),
                State('HhSize', min(row['hh_size']-1, 5))]
    sample=model_sample.likelihood_weighted_sample(evidence=evidence, size=1)
    resType.extend([int(sample['Bedrooms'])*3+int(sample['RentQ'])])
nhtsSample['resType']=resType
os.chdir('..')
nhtsSample[nhtsSample['occupation_type']==1].sample(n=50,replace=True
                      ).to_csv('ABM/includes/pop_occat_1.csv', index=False)
nhtsSample[nhtsSample['occupation_type']==2].sample(n=50,replace=True
                      ).to_csv('ABM/includes/pop_occat_2.csv', index=False)
nhtsSample[nhtsSample['occupation_type']==3].sample(n=50,replace=True
                      ).to_csv('ABM/includes/pop_occat_3.csv', index=False)
nhtsSample[nhtsSample['occupation_type']==4].sample(n=50,replace=True
                      ).to_csv('ABM/includes/pop_occat_4.csv', index=False)
nhtsSample[nhtsSample['occupation_type']==5].sample(n=50,replace=True
                      ).to_csv('ABM/includes/pop_occat_5.csv', index=False)