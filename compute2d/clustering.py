import os,time,simpledtw
from pathlib import Path
import numpy as np

import matplotlib.pyplot as plt
import pandas as pd

from tsv2json import tsv2jsonNew, getoptions, gettypes
from distance import langInter,prepareData, newPrepareData2d,dist,distGraphDep,writeData

#run when distance prepared and stored at clustering/

def closestGr(distData, n = 10):
    """
    find n closest graphs to the Graph, distData: a dictionary including distance data between graphs &Graph
    i.e. return keys of n min values
    """
    v = distData.values 
    #print(type(v))
    k = np.array(list(distData.keys())) #same ordre as v in python3
    #print(type(k))
    sortedIdx = v.argsort() 
    return k[sortedIdx[1:n+1]], v[sortedIdx[1:n+1]] #first one is self




def writeClosestGraph(distData,version, n = 1):
    close = {}
    for g in range(len(gr2id)):
        grs, ds = closestGr(distData.iloc[g], n = n)
        close[id2graphDf[g][0]] = {'graph':grs[0],'distance':ds[0]}
    writeData(['closestGraph1d_'+version+'.tsv'],[close],resFolder = "clustering")
    return close


def getGroupData(groupK):
    """groupK:indice of graphs (1D), return a list of df """ #TO TEST
    return [id2graphDf[grId][1] for grId in groupK]

def langInterGr(grData):
    
    langs = [set(pd.index.tolist()) for pd in grData]
    la = langs[0]
    inter = False
    for i in range(1,len(langs)):
        if la != langs[i]:
            inter = True
            #print("extract languages in group")
            la = la.intersection(langs[i])
    return [pd.loc[list(la)] for pd in grData] if inter else grData

def initCentre(n,d,label = None):
    """
    label: language names as point label, default None (cloud form)
    return a graph with n point in [0,1]**d 
    """
    c = np.random.uniform(size= (n,d))
    axlabel = "xyz"
    column = list(axlabel)[:d]
    
    if label == None:
        return pd.DataFrame(c, columns = column)
    
    assert(len(label)==n)
    return  pd.DataFrame(c, columns = column, index = label)  

def initCentres(K, n, d, label = None):
    """init randomly K centres """
    return [initCentre(n = n, d = d, label = label) for k in range(K)]

class KmeansDep:

    def __init__(self,K,IterationMax): ## instanciation d'un objet du type de la classe.
        self.K = K #cluster nb
        self.N = 0 #graph nb
        self.n = 0 #number of language pts
        self.D = 0 # pts dimension
        self.IterationMax = IterationMax
        self.affectations = np.zeros((self.N,self.K))
        self.centres = [pd.DataFrame(np.zeros((self.n,self.D))) for k in range(K)]
        #self.id2graphDf = {}
        #self.gr2id = {}
    
    def fit(self,id2grDf, dim):
        #self.id2graphDf = id2grDf
        #self.gr2id = gr2id
        
        self.N = len(id2grDf)
        label = id2grDf[0][1].index.tolist() #if not DTW else None
        self.n = len(label)
        print("there are ", self.n, " languages")
        self.D = dim
        centres = initCentres(self.K, self.n, self.D, label = label)
      
        ## boucle (comme plus haut)
        for  i in range(self.IterationMax):
            affectations = self.majAffectationDep(id2grDf, centres)
            centres = self.majcentresDep(id2grDf, affectations)
            #print(i, centres)
                     
        ## on affecte le resultat dans les variables membres de la classe.
        self.centres = centres
        self.affectations = affectations
        return self.centres, self.affectations
    
    #def dist(self, g1,g2):#peut pour n D  # il faut mettre pour la définition 
    #    """g1,g2: 2 dataframes contain positions of languages in both graph1 and graph2"""
    #    return np.sqrt(np.sum((a-b)**2))

    def centreDep(self,groupK, id2grDf):
        """
        language deplacement in 1D graph: calculate the barycentre of group K 
        groupK: indices of graphs
        """
        if len(groupK) == 0:
            print("group no element")
            labels = id2grDf[0][1].index.tolist()
            return initCentre(self.n, self.D, label = labels)

        centre = {}
        grData = langInterGr(getGroupData(groupK))
        for la in grData[0].index:
            #print([gr.loc[la] for gr in grData])
            centre[la] = sum([gr.loc[la] for gr in grData])/len(grData)
        return pd.DataFrame(data= centre).T
    
    def majAffectationDep(self, id2grDf, centres):
        #print("affectation")
        a = np.zeros((self.N,self.K))
        for n in range(self.N):
            distances = np.zeros(self.K)
            for k in range(self.K):
                distances[k] = distGraphDep(id2grDf[n][1], centres[k])
            group = np.argmin(distances)
            a[n,group] = 1
        return a 

    def majcentresDep(self, id2grDf, affectation):
        #print("majcenters")
        centres = []
        langIds = np.arange(self.N)
        
        for k in range(self.K):
            masque = affectation[:,k] == 1
            group = langIds[masque] 
            centres.append(self.centreDep(group, id2grDf))
        return centres



