#!/usr/bin/python3
# -*- coding: utf-8 -*-

####
# Copyright (C) 2017-2020 Kim Gerdes
# kim AT gerdes. fr
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU Affero General Public License (the "License")
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# See the GNU General Public License (www.gnu.org) for more details.
#
# You can retrieve a copy of of version 3 of the GNU Affero General Public License
# from http://www.gnu.org/licenses/agpl-3.0.html 
####

# dependencies:
# pip3 install pandas seaborn matplotlib tqdm psutil
# pip3 install psutil tqdm pandas

#import datetime, codecs, time, sys, os, glob, re, numpy, multiprocessing, psutil, tqdm
import time, sys, os, glob, re, multiprocessing, psutil, tqdm
from pathlib import Path

import conll


def readInLanguageNames():

	langNames={}
	langcodef=open("languageCodes.tsv")
	langcodef.readline()
	for li in langcodef:
		lis = li.strip().split('\t')
		langNames[lis[0]]=lis[-1]
		
	mylangNames = {li.split('\t')[0]: li.split('\t')[1] for li in open(
	'myLanguageCodes.tsv').read().strip().split('\n')}
			
	langNames = dict(langNames, **mylangNames)

	langnameGroup={li.split('\t')[0]:li.split('\t')[1] for li in open('languageGroups.tsv').read().strip().split('\n')  }
	
	return langNames, langnameGroup

langNames, langnameGroup = readInLanguageNames()
# print(langNames)

def getAllConllFiles(basefolder, groupByLanguage=True):
	"""
	for a given basefolder, 
	gives back a dictionary code -> list of files under the code
	{"en":["/dqsdf/en.partut.conllu", ...] }
	"""
	langConllFiles={}
	for dirpath, dirnames, files in os.walk(basefolder):
		for f in files:
			if f.endswith(".conllu") and "not-to-release" not in dirpath:
				if groupByLanguage:	lcode=re.split(r"\W|_",f)[0] # now all different treebanks for iso-639-3english are under 'en'
				else:			lcode=re.split(r"\-",f)[0] # now the codes are for example 'en', 'en_partut', 'en_lines'				
				#if lcode in langConllFiles: print lcode,f
				langConllFiles[lcode]=langConllFiles.get(lcode,[])+[os.path.join(dirpath,f)]
	#print langConllFiles
	return langConllFiles

relationsplit = re.compile(':|@')


# TODO: add this combination
 #elif x_type == "nominal":
		#data = df[df["headpos"].isin(["NOUN", "PROPN"])]
	#elif x_type == "content":
		#data = df[df["headpos"].isin(["NOUN", "PROPN", "ADJ", "ADV", "VERB"])]














def average(lis, rounding):
	try:
		return round(sum(lis)*1.0/len(lis),rounding)
	except:
		return 0

#types=["cat","func","f","f-dist","f-dist-SD","f-dist-noroot","f-dist-noroot-SD","cfc","cf","fc","funcTIMESdist","positive-direction", "cfc-dist", "cf-dist", "posdircfc", "posdircf", "abs-f-dist-noroot"]
types=[ "cat",
	"f",
	"f-dist",
	"f-dist-noroot",
	"cfc",
	"cf",
	"fc",
	"positive-direction", 
	"posdircfc", 
	"posdircf", 
	"cfc-dist", 
	"cf-dist",
	"abs-f-dist-noroot"]


distancetypes={"f-dist":"f","f-dist-noroot":"f","funcTIMESdist":"f", "cfc-dist":"cfc", "cf-dist":"cf", "abs-f-dist-noroot":"f"} # pointing to the corresponding frequency type
distancetypes={t:distancetypes[t] for t in distancetypes if t in types}
sdtypes={"f-dist-SD":"f-dist","f-dist-noroot-SD":"f-dist-noroot"}
sdtypes={t:sdtypes[t] for t in sdtypes if t in types}
multypes={"funcTIMESdist":"f", "positive-direction":"f", "posdircfc":"cfc", "posdircf":"cf"} # pointing to the corresponding frequency type
multypes={t:multypes[t] for t in multypes if t in types}

