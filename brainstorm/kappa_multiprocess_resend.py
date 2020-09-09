import os
import glob
import numpy as np
import pandas as pd
from os import fdopen

#from ema_workbench import (RealParameter, IntegerParameter, BooleanParameter, ScalarOutcome, ArrayOutcome, Constant, Model, MultiprocessingEvaluator, Policy, perform_experiments, ema_logging )
#start: 03:28PM 25 June 2020
from functools import partial
from multiprocessing import Pool, Lock

def calc_total_cells(mask):
    x = np.unique(mask, return_counts=True)[-1][-1]
    return x
    
def calc_agreement(mask, map1, map2, Pe1_array, Pe2_array, Po_array, pair):
    i = pair[0]
    j = pair[1]
    if mask[i,j] != 0:
        x = map1[i, j]
        y = map2[i, j]
        # Amend the expected array count
        Pe1_array[x]=Pe1_array[x]+1
        Pe2_array[y]=Pe2_array[y]+1
        # If there is agreement, amend the observed count
        if x == y:
            Po_array[x] = Po_array[x] + 1
            
    return Pe1_array, Pe2_array, Po_array
            
def kappa(counter, mask, total_cells, map_pairs):
    # Determine the map dimensions and number of land-use classes.
    print(map_pairs[counter][0], map_pairs[counter][1])
    map1 = np.array(pd.read_csv(map_pairs[counter][0],header=None))
    map2 = np.array(pd.read_csv(map_pairs[counter][1],header=None))
    shape_map1 = np.shape(map1)
    row = shape_map1[0]
    column = shape_map1[1]
    luc = np.amax(map1) + 1
    # Determine the total number of cells to be considered.
    if total_cells==0:
        for i in range(0, row):
            for j in range(0, column):
                x = mask[i, j]
                if x != 0:
                    total_cells = total_cells + 1
    # Initialise an array to store the observed agreement probability.
    Po_array = np.zeros(shape=luc)
    # Initialise a set of arrays to store the expected agreement probability,
    # for both maps, and then combined.
    Pe1_array = np.zeros(shape=luc)
    Pe2_array = np.zeros(shape=luc)
    Pe_array = np.zeros(shape=luc)
    # Initialise an array to store the maximum possible agreement probability.
    Pmax_array=np.zeros(shape=luc)
    # Analyse the agreement between the two maps.
                
    unique_map1 = np.unique(map1, return_counts=True)
    unique_map2 = np.unique(map2, return_counts=True)
    
    for i, cl in enumerate(unique_map1[0]):
        if (cl!=24) & (cl!=28):
            Pe1_array[cl] = unique_map1[1][i]
            similar = np.where(((map1==cl) & (map2==cl)), 1, 0)
            Po_array[cl] = np.sum(np.sum(similar))
            
    for i, cl in enumerate(unique_map2[0]):
        if (cl!=24) & (cl!=28):
            Pe2_array[cl] = unique_map2[1][i]
            
    # Convert to probabilities.
    Po_array[:] = [x/total_cells for x in Po_array]
    Pe1_array[:] = [x/total_cells for x in Pe1_array]
    Pe2_array[:] = [x/total_cells for x in Pe2_array]
    # Now process the arrays to determine the maximum and expected
    # probabilities.
    for i in range(0, luc):
        Pmax_array[i] = min(Pe1_array[i], Pe2_array[i])
        Pe_array[i] = Pe1_array[i]*Pe2_array[i]
    # Calculate the values of probability observed, expected, and max.
    Po = np.sum(Po_array)
    Pmax = np.sum(Pmax_array)
    Pe = np.sum(Pe_array)
    # Now calculate the Kappa histogram and Kappa location.
    Khist = (Pmax - Pe)/(1 - Pe)
    Kloc = (Po - Pe)/(Pmax - Pe)
    # Finally, calculate Kappa.
    Kappa=Khist*Kloc
    print(Kappa)
    # Return the value of Kappa.
    return Kappa
    
