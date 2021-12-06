import os,time,multiprocessing, psutil, tqdm, collections.abc,  simpledtw
from pathlib import Path
import numpy as np
import pandas as pd

from tsv2json import tsv2jsonNew, getoptions, gettypes
from distance import langInter,prepareData,newPrepareData2d,dist,update, writeData

#algo marriage

def getDistArray(gr1,gr2):
    """
    gr1, gr2: 2 dataframes
    return a matrixof distance between pts in gr1 and in gr2, with type array
    """
    #ti = time.time()
    #distance matrix
    langDist = np.zeros((len(gr1),len(gr2)))
    for l1 in range(len(gr1)):
        for l2 in range(len(gr2)):
            langDist[l1][l2] = dist(gr1.iloc[l1].values, gr2.iloc[l2].values)
    #print("dists calculated, taken time", time.time()-ti)
    return langDist 

def prepareLists(gr1, gr2):
    """
    gr1, gr2: 2 dataframes
    return preference list for languages in gr1 with index and dist of pts in gr2 and vice versa
    """
    ti = time.time()
    #distance matrix
    langDist = getDistArray(gr1,gr2)

    #preference lists
    #dictArray = langDist if len(gr1)<len(gr2) else langDist.T
    plists1 = {}
    for i, v in enumerate(langDist):#(dictArray):
        #plists1[i] = sorted(range(len(v)), key=lambda k: v[k])
        plists1[i] = sorted(enumerate(v), key=lambda x: x[1])
    
    plists2 = {}
    for i, v in enumerate(langDist.T):
        #plists2[i] = sorted(range(len(v)), key=lambda k: v[k])
        plists2[i] = sorted(enumerate(v), key=lambda x: x[1])
        
    # print(len(plists1),len(plists2))
    #print("preference lists done, taken time",time.time()-ti)
    return plists1,plists2,langDist


def newprepareLists(gr1, gr2):
    """
    gr1, gr2: 2 dataframes
    return preference list for languages in gr1 with index and dist of pts in gr2 and vice versa
    """
    #ti = time.time()
    #distance matrix
    gy = ['y'] if dimension == 1 else ['x','y']
    posDict1= {k: list(d.index) for k, d in gr1.groupby(gy) if len(d) > 1}
    posDict2= {k: list(d.index) for k, d in gr2.groupby(gy) if len(d) > 1}

    #print("repeated groups number in gr1: ", len(posDict1),"in gr2 ", len(posDict2) )
    langDist = np.zeros((len(gr1),len(gr2)))
    plists1 = {}
    for l1 in range(len(gr1)):
        p1 = tuple(gr1.iloc[l1].values)
        #print("\npts position: ", p1)
        if p1 in posDict1.keys() and l1 != posDict1[p1][0]: #if l1 in the same place as some others pts
            langDist[l1] = langDist[posDict1[p1][0]]
            continue

        for l2 in range(len(gr2)):
            #pp = dist(p1, gr2.iloc[l2].values)
            langDist[l1][l2] = dist(p1, gr2.iloc[l2].values)
        plists1[l1] = sorted(enumerate(langDist[l1]), key=lambda x: x[1])
    #print("dists calculated, taken time", time.time()-ti)
    
    #tii = time.time()
    #preference lists
    for k, ls in posDict1.items(): #pts at the same position
        #print("prl1 begin repete list idx", ls[0])
        for i, v in enumerate(ls[1:]):
            plists1[v] = plists1[ls[0]][(i+1):] + plists1[ls[0]][:(i+1)]
    
    plists2 = {}
    distArray = langDist.T
    #pts at the same position
    for k, ls in posDict2.items(): 
        #print("prl2 begin repete list idx", ls[0])
        plists2[ls[0]] = sorted(enumerate(distArray[ls[0]]), key=lambda x: x[1])
        for i, v in enumerate(ls[1:]):
            plists2[v] = plists2[ls[0]][(i+1):] + plists2[ls[0]][:(i+1)]
    #other pts
    for i, v in enumerate(distArray):
        if i not in plists2.keys():
            plists2[i] = sorted(enumerate(v), key=lambda x: x[1])
        
    #print("preference lists done, taken time",tii-ti)
    return plists1,plists2,langDist

def initMatch(lenGraph):
    """
    graph: a dataframe
    return a dictionary with indice of languages in gr1 as keys 
    and [partner index in gr2, distance, partener index in plists] as values, set to default value [-1,-1.,-1]  
    """
    matchInit = {}
    for la in range(lenGraph):
        matchInit[la] = [-1,-1., -1]
    return matchInit    

