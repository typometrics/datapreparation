import os,time,multiprocessing, psutil, tqdm, collections.abc, simpledtw
#from concurrent.futures import ProcessPoolExecutor as fatherPool #with python3.8+
from functools import partial
from contextlib import contextmanager

from pathlib import Path
import numpy as np
import pandas as pd

from tsv2json import tsv2jsonNew, getoptions, gettypes

@contextmanager
def poolcontext(*args, **kwargs):
    pool = multiprocessing.Pool(*args, **kwargs)
    yield pool
    pool.terminate()

#global var : graphs, id2graphDf, gr2id,dimension,version
dimension = 1
version = 'ud'
#types = gettypes()
#types = ['menzerath']
#types = ['distribution']
#types = ['direction','direction-cfc']
types = ['distance','distance-abs','distance-cfc']

print(types)
graphs = [(ty,opt) for ty in types for opt in getoptions(ty)]

if dimension==2:
    ax1pts = [(li.split('\t')[0],li.split('\t')[1]) for li in open("clustering/names1ptsGr_"+version+".tsv").read().strip().split('\n') ]
    axgraphs = [v for v in graphs if v not in ax1pts] #remove the 1D graphs among 2d graphs
    graphs1d = axgraphs.copy()
    graphs= [(grx,gry) for grx in axgraphs for gry in axgraphs if (grx!=gry) ] 

print(len(graphs)) 
#dim == 2, minonzero=60: 1312170 for sud, 834482 for ud after removing 1 pts graphs

#creat position dataframe from the input jsondata
def posData(axtypes, ax, dim, axminOcc = None, lang = True):
    """
    dim as dimension, axtypes & ax: list with len=dim or string with dim 1
    return positions data after normalization (in [0,1])
    """
    if axminOcc == None:
        axminOcc = np.zeros(dim)
    assert(len(axminOcc) == dim)
    jsonData, _, _, _, _,_ = tsv2jsonNew(axtypes = axtypes, ax = ax , axminocc = axminOcc,dim = dim, verbose = False)
    
    N = len(jsonData)
    dataDict = {}
    for i, la in enumerate(jsonData):
        assert(len(la.get('data'))==1)
        data = la.get('data')[0]
        
        k = data.get('label') if lang else i
        dataDict[k]={'y': np.float16(data.get('y'))} #graph1d with pts at y axis
        if dim > 1:
            dataDict[k]['x'] = np.float16(data.get('x'))
        #if dim == 3:
            
    XY = pd.DataFrame(data=dataDict).T
    return XY

    #normalisation
    sub = (XY.max()-XY.min()) 
    res =  (XY-XY.min())/sub
    if sub.loc['y'] == 0:
        print("Error: should not enter here when computation 2d")
        print("pos y idem ", axtypes, ax)
        res['y'] = 0.5
    # #if 2D: to calculate distances between 2D graphs, graphs with idem column.s removed in advance 
    # #so we can put in comment this if
    # if dim > 1 and sub.loc['x'] == 0:
    #     res['x'] = 0. 
    #     return res
    return res



def langInter(posG1,posG2):
    """
    extract languges in both graph1 and graph2
    posG1, posG2 : dataframes of languges positions in graph1 & graph2
    """
    lanG1 = sorted(posG1.index.tolist())
    lanG2 = sorted(posG2.index.tolist())
    #print(lanG1 ==lanG2)
    
    if lanG1 !=lanG2:
        #print("extract languages")
        langN = [lan for lan in lanG1 if lan in lanG2 ]
        #extract positions of langN 
        posG1 =  posG1.loc[langN]
        posG2 = posG2.loc[langN]
        assert(posG1.index.tolist() == posG2.index.tolist())
    return posG1, posG2


def prepareData(graphs, lang = True):
    """return graph2id and id2graphDf dict, graph 1D"""
    ti = time.time()
    gr2id = {}
    id2gr = {}
    print("prepare data 1d\n ",len(graphs),'\n')# graphs)
    for i, v in enumerate(graphs):
        #print("idx: ", i, " items ", v)
        gr = ':'.join(v)
        #print(gr)
        gr2id[gr] = i
        id2gr[i] = [gr,posData(v[0],v[1], dim = 1, lang = lang)]#get1Data(gr)]
    print("data prepared, take time: ", time.time()-ti)
    return id2gr, gr2id 