def kappa_old(map1, map2, mask, total_cells):
    # Determine the map dimensions and number of land-use classes.
    shape_map1 = np.shape(map1)
    row = shape_map1[0]
    column = shape_map1[1]
    luc = np.amax(map1) + 1
    # Determine the total number of cells to be considered.
    #total_cells = 0
    #for i in range(0, row):
    #    for j in range(0, column):
    #        x = mask[i, j]
    #        if x != 0:
    #            total_cells = total_cells + 1
    # Initialise an array to store the observed agreement probability.
    Po_array = np.zeros(shape=luc)
    # Initialise a set of arrays to store the expected agreement probability,
    # for both maps, and then combined.
    Pe1_array = np.zeros(shape=luc)
    Pe2_array = np.zeros(shape=luc)
    Pe_array = np.zeros(shape=luc)
    # Initialise an array to store the maximum possible agreement probability.
    Pmax_array=np.zeros(shape=luc)
    # Analyse the agreement between the two maps.
    for i in range(0, row):
        for j in range(0, column):
            if mask[i,j] != 0:
                x = map1[i, j]
                y = map2[i, j]
                # Amend the expected array count
                Pe1_array[x]=Pe1_array[x]+1
                Pe2_array[y]=Pe2_array[y]+1
                # If there is agreement, amend the observed count
                if x == y:
                        Po_array[x] = Po_array[x] + 1
    # Convert to probabilities.
    Po_array[:] = [x/total_cells for x in Po_array]
    Pe1_array[:] = [x/total_cells for x in Pe1_array]
    Pe2_array[:] = [x/total_cells for x in Pe2_array]
    # Now process the arrays to determine the maximum and expected
    # probabilities.
    for i in range(0, luc):
        Pmax_array[i] = min(Pe1_array[i], Pe2_array[i])
        Pe_array[i] = Pe1_array[i]*Pe2_array[i]
    # Calculate the values of probability observed, expected, and max.
    Po = np.sum(Po_array)
    Pmax = np.sum(Pmax_array)
    Pe = np.sum(Pe_array)
    # Now calculate the Kappa histogram and Kappa location.
    Khist = (Pmax - Pe)/(1 - Pe)
    Kloc = (Po - Pe)/(Pmax - Pe)
    # Finally, calculate Kappa.
    Kappa=Khist*Kloc
    # Return the value of Kappa.
    return Kappa


if __name__ == '__main__':
    
    print('loading mask')
    src = 'regionboundaries.asc'
    a = np.loadtxt(src, skiprows=6)
    mask = np.where((a == 24) | (a ==28 ), 0 , 1)
    total_cells = calc_total_cells(mask)
    
    all_slices = []
    all_slices.extend(['extracted_slicenew1_/map500exp_'+str(x)+'.csv' for x in np.arange(0,1300)])
    all_slices.extend(['extracted_slicenew2_/map500exp_'+str(x)+'.csv' for x in np.arange(0,350)])
    all_slices.extend(['extracted_slicenew3_/map500exp_'+str(x)+'.csv' for x in np.arange(0,350)])
    #all_slices = ['extracted/map500exp_{}.csv'.format(x) for x in range(5)]
    print('no of maps: ' + str(len(all_slices)))
    
    print('generating map pairs')
    map_pairs=[]
    y = []
    for j in range(len(all_slices)):
        for i in range(len(all_slices)):
            if i < j:
                map1 = all_slices[j]
                map2 = all_slices[i]
                map_pairs.append((map1,map2))
                
    print('starting kappa')
    print(len(map_pairs))
    #print(kappa(counter=0, mask=mask,total_cells=total_cells,map_pairs=map_pairs))
    #print(kappa_old(map1=np.array(pd.read_csv(map_pairs[0][0],header=None)), 
    #        map2=np.array(pd.read_csv(map_pairs[0][1],header=None)),
    #        mask=mask,total_cells=total_cells))
    counters = list(np.arange(0,len(map_pairs),1))
    num_processors = 50
    p=Pool(processes=num_processors)
    output = p.map(partial(kappa,mask=mask,total_cells=total_cells,map_pairs=map_pairs), counters)
    df = pd.DataFrame()
    df['map1'] = [x[0] for x in map_pairs]
    df['map2'] = [x[1] for x in map_pairs]
    df['kappa'] = output
    print(len(df))
     
    #df = pd.DataFrame(np.ones((len(outcomes['lusmap']), len(outcomes['lusmap']))))
    #for item in y:
    #    try:
    #        i = item[0]
    #        j = item[1]
    #        k = item[2]
    #        df[i][j] = k
    #    except:
    #        pass

    df.to_csv('test_multiprocessnew.csv')

 
    

            
    
    
    
   
    
    
    
 



            