def singleRound(singleOnes,prLists1, matchDict1, matchDict2):
    """
    algo marriage, graph1-optimal : gr1 propose, gr2 decide
    prLists1: a dictionary with{language index i: [prefefence list of i ],... }
    """
    for idx in singleOnes:
        #print(len(prLists1))
        candidat = matchDict1[idx][2]+1 #index of candidate in prLists1
        cinfo = prLists1[idx][candidat] #(id in graph2, distance)

        matchDict1[idx][-1] = candidat

        if matchDict2[cinfo[0]][0] == -1: # if candidate unmarried
            matchDict1[idx][:2] = [cinfo[0],cinfo[1]] #partner index in graph2, dist, index in prLIst1
            matchDict2[cinfo[0]]=[idx, cinfo[1]] #, -1]
        else:#if married, compare preference (i.e distance)
            #print("idx",idx," can ",candidat, " current partner of can", matchDict2[cinfo[0]])
            if cinfo[1] < matchDict2[cinfo[0]][1]: #if candidate prefer idx than her current partener
                #print("marriage: ", idx, " ", cinfo[0], "candidat n ", candidat)
                matchDict1[matchDict2[cinfo[0]][0]][:2] = [-1,-1.] #divorce
                matchDict1[idx][:2] = [cinfo[0],cinfo[1]] #re marry
                matchDict2[cinfo[0]]=[idx, cinfo[1]] #, -1]
    return matchDict1, matchDict2

def newsingleRound(singleOnes,prLists1,prLists2, matchDict1, matchDict2):
    """
    algo marriage, graph1-optimal : gr1 propose, gr2 decide
    prLists1: a dictionary with{language index i: [prefefence list of i ],... }
    """
    for idx in singleOnes:
        candidat = matchDict1[idx][1]+1 #index of candidate in prLists1
        cid = prLists1[idx][candidat] #id in graph2
        #print("idx= ", idx, "can = ", candidat, matchDict1[idx] )
        matchDict1[idx][1] = candidat #update current candidate number
        
        #print(prLists2[cid])
        preferIdx = prLists2[cid].index(idx) #index of idx in prLists2
        if matchDict2[cid][0] == -1: # if candidate unmarried
            matchDict1[idx][0] = cid #partner index in graph2
            matchDict2[cid]=[idx, preferIdx] 
        else:#if married, compare preference 
            #print("idx",idx," can ",candidat, " current ", matchDict2[cid])
            if preferIdx < matchDict2[cid][1]: #if candidate prefer idx than her current partener
                #print("marriage: ", idx, " ", cid, "candidat n ", candidat)
                matchDict1[matchDict2[cid][0]][0] = -1 #divorce
                matchDict1[idx][0] = cid #re marry
                matchDict2[cid]=[idx, preferIdx] 

    return matchDict1, matchDict2

def getSingleMen(matchDict):
    return [ idx for idx, val in matchDict.items() if val[0] == -1 ]

def distMarriage(prLists1, lenGr1,lenGr2):
    """return dist of stable marriage match between  graph1 et graph2 """
    ti = time.time()
    matches = (initMatch(lenGr1), initMatch(lenGr2))
    
    matchId = 0 if lenGr1<=lenGr2 else 1
    single = getSingleMen(matches[matchId])
    
    while(single):
        #print(len(single))
        singlemen = single if matchId == 0 else getSingleMen(matches[0])
        matches = singleRound(singlemen, prLists1, matches[0], matches[1])
        single = getSingleMen(matches[matchId])
    
    #distls= [ val[1] for idx, val in match1.items()] #sum(distls),
    #print("match calculated taken time ", time.time()-ti)
    return matches

def newdistMarriage(prLists1,prLists2, lenGr1,lenGr2):
    """return dist of stable marriage match between  graph1 et graph2 #more slow than distMarriage"""
    match1 = initMatch(lenGr1)
    match2 = initMatch(lenGr2)
    
    single = [ idx for idx, val in match1.items() if val[0] == -1 ]
    while(single):
        #print(len(single))
        match1, match2 = newsingleRound(single, prLists1,prLists2, match1, match2)
        single = [ idx for idx, val in match1.items() if val[0] == -1 ]
    
    return match1, match2