udcats="ADJ ADP PUNCT ADV AUX SYM INTJ CCONJ X NOUN DET PROPN NUM VERB PART PRON SCONJ".split()
udlexcats="ADJ PUNCT ADV SYM INTJ X NOUN PROPN NUM VERB PRON".split()
udfuncats="ADP AUX CCONJ DET PART SCONJ".split()

udfuncs="nsubj obj iobj csubj ccomp xcomp obl vocative expl dislocated advcl advmod discourse aux cop mark nmod appos nummod acl amod det clf case conj cc fixed flat compound list parataxis orphan goeswith reparandum punct root dep".split()
sudfuncs="appos vocative expl dislocated discourse dep mot comp subj mod unk udep det clf case conj cc fixed flat compound list parataxis orphan goeswith reparandum punct root dep".split() # dep_SUD FAIL_advcl _

thesefuncs = sudfuncs
thesefuncs = udfuncs

verbose=True
verbose=False

errorfile = open("errors.tsv",'w')

def makeStatsOneThread(info):
	"""
	computes the stats for one language
	
	"""
	lcode, langConllFiles, skipFuncs, rounding = info
	if verbose: 
		print(lcode, "...")
		print(multiprocessing.current_process())
	
	
	typesDics={} # temp dico for each language: {"func"(type) ->  {"subj":33, ...}  } - later stored in combined typesDics[ty]["lang"][lcode] :::
	for ty in types:
		typesDics[ty]={}
		typesDics[ty]["all"]={}
		typesDics[ty]["lang"]={lcode:{}}
	
	# 1. collects all the information from the trees:
	for conllfile in langConllFiles[lcode]: # for each conllfile for the current language
		if verbose: print('processing',conllfile, multiprocessing.current_process())
		trees = conll.conllFile2trees(conllfile)
		langcode=lcode.split("_")[0]
		if verbose: print("doing",len(trees),"trees of",lcode,langNames[langcode], multiprocessing.current_process()) # [:2]
		titi=time.time()
		for tree in trees:
			for ni,node in tree.items():
				#skip=False
				tag = node["tag"].strip()
				if tag in udcats:
					typesDics["cat"]["all"][tag]=typesDics["cat"]["all"].get(tag,0)+1
					typesDics["cat"]["lang"][lcode][tag]=typesDics["cat"]["lang"][lcode].get(tag,0)+1
				else:
					tag="X"
				for gi in node["gov"]:
					func=node["gov"][gi]
					syntfunc = func.split("@")[0]
					simpfunc=relationsplit.split(func)[0]
					funcs = [simpfunc]
					if syntfunc!=simpfunc:
						funcs+=[syntfunc]
					if simpfunc in skipFuncs:
						break
					if simpfunc not in thesefuncs: #udfuncs+sudfuncs:
						print("weird simple function",simpfunc)
						errorfile.write('\t'.join([simpfunc,conllfile])+'\n')
						#skip=True
						break
					for f in funcs:
						#typesDics["func"]["lang"][lcode][func]=typesDics["func"]["lang"][lcode].get(func,0)+1
						typesDics["f"]["lang"][lcode][f]=typesDics["f"]["lang"][lcode].get(f,0)+1
						typesDics["f-dist"]["lang"][lcode][f]=typesDics["f-dist"]["lang"][lcode].get(f,[])+[ni-gi]
						if gi: 
							typesDics["f-dist-noroot"]["lang"][lcode][f]=typesDics["f-dist-noroot"]["lang"][lcode].get(f,[])+[ni-gi]
							typesDics["abs-f-dist-noroot"]["lang"][lcode][f]=typesDics["abs-f-dist-noroot"]["lang"][lcode].get(f,[])+[abs(ni-gi)]
						
						gc = tree.get(gi,{"tag":"ROOT"})["tag"].strip()
						if gc not in udcats: gc="X"
						
						fc = f+"-"+tag
						cfc = gc+"-" +fc
						cf = gc+"-" +f
						
						typesDics["cfc"]["lang"][lcode][cfc]=typesDics["cfc"]["lang"][lcode].get(cfc,0)+1
						typesDics["fc"]["lang"][lcode][fc]=typesDics["fc"]["lang"][lcode].get(fc,0)+1
						typesDics["cf"]["lang"][lcode][cf]=typesDics["cf"]["lang"][lcode].get(cf,0)+1
						typesDics["cfc-dist"]["lang"][lcode][cfc]=typesDics["cfc-dist"]["lang"][lcode].get(cfc,[])+[ni-gi]
						typesDics["cf-dist"]["lang"][lcode][cf]=typesDics["cf-dist"]["lang"][lcode].get(cf,[])+[ni-gi]
						#typesDics["func"]["all"][func]=None 
						typesDics["f"]["all"][f]=None 
						typesDics["f-dist"]["all"][f]=None 
						#typesDics["f-dist-SD"]["all"][f]=None 
						if gi: typesDics["f-dist-noroot"]["all"][f]=None 
						if gi: typesDics["abs-f-dist-noroot"]["all"][f]=None 
						#if gi: typesDics["f-dist-noroot-SD"]["all"][f]=None 
						typesDics["cfc"]["all"][cfc]=None 
						typesDics["fc"]["all"][fc]=None 
						typesDics["cf"]["all"][cf]=None 
						#typesDics["funcTIMESdist"]["all"][f]=None
						typesDics["positive-direction"]["all"][f]=None
						typesDics["posdircfc"]["all"][cfc]=None
						typesDics["posdircf"]["all"][cf]=None
					
				
				
				#if skip: continue
				
		if verbose: print("current speed:",int((time.time()-titi)/len(trees)*1000000),"seconds per mtrees of",langNames[langcode])
	
	#for ty in sdtypes: # compute sd (before computing averages)
		#for simpfunc in sorted(typesDics[ty]["all"]):
			#typesDics[ty]["lang"][lcode][simpfunc]=round(numpy.std(typesDics[sdtypes[ty]]["lang"][lcode].get(simpfunc,[])),rounding)
	# 2. compute pourcentages of right-pointing links and averages
	for f in sorted(typesDics["positive-direction"]["all"]): # average percentage of simple relations going to the right
		dists = typesDics["f-dist"]["lang"][lcode].get(f,[])
		if len(dists): posdir=100.0*len([d for d in dists if d>0])/len(dists)
		else: posdir=-1
		typesDics["positive-direction"]["lang"][lcode][f]=posdir
	for cfc in sorted(typesDics["posdircfc"]["all"]): # average percentage of cfc going to the right
		dists = typesDics["cfc-dist"]["lang"][lcode].get(cfc,[])
		if len(dists): posdir=100.0*len([d for d in dists if d>0])/len(dists)
		else: posdir=-1
		typesDics["posdircfc"]["lang"][lcode][cfc]=posdir
	for cf in sorted(typesDics["posdircf"]["all"]): # average percentage of cf going to the right
		dists = typesDics["cf-dist"]["lang"][lcode].get(cf,[])
		if len(dists): posdir=100.0*len([d for d in dists if d>0])/len(dists)
		else: posdir=-1
		typesDics["posdircf"]["lang"][lcode][cf]=posdir
		
	for ty in distancetypes: # compute average of distances. before: list of values, after: average
		for f in sorted(typesDics[ty]["all"]):
			typesDics[ty]["lang"][lcode][f]=average(typesDics[ty]["lang"][lcode].get(f,[]),rounding)
	
	#special stuff for multiplication type:
	#total=sum(typesDics["simpfunc"]["lang"][lcode].values())
	#for simpfunc in sorted(typesDics[ty]["all"]):
		#typesDics["funcTIMESdist"]["lang"][lcode][simpfunc]=typesDics["simpfunc"]["lang"][lcode].get(simpfunc,0) * typesDics["simpfunc-dist-noroot"]["lang"][lcode].get(simpfunc,0) / total
	
	if verbose: print("____",lcode,"done",multiprocessing.current_process())
	
	#if len(typesDics["cat"]["lang"])>1: break # comment this out in order to analyze all languages	

	return typesDics