def newPrepareData2d(graphs,graphs1d,lang = True):
    ti = time.time()
    gr2id = {}
    id2gr = {}
    print("prepare data 2d\n ",len(graphs),'\n')
    #prepare axis
    id2gr1D, gr2id1D = prepareData(graphs1d, lang = lang)
    #print("axis prepared, take time ", time.time() - ti)
    #prepare graphs
    for i, v in enumerate(graphs):
        #print("idx: ", i, " items ", v)
        axisx = ':'.join(v[0])
        axisy = ':'.join(v[1])

        gr = '::'.join([axisx , axisy])
        gr2id[gr] = i
        dfx = id2gr1D[gr2id1D[axisx]][1]
        dfy = id2gr1D[gr2id1D[axisy]][1]
        res = pd.concat([ dfx.rename(columns={'y':'x'}), dfy], axis=1, join = 'inner')

        if np.any(res.max() != 1.) or np.any(res.min() != 0.):
            res = (res-res.min())/(res.max()-res.min())

        id2gr[i] = [gr, res]
    print("data prepared, take time(total): ", time.time()-ti)
    return id2gr, gr2id


def dist(p1,p2):
    return np.sum((p1-p2)**2)**0.5


def distGraphDep(g1,g2):
    """
    languages' deplacement between g1 and g2 
    g1,g2: 2 dataframes contain positions of languages in both graph1 and graph2
    """
    g1,g2 = langInter(g1,g2)
    distSum = 0.
    for la in g1.index:
        # dl = dist(g1.loc[la].values, g2.loc[la].values)
        # distSum += dl
        distSum += np.float32(dist(g1.loc[la].values, g2.loc[la].values))
    return np.float32(distSum/len(g1))

#id2graphDf, gr2id = prepareData(graphs) if dimension == 1 else prepareData2d(graphs)

def distData1_sub(graphsId, posG1, resDicts):
    #compute for the row with index k1
    
    graphsId = [graphsId] if np.isscalar(graphsId) else graphsId
    dictDep, dictDTW,dictDTW_map = resDicts
    map_k2k1 = {}

    for g2 in graphsId:
        k2 = id2graphDf[g2][0]

        if dictDep.get(k2) ==None:
            posG2 = id2graphDf[g2][1] 
            dictDep[k2] = distGraphDep(posG1,posG2) 

        if dictDTW_map.get(k2) == None:
            assert(dictDTW.get(k2) == None)
            matches, distDTW, mapping1, mapping2, matrix = simpledtw.dtw(posG1.values, posG2.values)
            distDTW = np.float16(distDTW/len(matches))
            dictDTW[k2] = distDTW
            dictDTW_map[k2] = mapping1
            map_k2k1[k2]= mapping2 

    return dictDep, dictDTW,dictDTW_map, map_k2k1

def distDataMulti_sub(graphsId, posG1, resDicts):
    #compute for the row with index k1
    #graphsId: list of graphs idx 
    
    ti = time.time()
    print("compute distance multi_sub ", len(graphsId) )
    dictDep, dictDTW,dictDTW_map = resDicts
    map_k2k1 = {}

    #pbar = tqdm.tqdm(total=len(graphs))
    results = []
    
    with poolcontext(processes = psutil.cpu_count()) as pool: #psutil.cpu_count()
        for res in pool.imap_unordered(partial(distData1_sub, posG1 = posG1, resDicts = resDicts),graphsId):
            #pbar.update()
            results.append(res)
            
    print("it took",time.time()-ti,"seconds")
    print("\n\n\n====================== finished reading in. \n combining...")
    
    for dists in results:
        update(dictDep, dists[0])
        update(dictDTW, dists[1])
        update(dictDTW_map, dists[2])
        update(map_k2k1, dists[3])
        
    print("it took",time.time()-ti,"seconds")
    return dictDep, dictDTW,dictDTW_map, map_k2k1