def distDataMarry(graphsId):
    """
    distance of cloudform with stable marriage problem
    #graphss: list of tuple (ty,option) in analysis data 
    graphsId: list of graph id
    
    """
    ti = time.time()
    graphsId = [graphsId] if np.isscalar(graphsId) else graphsId

    # print("compute distance for ", graphss) # process", multiprocessing.current_process())

    distDataM = {'dist': {}, 'match':{}}

    for g1 in graphsId:
        k1 = id2graphDf[g1][0] #':'.join(g1)
        print("compute distance for ", k1)
        distDataM['dist'][k1] = distDataM['dist'].get(k1,{})
        distDataM['match'][k1] = distDataM['match'].get(k1,{}) #k1 optimal

        distDataM['dist'][k1][k1]= 0.0
        posG1 = id2graphDf[gr2id[k1]][1] 
        distDataM['match'][k1][k1] = list(range(len(posG1)))
        
        for id2, val2 in id2graphDf.items():
            
            k2 = val2[0] 
            #if(k1 == k2):   print("self", k1, id2)
            distDataM['dist'][k2] = distDataM['dist'].get(k2,{})
            distDataM['match'][k2] = distDataM['match'].get(k2,{})
            
            if distDataM['dist'][k1].get(k2)==None:
                #print('g1 = ',k1, " g2 = ",k2)
                posG2 = val2[1] 

                prl1, prl2,distarray = newprepareLists(posG1, posG2)
                len1 = len(posG1)
                len2 = len(posG2)
                #print("\n\n calculate for gr size", len1, len2)
                match1, _ = distMarriage( prl1, len1, len2) 
                distlist= [ val[1] for idx, val in match1.items() if val[0]!=-1]
                distM = sum(distlist)/len(distlist) #average by number of languages
                # match1 = newdistMarriage( prl1,prl2, len(posG1), len(posG2))

                distDataM['dist'][k1][k2]= distM
                distDataM['dist'][k2][k1]= distM
                distDataM['match'][k1][k2] = [match1[idx][0] for idx in range(len(match1))] #range(len(match1)) == sorted(match1)
                
                match2,_ = distMarriage(prl2, len2, len1)
                #match2 =  newdistMarriage( prl2,prl1, len(posG2), len(posG1))
                distDataM['match'][k2][k1] = [match2[idx][0] for idx in range(len(match2))]
    
    print("take time: ", time.time()-ti)
    return distDataM


def distMarryMulti(graphsId):
    ti = time.time()
    print("compute distance multi")
    distDataM = {'dist': {}, 'match':{}}

    pbar = tqdm.tqdm(total=len(graphsId))
    results = []
    
    with multiprocessing.Pool(psutil.cpu_count()) as pool:
        for res in pool.imap_unordered(distDataMarry, graphsId):
            pbar.update()
            results.append(res)        
    print("it took",time.time()-ti,"seconds")
    print("\n\n\n====================== finished reading in. \n combining...")
    
    for dists in results:
        update(distDataM['dist'], dists['dist'])
        update(distDataM['match'], dists['match'])
        
    print("it took",time.time()-ti,"seconds")
    return distDataM


def prepareDistMarr(version, resfolder = "clustering" ):
    distDataMarr =  distMarryMulti(range(len(graphs))) #distDataMarry(range(len(graphs)))
    files = [ "distMarry_"+version+".tsv","mappingMarry_"+version+".tsv"]
    writeData(files, [distDataMarr['dist'],distDataMarr['match'] ] , resFolder = resfolder)


if __name__ == '__main__':
    #global var : graphs, id2graphDf, gr2id,dimension,version
    dimension = 2
    version = 'sud'

    typeGroups = {
        'distance': ['distance','distance-abs','distance-cfc'],
        'direction': ['direction','direction-cfc'],
        'menzerath':['menzerath']
     }

    #group distance
    group = 'distance'
    #group = 'direction'
    #group = 'menzerath'
    types = typeGroups[group]
    graphs = [(ty,opt) for ty in types for opt in getoptions(ty)][:4]
    if dimension==2:
        ax1pts = [(li.split('\t')[0],li.split('\t')[1]) for li in open("clustering/names1ptsGr_"+version+".tsv").read().strip().split('\n') ]
        axgraphs = [v for v in graphs if v not in ax1pts] #remove the 1D graphs among 2d graphs
        graphs1d = axgraphs.copy()
        graphs= [(grx,gry) for grx in axgraphs for gry in axgraphs if (grx!=gry) ] 
    print(len(graphs)) 

    #prepare data
    id2graphDf, gr2id = newPrepareData2d(graphs,graphs1d, lang = False)
    #computation
    resfolder = "clustering/dist2D/"+group
    prepareDistMarr(version = version+"2d_"+group,resfolder = resfolder )