class KmeansDTW:

    def __init__(self,K,IterationMax): ## instanciation d'un objet du type de la classe.
        self.K = K #cluster nb
        self.N = 0 #graph nb
        self.n = 0 #number of language pts
        self.D = 0 # pts dimension
        self.IterationMax = IterationMax
        self.affectations = np.zeros((self.N,self.K))
        self.centres = [pd.DataFrame(np.zeros((self.n,self.D))) for k in range(K)]
        #self.id2graphDf = {}
        #self.gr2id = {}
    
    def fit(self,id2grDf,mappings, dim):
        #self.id2graphDf = id2grDf
        #self.gr2id = gr2id
        ti = time.time()
        
        self.N = len(id2grDf)
        self.n = len(id2grDf[0][1].index)
        print("there are ", self.n, " languages")
        self.D = dim
        centres = initCentres(self.K, self.n, self.D)
      
        ## boucle (comme plus haut)
        for  i in range(self.IterationMax):
            affectations = self.majAffectationDTW(id2grDf, centres)
            centres = self.majcentresDTW(id2graphDf, affectations, mappings)
            #print(i, representants)
                     
        ## on affecte le resultat dans les variables membres de la classe.
        self.centres = centres
        self.affectations = affectations
        print("\nfit done, time used:", time.time()-ti)
        return self.centres, self.affectations
    
    #def dist(self, g1,g2, DTW = True):#peut pour n D  # il faut mettre pour la définition 
    #    """g1,g2: 2 dataframes contain positions of languages in both graph1 and graph2"""       
    #   return np.sqrt(np.sum((a-b)**2))

    def centreDTW(self, groupK, mappings):
        """
        cloud form in 1D graph: calculate the barycentre of group K with mapping
        groupK: indices of graphs
        """
        ti = time.time()
        axlabel = "xyz"
        column = list(axlabel)[:self.D]

        if len(groupK) == 0:
            print("group no element")
            centre = initCentre(self.n, self.D) 
            print("time used:", time.time()-ti)
            return pd.DataFrame(data= centre, columns = column)

        grData = getGroupData(groupK)

        #take the first graph as "serie 1" in DTW
        gr1 = id2graphDf[groupK[0]][0]
        N = len(grData[0]) #number of language pts
        assert(gr1 in mappings.index)
        mapping = mappings.loc[gr1]

        centre = np.empty((N, self.D)) 
        for idx in range(N): #index of languages
            pts = []
            for g in range(len(grData)):
                #df: grData[g], graph label(1D): groupK[g], mapping between 0&g: mappings.loc[groupK[g]] typ=str
                gr = id2graphDf[groupK[g]][0]
                plist = grData[g].iloc[eval(mapping.loc[gr])[idx]].values
                pts.append(sum(plist)/len(plist))  #'sum' necessary for 2nd 'sum', otherwise error of array shape       
            centre[idx] = sum(pts)/len(pts)

        print("time used:", time.time()-ti)
        return pd.DataFrame(data= centre, columns = column)
    
    def majAffectationDTW(self,id2graphDf, centres):
        a = np.zeros((self.N,self.K))
        for n in range(self.N):
            distances = np.zeros(self.K)
            for k in range(self.K):
                _, cost, mapping1, mapping2, _ = simpledtw.dtw(id2graphDf[n][1].values, centres[k].values)
                distances[k] = cost
            group = np.argmin(distances)
            a[n,group] = 1
        return a

    def majcentresDTW(self,id2graphDf, affectation, mappings):
        centres = []
        langIds = np.arange(self.N)
        for k in range(self.K):
            masque = affectation[:,k] == 1
            group = langIds[masque] 
            centres.append(self.centreDTW(group, mappings))
        return centres