def newDistData1(graphsId):
    ti = time.time()
    graphsId = [graphsId] if np.isscalar(graphsId) else graphsId
    #print("new version dist data")
    
    distDataDep = {} 
    distDataDTW = {'distDTW':{},
                    'mapping':{}
                    }

    for g1 in graphsId:
        k1 = id2graphDf[g1][0] 
        print("compute distance for ", k1) 
        #init
        distDataDep[k1] = distDataDep.get(k1,{})
        distDataDTW['distDTW'][k1] = distDataDTW['distDTW'].get(k1,{})
        distDataDTW['mapping'][k1] = distDataDTW['mapping'].get(k1,{})
        #k1 == k2
        posG1 = id2graphDf[g1][1]
        distDataDep[k1][k1] = 0.
        distDataDTW['distDTW'][k1][k1] = 0.
        distDataDTW['mapping'][k1][k1] = [[i] for i in range(len(posG1))]

        if dimension == 2:
            ax0,ax1 = k1.split('::')
            k3 = ax1+'::'+ax0
            distDataDep[k3] = distDataDep.get(k3,{})
            distDataDTW['distDTW'][k3] = distDataDTW['distDTW'].get(k3,{})
            distDataDTW['mapping'][k3] = distDataDTW['mapping'].get(k3,{})

        #compute for k1
        resDictK1 = [distDataDep.get(k1,{}),
                    distDataDTW['distDTW'].get(k1,{}), 
                    distDataDTW['mapping'].get(k1,{}) ]

        grIds = range(len(gr2id))  #gr2id global var
        dictDep, dictDTW,dictDTW_map, map_k2k1 = distDataMulti_sub( grIds , posG1, resDictK1)

        #affectation
        distDataDep[k1] = dictDep
        distDataDTW['distDTW'][k1]= dictDTW
        distDataDTW['mapping'][k1]=dictDTW_map

        if False:
            resfd = "clusteringTMP/menzerath/tempo{}".format(g1)
            Path(resfd).mkdir(parents=True, exist_ok=True)
            files = ["tmp_"+k1+"_dep.tsv", "tmp_"+k1+"_dtw.tsv","tmp_"+k1+"_map.tsv"]
            dicts = [distDataDep[k1], distDataDTW['distDTW'][k1],distDataDTW['mapping'][k1]]

            for i in range(len(files)):
                with open(resfd+'/'+files[i], 'w+',encoding="utf8")as t:
                    line0 = "options"+'\t'+k1 +'\n' 
                    t.write(line0)
                    for gr in sorted(dicts[i]):
                        t.write(gr + '\t'+ str(dicts[i].get(gr))+'\n')
        
        for g2 in grIds:
            if g2!= g1:
                k2 = id2graphDf[g2][0]
                #print("\nk2 ==",k2)
                assert(k2 in dictDep.keys() and k2 in dictDTW.keys() and k2 in dictDTW_map.keys() )
                distDataDep[k2] = distDataDep.get(k2,{})
                distDataDTW['distDTW'][k2] = distDataDTW['distDTW'].get(k2,{})
                distDataDTW['mapping'][k2] = distDataDTW['mapping'].get(k2,{})

                distDataDep[k2][k1]= distDataDep[k1][k2]
                distDataDTW['distDTW'][k2][k1]= distDataDTW['distDTW'][k1][k2]
                if k2 in map_k2k1.keys():
                    distDataDTW['mapping'][k2][k1] = map_k2k1[k2] #if g2==g1, k2 not in map_k2k1

                if dimension == 2:
                    ax0,ax1 = k2.split('::')
                    k4 = ax1+'::'+ax0
                    if distDataDep[k3].get(k4)==None:#when K4 = K1, if k1 = AB, k2 = BA, then K3 = BA, K4 = AB
                        distDataDep[k4] = distDataDep.get(k4,{})
                        distDataDTW['distDTW'][k4] = distDataDTW['distDTW'].get(k4,{})
                        distDataDTW['mapping'][k4] = distDataDTW['mapping'].get(k4,{})

                        distDataDep[k3][k4]= distDataDep[k1][k2]
                        distDataDep[k4][k3]= distDataDep[k1][k2]
                        assert(distDataDTW['distDTW'][k3].get(k4) == None)
                        distDataDTW['distDTW'][k3][k4]= distDataDTW['distDTW'][k1][k2]
                        distDataDTW['distDTW'][k4][k3]= distDataDTW['distDTW'][k1][k2]
                        distDataDTW['mapping'][k3][k4] = distDataDTW['mapping'][k1][k2]
                        distDataDTW['mapping'][k4][k3] = distDataDTW['mapping'][k2][k1]
        # distDataDep[k1] = {}
        # distDataDTW['distDTW'][k1] = {}
        # distDataDTW['mapping'][k1] = {}

    print("take time: ", time.time()-ti)
    return distDataDep,distDataDTW