def makeStatsOneThreadMinimal(info):
	"""
	computes minimal stats for one language
	
	"""
	lcode, langConllFiles, skipFuncs, rounding = info
	if verbose: 
		print(lcode, "...")
		print(multiprocessing.current_process())
	
	
	typesDics={} # temp dico for each language: {"func"(type) ->  {"subj":33, ...}  } - later stored in combined typesDics[ty]["lang"][lcode] :::
	types = ['funcGov']
	for ty in types:
		typesDics[ty]={}
		typesDics[ty]["all"]={}
		typesDics[ty]["lang"]={lcode:{}}
	totaltoks = 0
	totaltrees = 0
	typesDics["funcGov"]["lang"][lcode]['rel']=typesDics["funcGov"]["lang"][lcode].get('rel',0)
	typesDics["funcGov"]["lang"][lcode]['tree']=typesDics["funcGov"]["lang"][lcode].get('tree',0)
	# 1. collects all the information from the trees:
	for conllfile in langConllFiles[lcode]: # for each conllfile for the current language
		if verbose: print('processing',conllfile, multiprocessing.current_process())
		trees = conll.conllFile2trees(conllfile)
		langcode=lcode.split("_")[0]
		if verbose: print("doing",len(trees),"trees of",lcode,langNames[langcode], multiprocessing.current_process()) # [:2]
		titi=time.time()
		
		for tree in trees:
			treeOnlyLexGov = True
			for ni,node in tree.items():
				tag = node["tag"].strip()
				for gi in node["gov"]:
					gc = tree.get(gi,{"tag":"ROOT"})["tag"].strip()
					gf = node["gov"][gi]
					if gc in udfuncats and gf not in ['punct']:
						treeOnlyLexGov = False
						typesDics["funcGov"]["lang"][lcode]['rel']=typesDics["funcGov"]["lang"][lcode].get('rel',0)+1
						if lcode in ['fr','en', 'de'] and len(tree)<10: #  or True
							print(ni,gi,node["gov"][gi],tree)
							
			if treeOnlyLexGov == False:
				typesDics["funcGov"]["lang"][lcode]['tree']=typesDics["funcGov"]["lang"][lcode].get('tree',0)+1
				

			totaltoks += len(tree)	
						
		totaltrees += len(trees)		
		if verbose: print("current speed:",int((time.time()-titi)/len(trees)*1000000),"seconds per mtrees of",langNames[langcode])
	
	# print(typesDics)
	
	typesDics["funcGov"]["lang"][lcode]['rel']=typesDics["funcGov"]["lang"][lcode]['rel']/totaltoks*100
	typesDics["funcGov"]["lang"][lcode]['tree']=typesDics["funcGov"]["lang"][lcode]['tree']/totaltrees*100
	# print(typesDics)
	
	if verbose: print("____",lcode,"done",multiprocessing.current_process())
	
	#if len(typesDics["cat"]["lang"])>1: break # comment this out in order to analyze all languages	

	return typesDics