def drawGraph(ax,dataIdx,dim):
    """compare graphs for cloud form, maybe useful for language deplacement """
    gr, dataf = id2graphDf[dataIdx]
    ydata = np.zeros(len(dataf)) if dim == 1 else dataf.values[:,1]
    ax.scatter(dataf.values[:,0], ydata)
    ax.set_title(gr)

def DrawLanguage(ax,dataIdList, lang, dim, label = True):
    """
    language deplacement: draw the language positions of diffrent graphs (input by dataIdList) in a figure
    lang should in every graph of dataIdList
    """
    lanData = np.array([[id2graphDf[i][0],id2graphDf[i][1].loc[lang].values] for i in dataIdList if lang in id2graphDf[i][1].index])
    assert(len(lanData) == len(dataIdList))
    ptsName, pts = lanData[:,0], lanData[:,1]
    
    for i, p in enumerate(pts):
        y = 0 if dim == 1 else p[1]
        ax.scatter(p[0],y, label = str(i)+" "+ ptsName[i])
        ax.annotate(i, [p[0],y-0.01])
    ax.set_title(lang)


def writeAffect(K, affect, filename, resfolder):
    Path(resfd).mkdir(parents=True, exist_ok=True)
    langIds = np.arange(len(id2graphDf))

    with open(resfd+'/' + filename, 'w+',encoding="utf8")as t:
        for k in range(K):
            masque = affect[:,k] == 1
            group = langIds[masque] 

            line = "group"+str(k)+'\t'+str(group)+'\n' 
            t.write(line)


def writeCenter(centers, version, resfolder):
    #1d
    Path(resfolder).mkdir(parents=True, exist_ok=True)
    for i, ct in enumerate(centers):
        ct.to_csv(resfolder+"center{}_{}.tsv".format(i,version), sep = '\t')


if __name__ == '__main__':

    version = 'sud1d'
    typeGroup = 'direction'
    fileDTW1d_map = "clustering/dist1D/"+typeGroup+"/mappingDTW_"+ version +'_'+typeGroup+ ".tsv"


    mappings = pd.read_csv(fileDTW1d_map,sep = '\t',index_col = 0) 
    assert(len(mappings.columns) == len(mappings.index))

    #clustering
    #global var : graphs, id2graphDf, gr2id
    dimension = 1
    #types = gettypes()
    types = ['direction','direction-cfc']
    graphs = [(ty,opt) for ty in types for opt in getoptions(ty)]

    if dimension==2:
        ax1pts = [(li.split('\t')[0],li.split('\t')[1]) for li in open("clustering/names1ptsGr_"+version+".tsv").read().strip().split('\n') ]
        axgraphs = [v for v in graphs if v not in ax1pts]
        graphs1d = axgraphs.copy()
        graphs= [(grx,gry) for grx in axgraphs for gry in axgraphs if (grx!=gry) ] 

    id2graphDf, gr2id = prepareData(graphs) if dimension == 1 else newPrepareData2d(graphs)

    print("test K")

    K = 5 
    resfd = "clusteringInfo/"+typeGroup

    Km = KmeansDep(K = K, IterationMax = 50)
    print("deplacement, k = ", K)
    centers, affect = Km.fit(id2graphDf, dim = 1)

    writeAffect(K, affect, "affectDep"+str(K)+".txt", resfd)
    writeCenter(centers, 'dep', resfd+"/depCenters/")


    Km1 = KmeansDTW(K = K, IterationMax = 50)
    centers1, affect1 = Km1.fit(id2graphDf, mappings, dim = 1)
    print("test cloud form DTW")
    centers1, affect1 = Km.fit(id2graphDf, dim = 1)

    writeAffect(K, affect1, "affectDTW"+str(K)+".txt", resfd)
    writeCenter(centers, 'dtw', resfd+"/dtwCenters/")