def distData1(graphsId):
    """
    distance of cloudform with DTW and languge deplacement for 1D graphs
    graphsId: list of graph id
    
    """
    
    ti = time.time()
    graphsId = [graphsId] if np.isscalar(graphsId) else graphsId

    # print("compute distance for ", id2graphDf[graphsId][0]) # process", multiprocessing.current_process())
    #id2graphDf, gr2id = prepareData(graphs)

    distDataDep = {} 
    distDataDTW = {'distDTW':{},
                    'mapping':{}
                    }

    for g1 in graphsId:
        k1 = id2graphDf[g1][0] #':'.join(g1)
        print("compute distance for ", k1) 
        distDataDep[k1] = distDataDep.get(k1,{})
        distDataDTW['distDTW'][k1] = distDataDTW['distDTW'].get(k1,{})
        distDataDTW['mapping'][k1] = distDataDTW['mapping'].get(k1,{})
        
        posG1 = id2graphDf[g1][1]
        distDataDep[k1][k1] = 0.
        distDataDTW['distDTW'][k1][k1] = 0.
        distDataDTW['mapping'][k1][k1] = [[i] for i in range(len(posG1))]

        if dimension == 2:
            ax0,ax1 = k1.split('::')
            k3 = ax1+'::'+ax0
            distDataDep[k3] = distDataDep.get(k3,{})
            distDataDTW['distDTW'][k3] = distDataDTW['distDTW'].get(k3,{})
            distDataDTW['mapping'][k3] = distDataDTW['mapping'].get(k3,{})
        

        for id2, val2 in id2graphDf.items():
            
            k2 = val2[0] 
            #if(k1 == k2):   print("self", k1, id2)
            distDataDep[k2] = distDataDep.get(k2,{})
            distDataDTW['distDTW'][k2] = distDataDTW['distDTW'].get(k2,{})
            distDataDTW['mapping'][k2] = distDataDTW['mapping'].get(k2,{})
            
            if distDataDep[k1].get(k2)==None:
                #print('g1 = ',k1, " g2 = ",k2)    
                posG2 = val2[1] 
                distDep = distGraphDep(posG1,posG2)                
                distDataDep[k1][k2]= distDep
                distDataDep[k2][k1]= distDep
                
                assert(distDataDTW['distDTW'][k1].get(k2) == None)
                matches, distDTW, mapping1, mapping2, matrix = simpledtw.dtw(posG1.values, posG2.values)
                distDTW = distDTW/len(matches)
                distDataDTW['distDTW'][k1][k2]= distDTW
                distDataDTW['distDTW'][k2][k1]= distDTW
                distDataDTW['mapping'][k1][k2] = mapping1
                distDataDTW['mapping'][k2][k1] = mapping2 

                if dimension == 2:
                    ax0,ax1 = k2.split('::')
                    k4 = ax1+'::'+ax0
                    if distDataDep[k3].get(k4)==None:#when K4 = K1, if k1 = AB, k2 = BA, then K3 = BA, K4 = AB
                        distDataDep[k4] = distDataDep.get(k4,{})
                        distDataDTW['distDTW'][k4] = distDataDTW['distDTW'].get(k4,{})
                        distDataDTW['mapping'][k4] = distDataDTW['mapping'].get(k4,{})

                        distDataDep[k3][k4]= distDep
                        distDataDep[k4][k3]= distDep
                        assert(distDataDTW['distDTW'][k3].get(k4) == None)
                        distDataDTW['distDTW'][k3][k4]= distDTW
                        distDataDTW['distDTW'][k4][k3]= distDTW
                        distDataDTW['mapping'][k3][k4] = mapping1
                        distDataDTW['mapping'][k4][k3] = mapping2
                    #assert(distDataDTW['distDTW'][k1].get(k2) == None)

    print("take time: ", time.time()-ti)
    return distDataDep,distDataDTW


#copied from datapreparation/conll.py
def update(d, u):
	for k, v in u.items():
		if isinstance(v, collections.abc.Mapping): 
			r = update(d.get(k, {}), v)
			d[k] = r
		else:
			d[k] = u[k]
	return d

def distDataMulti(graphs):

    #pools in pools. BrokenPipeError no 32 if len(graphs) is very large/nb(process) very large
    #graphs: list of graphs idx

    ti = time.time()
    print("compute distance multi")

    #id2graphDf, gr2id = prepareData(graphs)
    distDataDep = {} 
    distDataDTW = {'distDTW':{},
                    'mapping':{}
                    }

    pbar = tqdm.tqdm(total=len(graphs))
    results = []
    
    # with fatherPool(psutil.cpu_count()) as pool_out: #this works with little datasize len(graph)<
    #     for res in pool_out.map(newDistData1,graphs):
    #         pbar.update()
    #         results.append(res)
    with multiprocessing.Pool(psutil.cpu_count()) as pool:
        for res in pool.imap_unordered(distData1,graphs):
            pbar.update()
            results.append(res)
            
    print("it took",time.time()-ti,"seconds")
    print("\n\n\n====================== finished reading in. \n combining...")
    
    for dists in results:
        update(distDataDep, dists[0])
        update(distDataDTW['distDTW'], dists[1]['distDTW'])
        update(distDataDTW['mapping'], dists[1]['mapping'])
        
    print("it took",time.time()-ti,"seconds")
    return distDataDep,distDataDTW