def makeStatsThreaded(langConllFiles, skipFuncs=['root','compound','fixed','flat','conj'], skipLangs=['kk','sa','ug','lt','be','cop','ta'], rounding=5, colons="langname", analysisfolder='.', minimal=False):
	
	ti = time.time()
	Path(analysisfolder).mkdir(parents=True, exist_ok=True)

	pool = multiprocessing.Pool(psutil.cpu_count()) # *2 -1
	typesDics={} # global dic: {"func" -> { "all":{ "subj":234, ... }, "lang":{"en":{"subj":33, ...}} }
	for ty in types:
		typesDics[ty]={}
		typesDics[ty]["all"]={}
		typesDics[ty]["lang"]={}
	
	infotodo = [(lcode, langConllFiles, skipFuncs, rounding) for lcode in langConllFiles if lcode not in skipLangs]
	#for res in makeStatsOneThread(infotodo[0]): # test first
		#print "______",res,"______" 
	#print infotodo
	#qsdf
	pbar = tqdm.tqdm(total=len(infotodo))
	results = []
	if minimal:
		for res in pool.imap_unordered(makeStatsOneThreadMinimal, infotodo):
			pbar.update()
			results.append(res)
	else:
		for res in pool.imap_unordered(makeStatsOneThread, infotodo):
			pbar.update()
			results.append(res)
	print("it took",time.time()-ti,"seconds")
	print("\n\n\n====================== finished reading in. \n combining...")
	for tdi in results:
		conll.update(typesDics, tdi)
	
	print("it took",time.time()-ti,"seconds")
	print("writing...")
	
	# combining special type dictionaries:
	specdic=distancetypes.copy()
	specdic.update(sdtypes)
	specdic.update(multypes)
	

	# if minimal:
	# 	print(typesDics)
	# 	tsvstr = ""
	# 	realtypes = []
	# 	for ty in typesDics:
	# 		print(ty)
	# 		if typesDics[ty] == {'all': {}, 'lang': {}}: continue
	# 		with open(os.path.join(analysisfolder,ty+".tsv"),"w") as out:


		
	# 	out.write("\t".join(idcolon+sorted(typesDics[ty]["all"])+["total"])+"\n") # title line
	# else:
	if minimal: thesetypes = typesDics.keys()
	else: thesetypes = types
	for ty in thesetypes:
			print(ty)
			if minimal and typesDics[ty] == {'all': {}, 'lang': {}}: continue
			with open(os.path.join(analysisfolder,ty+".tsv"),"w") as out:
				if colons=="langname": idcolon=["name"]
				#elif colons=="langcode": idcolon=["lang"]
				else: idcolon=["lang","name"]
				if minimal:
					somelanguage = list(typesDics[ty]["lang"].keys())[0]
					out.write("\t".join(idcolon+sorted(typesDics[ty]["lang"][somelanguage]))+"\n") # title line
				else:
					out.write("\t".join(idcolon+sorted(typesDics[ty]["all"])+["total"])+"\n") # title line
				for lcode in sorted(langConllFiles): # for each language
					if lcode in typesDics[ty]["lang"]:
						langname=langNames[lcode.split("_")[0]]
						if colons=="langname": idcolon=[langname]
						else: idcolon=[lcode,langname]
					if minimal:
						out.write("\t".join(idcolon+[str(typesDics[ty]["lang"][lcode].get(x,0)) for x in sorted(typesDics[ty]["lang"][lcode])])+"\n")

					else:
					
						if ty in specdic: # distances are already averages, they are written as such. only the "total" is complicated:
							# total: rather average direction/distance of functions. to compute it:
							# for each function: get number of times the simpfunc exists * average distance of this simpfunc
							# add all that and divide by number of relations in total. total is not necessarily useful for sdtypes
							total=sum([typesDics[specdic[ty]]["lang"][lcode].get(x,0)*typesDics[ty]["lang"][lcode].get(x,0) for x in sorted(typesDics[ty]["all"])])/sum(typesDics[specdic[ty]]["lang"][lcode].values())
							out.write("\t".join(idcolon+[str(typesDics[ty]["lang"][lcode].get(x,0)) for x in sorted(typesDics[ty]["all"])]+[str(total)])+"\n")
						else:# frequencies (relative frequencies because divided by total number of links)
							total=sum(typesDics[ty]["lang"][lcode].values())
							out.write("\t".join(idcolon+[str(round(typesDics[ty]["lang"][lcode].get(x,0)*1.0/total,rounding)) for x in sorted(typesDics[ty]["all"])]+[str(total)])+"\n")
							
	print("it took",time.time()-ti,"seconds =",(time.time()-ti)/60,"minutes",(time.time()-ti)/60/60,"hours in total")


#syntactic = "nsubj csubj subj obj iobj ccomp xcomp aux cop case mark cc advmod advcl obl dislocated vocative expl nummod nmod amod discourse acl det clf".split()
#skipFuncs=['root']	
	
def simpleStat(tree):
	"""
	takes a conll tree
	returns 
	- total nb of relations
	- nb of syntactic relations
	- total average dep dist
	- average syntactic dep dist
	- total % right branching
	- syntactic % right branching
	"""
	
	totdist, depdist, totright, depright = [], [], 0, 0
	for ni,node in tree.items():
		for gi in node["gov"]:
			func=node["gov"][gi]
			simpfunc=func.split(":")[0]
		if simpfunc not in skipFuncs:
			totdist += [abs(ni-gi)]
			if ni>gi: totright += 1
			if simpfunc in syntactic:
				depdist += [abs(ni-gi)]
				if ni>gi: depright += 1
	return len(totdist), len(depdist), sum(totdist)/len(totdist), sum(depdist)/len(depdist), len(totright)/len(totdist)*100.0, len(depright)/len(depdist)*100.0

#def simpleDirections(langConllFiles, skipFuncs=['root','compound','fixed','flat','conj'], skipLangs=['kk','sa','ug','lt','be','cop','ta'], rounding=5):
	#"""
	#langConllFiles: dictionary of the form: {"en": [filename1, filename2, ...], ... } e.g. 'en': ['ud-treebanks-v2.0/UD_English/en-ud-train.conllu', 'ud-treebanks-v2.0/UD_English/en-ud-dev.conllu'], 'zh': ['ud-treebanks-v2.0/UD_Chinese/zh-ud-train.conllu',
	#"""
	#ti = time.time()
	
	
	#langPosrel={}
	#for lcode in langConllFiles: # for each language
		#if lcode in skipLangs: continue
		#print(lcode, "...")
		##dicos={} # temp dico for each language: {"func"(type) ->  {"subj":33, ...}  } - later stored in typesDics[ty]["lang"][lcode]
		#rels=0
		#posrels=0
		#for conllfile in langConllFiles[lcode]: # for each conllfile for the current language
			#trees = conll.conllFile2trees(conllfile)
			#langcode=lcode.split("_")[0]
			#print("doing",len(trees),"trees of",lcode,langNames[langcode]) # [:2]
			#titi=time.time()
			#for tree in trees:
				#for ni,node in tree.items():
					#skip=False
					#for gi in node["gov"]:
						#func=node["gov"][gi]
						#simpfunc=func.split(":")[0]
						#if simpfunc in skipFuncs:
							#skip=True
							#break
						#rels+=1
						#if ni-gi>0: posrels+=1
					
			#print("speed now:",int((time.time()-titi)/len(trees)*1000000),"seconds per mtrees")
		
		#print(posrels,rels,100.0*posrels/rels)
		#langPosrel[lcode]=100.0*posrels/rels
		##if len(langPosrel)>1: break
	#print("it took",time.time()-ti,"seconds")
	#print("writing...")
	
	
	#with codecs.open("posdis.tsv","w","utf-8") as out:
		#out.write("\t".join(["name","total"])+"\n")
		#for lcode in sorted(langConllFiles): # for each language
			#if lcode in langPosrel:
				#langname=langNames[lcode.split("_")[0]]
				#total=langPosrel[lcode]
				#out.write("\t".join([langname,str(total)])+"\n")
				
	#print("it took",time.time()-ti,"seconds =",(time.time()-ti)/60,"minutes in total")



def maincomputation():
	conlldatafolder = "ud-treebanks-v2.9"
	analysisfolder = conlldatafolder + '-analysis'
	langConllFiles=getAllConllFiles(conlldatafolder, groupByLanguage=True)
	# print(langConllFiles)
	for code in langConllFiles:
		if code not in langNames : 
			print("can't find", code,langConllFiles[code])
			qsdf

		if ' ' in langConllFiles[code]:
			print('consider replacing this language name:',code,langConllFiles[code])
			qsdf
		#print(code,langNames[code])
	makeStatsThreaded(langConllFiles, skipFuncs=['root'], skipLangs=[], analysisfolder=analysisfolder, minimal=True)
	
	
if __name__ == "__main__":
	
	maincomputation()
	#langConllFiles = {a:v for a,v in langConllFiles.iteritems() if "fr" in a}