def writeData(filenames,dicts,resFolder = "clustering"):
    print("writing files")
    assert(len(filenames)==len(dicts))
    Path(resFolder).mkdir(parents=True, exist_ok=True)
    for i in range(len(filenames)):
        print(filenames[i])
        with open(resFolder+'/'+filenames[i], 'w+',encoding="utf8")as t:
            #index labels = column labels, 'total' not at the end of each type in the distfile
            line0 = "options"+'\t'+'\t'.join(sorted(dicts[i]))+'\n' 
            t.write(line0)
            for gr in sorted(dicts[i]):
                #print("line for", gr)
                line = gr +'\t'+ '\t'.join([str(dicts[i][gr].get(g)) for g in sorted(dicts[i][gr])])+'\n'
                t.write(line)


def prepareDist0(version, graphsIdList,resfolder = "clustering"):
    #types = gettypes()
    #graphs = [(ty,opt) for ty in types for opt in getoptions(ty)]
    distDataDep,distDataDTW = distDataMulti(graphsIdList) #newDistData1(graphsIdList)  # distData0(graphs) 

    files = ["distDep_"+version+".tsv", "distDTW_"+version+".tsv","mappingDTW_"+version+".tsv"]
    dicts = [distDataDep, distDataDTW['distDTW'],distDataDTW['mapping']]

    writeData(files, dicts, resFolder = resfolder)


def getOnePointGr(version):
    """
    #modify posData to get the 'idem' variable
    find 1D graph(mesure:opt) where every point shares the same position, and remove them before computation of 2D graph
    """ 
    gr1pts = []
    nb = 0

    with open("clustering/info1ptsGr_"+version+".tsv", 'w+',encoding="utf8")as t1:
        with open("clustering/names1ptsGr_"+version+".tsv", 'w+',encoding="utf8")as tname:
            t1.write("graphName\tpointsNumber\tvalue\n")
            for i, v in enumerate(graphs):
                idem, nbPts, vPts = posData(v[0],v[1], dim = 1, lang = True)
                if idem:
                    nb = nb+1
                    gr1pts.append(v)
                    print(i)
                    t1.write(':'.join(v)+'\t'+str(nbPts)+'\t'+str(vPts)+'\n')
                    tname.write('\t'.join(v)+'\n')

    print("graph 1D with 1 pts : nbr ", nb, "name\n", gr1pts)
    return nb, gr1pts

if __name__ == '__main__':
    #prepare data
    id2graphDf, gr2id = prepareData(graphs) if dimension == 1 else newPrepareData2d(graphs, graphs1d)
    
    #computation
    #resfolder = "clusteringTest/dist2D/pool"
    ls = np.arange(len(graphs))
    resfolder = "clustering/dist1D/distance"
    prepareDist0(version = "ud1d_distance",graphsIdList = ls, resfolder = resfolder )

    types = ['direction','direction-cfc']
    graphs = [(ty,opt) for ty in types for opt in getoptions(ty)]
    id2graphDf, gr2id = prepareData(graphs) 
    resfolder = "clustering/dist1D/direction"
    prepareDist0(version = "ud1d_direction",graphsIdList = np.arange(len(graphs)), resfolder = resfolder )

    types = ['menzerath']
    graphs = [(ty,opt) for ty in types for opt in getoptions(ty)]
    id2graphDf, gr2id = prepareData(graphs) 
    resfolder = "clustering/dist1D/menzerath"
    prepareDist0(version = "ud1d_menzerath",graphsIdList = np.arange(len(graphs)), resfolder = resfolder )

    types = ['distribution']
    graphs = [(ty,opt) for ty in types for opt in getoptions(ty)]
    id2graphDf, gr2id = prepareData(graphs) 
    resfolder = "clustering/dist1D/distribution"
    prepareDist0(version = "ud1d_distribution",graphsIdList = np.arange(len(graphs)), resfolder = resfolder )


    # #find graphs where every pts is equal to each other, remove them from axis options before computation of 2d graph to avoid repetition
    # nb, gr1pts = getOnePointGr(version)
    # print("1d graphs name of "+version+" with idem columns")
    # ax1pts = [(li.split('\t')[0],li.split('\t')[1]) for li in open("clustering/names1ptsGr_"+version+".tsv").read().strip().split('\n') ]
    # print(ax1pts)


