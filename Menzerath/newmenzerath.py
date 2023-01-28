#!/usr/bin/python3
# -*- coding: utf-8 -*-

####
# Copyright (C) 2018 Kim Gerdes
# kim AT gerdes. fr
# http://arborator.ilpga.fr/
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


version="2.2"
version="2.3"
version="2.4"
version = "2.5"
version = "2.7"



import re, copy, os
import conll
from .lib import transconll, docopt


import datetime, codecs, time, sys, os, glob, re, numpy, multiprocessing, psutil
#sys.path.insert(0, '../lib')
#import tqdm
#tqdm.monitor_interval = 0
try:
	import tqdm
	tqdm.monitor_interval = 0
except:
	pass



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



def getAllConllFiles(basefolder, groupByLanguage=True):
	"""
	for a given basefolder, 
	gives back a dictionary code -> list of files under the code
	{"en":["/dqsdf/en.partut.conllu", ...] }
	"""
	langConllFiles={}
	for dirpath, dirnames, files in os.walk(basefolder):
		for f in files:
			if f.endswith(".conllu") and "not-to-release" not in dirpath: # and '-PUD' in dirpath:
				if groupByLanguage:	lcode=re.split(r"\W|_",f)[0] # now all different treebanks for english are under 'en'
				else:			lcode=re.split(r"\-",f)[0] # now the codes are for example 'en', 'en_partut', 'en_lines'				
				#if lcode in langConllFiles: print lcode,f
				langConllFiles[lcode]=langConllFiles.get(lcode,[])+[os.path.join(dirpath,f)]
			#else:
				#print(f)
	#print langConllFiles
	return langConllFiles





debug=False
#debug=True


#inconll = 
def openfile(code):
	outfile=open('resultTsv'+version+'/'+code+".heavymenz.tsv","w")
	addlinetotsv(outfile, "corpus", "type", "constsize", 'sentencesize')
	return outfile

def addlinetotsv(outfile,corpus,ty,size,sentencesize):
	outfile.write('\t'.join([corpus]+[ty]+[str(size), str(sentencesize)])+'\n')


def find_heads(tree, xtype):
	if xtype == "root":
		heads = [tree.rootnode]
	elif xtype == "VERB":
		heads = [i for i in tree if tree[i]["tag"]=="VERB"]
	elif xtype == "NOUN-PROPN":
		heads = [i for i in tree if tree[i]["tag"] in ["NOUN", "PROPN"]]
	elif xtype == "countent-word":
		heads = [i for i in tree if tree[i]["tag"] in ["NOUN", "PROPN", "ADJ", "ADV", "VERB"]]
	elif xtype == "any":
		heads = [i for i in tree if len(tree[i]["span"])>1] #add all nodes that have one or more dependants
	return heads

def has_right_abtype(tree, abtype, dependants): 
	#type XAB with X = VERB
	test = True
	if abtype in["comp", "mod"]:
		for dep in dependants:
			rel = list(tree[dep]["gov"].values())[0]
			urel = rel.split("@")[0].split(":")[0]
			# print(urel)
			if urel != abtype:
				test = False
	# TODO
	elif abtype == "content-word-phrase":
		pass
	return test


def span_has_content_word(tree, span):
	test = False
	for num in span:
		tag = tree[num]["tag"]
		if tag in ["NOUN", "PROPN", "VERB", "ADJ", "ADV"]:
			test = True
			return str(test)
	return str(test)

def newnewheavymenz(langConllFiles, outfile):
	with open(outfile, "w") as outf:

		outf.write("\t".join(["lang", "dir", "t_id", "h_id", "type", "weight", "cw_inspan", "headpos", "headrel", "deppos", "deprel", "ashorterthanb"])+"\n")
		t_id = -1
		for lcode in langConllFiles:
			print("====", lcode)

			for inconll in langConllFiles[lcode]:
				trees = conll.conllFile2trees(inconll)

				for tree in trees:
					t_id += 1
					tree.addspan(exclude=['punct'])
				
					heads = [i for i in tree if len(tree[i]["span"])>1]
					
					for head in heads:
						depstoright = [i for i in tree[head]['kids'] if i>head]
						depstoleft = [i for i in tree[head]["kids"] if i<head]
						headpos = tree[head]["tag"]
						headrel = list(tree[head]["gov"].values())[0].split("@")[0].split(":")[0]

						# right dependants
						if len(depstoright) == 1:
							nature = "c" #type XC with X = VERB
							weight = len(tree[depstoright[0]]["span"])
							cw = span_has_content_word(tree, tree[depstoright[0]]["span"])
							deppos = tree[depstoright[0]]["tag"]
							deprel = list(tree[depstoright[0]]["gov"].values())[0].split("@")[0].split(":")[0]
							outf.write("\t".join([lcode, "right", str(t_id), str(head), nature, str(weight), cw, headpos, headrel, deppos, deprel, "True"])+"\n")

						elif len(depstoright) == 2:

							if len(tree[depstoright[0]]["span"]) < len(tree[depstoright[1]]["span"]):
								condition = "True"
							else:
								condition = "False"
							# a
							nature = "a"
							weight = len(tree[depstoright[0]]["span"])
							cw = span_has_content_word(tree, tree[depstoright[0]]["span"])
							deppos = tree[depstoright[0]]["tag"]
							deprel = list(tree[depstoright[0]]["gov"].values())[0].split("@")[0].split(":")[0]
							outf.write("\t".join([lcode, "right", str(t_id), str(head), nature, str(weight), cw, headpos, headrel, deppos, deprel, condition])+"\n")
							# b
							nature = "b"
							weight = len(tree[depstoright[1]]["span"])
							cw = span_has_content_word(tree, tree[depstoright[1]]["span"])
							deppos = tree[depstoright[1]]["tag"]
							deprel = list(tree[depstoright[1]]["gov"].values())[0].split("@")[0].split(":")[0]
							outf.write("\t".join([lcode, "right", str(t_id), str(head), nature, str(weight), cw, headpos, headrel, deppos, deprel, condition])+"\n")

						# left dependants
						if len(depstoleft) == 1:
							nature = "c"
							weight = len(tree[depstoleft[0]]["span"])
							cw = span_has_content_word(tree, tree[depstoleft[0]]["span"])
							deppos = tree[depstoleft[0]]["tag"]
							deprel = list(tree[depstoleft[0]]["gov"].values())[0].split("@")[0].split(":")[0]
							outf.write("\t".join([lcode, "left", str(t_id), str(head), nature, str(weight), cw, headpos, headrel, deppos, deprel, "True"])+"\n")
						elif len(depstoleft) == 2:


							if len(tree[depstoleft[1]]["span"]) < len(tree[depstoleft[0]]["span"]):
								condition = "True"
							else:
								condition = "False"
							# b
							nature = "b"
							weight = len(tree[depstoleft[0]]["span"])
							cw = span_has_content_word(tree, tree[depstoleft[0]]["span"])
							deppos = tree[depstoleft[0]]["tag"]
							depprel = list(tree[depstoleft[0]]["gov"].values())[0].split("@")[0].split(":")[0]
							outf.write("\t".join([lcode, "left", str(t_id), str(head), nature, str(weight), cw, headpos, headrel, deppos, deprel, condition])+"\n")
							# a
							nature = "a"
							weight = len(tree[depstoleft[1]]["span"])
							cw = span_has_content_word(tree, tree[depstoleft[1]]["span"])
							deppos = tree[depstoleft[1]]["tag"]
							deprel = list(tree[depstoleft[1]]["gov"].values())[0].split("@")[0].split(":")[0]
							outf.write("\t".join([lcode, "left", str(t_id), str(head), nature, str(weight), cw, headpos, headrel, deppos, deprel, condition])+"\n")

def findSampleSentence(lcode):
	langConllFiles=getAllConllFiles("sud-treebanks-v2.7/", groupByLanguage=True)
	for inconll in langConllFiles[lcode]:
		#print(inconll)
		if 'SUD_English-GUM' not in inconll: continue
		print('file:',inconll)
		trees = conll.conllFile2trees(inconll)

		for tree in trees:
			#t_id += 1
			tree.addspan(exclude=['punct'])
		
			heads = [i for i in tree if len(tree[i]["span"])>1]
			
			for head in heads:
				depstoright = [i for i in tree[head]['kids'] if i>head]
				depstoleft = [i for i in tree[head]["kids"] if i<head]
				headpos = tree[head]["tag"]
				headrel = list(tree[head]["gov"].values())[0].split("@")[0].split(":")[0]

				

				if headpos=="VERB" and headrel=="root" and len(depstoright) == 2:
					print('=====',tree.sentence())
					## a
					#nature = "a"
					#weight = len(tree[depstoright[0]]["span"])
					#cw = span_has_content_word(tree, tree[depstoright[0]]["span"])
					#deppos = tree[depstoright[0]]["tag"]
					#deprel = list(tree[depstoright[0]]["gov"].values())[0].split("@")[0].split(":")[0]
					#outf.write("\t".join([lcode, "right", str(t_id), str(head), nature, str(weight), cw, headpos, headrel, deppos, deprel])+"\n")
					## b
					#nature = "b"
					#weight = len(tree[depstoright[1]]["span"])
					#cw = span_has_content_word(tree, tree[depstoright[1]]["span"])
					#deppos = tree[depstoright[1]]["tag"]
					#deprel = list(tree[depstoright[1]]["gov"].values())[0].split("@")[0].split(":")[0]
					#outf.write("\t".join([lcode, "right", str(t_id), str(head), nature, str(weight), cw, headpos, headrel, deppos, deprel])+"\n")



def newheavymenz(info):
	
	aa,bb,cc, allss, considss = [],[],[], [], []
	count=0
	(lcode, langConllFiles, direction, xtype, abtype) = info
	print('doing',lcode)
	print('param', direction, xtype, abtype)
	
	# direction = "right"
	# xtype = "any"
	# abtype = "any"
	# abtype = "comp"
	
	heads = []
	
	for inconll in langConllFiles[lcode]:
		trees = conll.conllFile2trees(inconll)
		
		for tree in trees:
			tree.addspan(exclude=['punct'])
			ssize=max(tree) #len(tree)
			allss+=[ssize]
			if direction == "right":
				heads = find_heads(tree, xtype)
				for head in heads:
					depstoright = [i for i in tree[head]['kids'] if i>head]
					if len(depstoright) == 1:
						if abtype == "any":
							test = True
						else:
							test = has_right_abtype(tree, abtype, depstoright)
						if test:
							c = len(tree[depstoright[0]]["span"])
							cc+=[c]
							considss+=[ssize]
						else:
							continue
					elif len(depstoright) == 2:
						if abtype == "any":
							test = True
						else:
							test = has_right_abtype(tree, abtype, depstoright)
						if test:
							a=len(tree[depstoright[0]]['span'])
							aa+=[a]
							b=len(tree[depstoright[1]]['span'])
							bb+=[b]
							considss+=[ssize]
					else:
						continue
			else:
				heads = find_heads(tree, xtype)
				for head in heads:
					depstoleft = [i for i in tree[head]['kids'] if i<head] #left
					if len(depstoleft) == 1:
						if abtype == "any":
							test = True
						else:
							test = has_right_abtype(tree, abtype, depstoleft)
						if test:
							c = len(tree[depstoleft[0]]["span"])
							cc+=[c]
							considss+=[ssize]
					elif len(depstoleft) == 2:
						if abtype == "any":
							test = True
						else:
							test = has_right_abtype(tree, abtype, depstoleft)
						if test:
							a=len(tree[depstoleft[1]]['span']) # the one with the highest id is "a" this time
							aa+=[a]
							b=len(tree[depstoleft[0]]['span'])
							bb+=[b]
							considss+=[ssize]
					else:
						continue
	print('done',lcode)
	if len(aa) == 0:
		res_a = "nan"
	else:
		res_a = sum(aa)/len(aa)
	if len(bb) == 0:
		res_b = "nan"
	else:
		res_b = sum(bb)/len(bb)
	if len(cc) == 0:
		res_c = "nan"
	else:
		res_c = sum(cc)/len(cc)
	# print(langNames[lcode], lcode, sum(aa)/len(aa), sum(bb)/len(bb), sum(cc)/len(cc), sum(allss)/len(allss), sum(considss)/len(considss), len(considss))
	return (langNames[lcode], lcode, res_a, res_b, res_c, sum(allss)/len(allss), sum(considss)/len(considss), len(considss))



def heavymenz(info):
	
	aa,bb,cc, allss, considss = [],[],[], [], []
	#ssizeabc={}
	count=0
	(lcode, langConllFiles) = info
	
	print('doing',lcode)
	
	#outfile = openfile(lcode)
	#avoutfile = openfile(lcode+'.av')
	
	for inconll in langConllFiles[lcode]:
		print(inconll)
		trees = conll.conllFile2trees(inconll)
		#corpus = inconll.split("/")[-1].split('.')[0]
		
		for tree in trees:
			tree.addspan(exclude=['punct'])
			#print(tree)
			#print(tree.rootnode)
			#print(tree[tree.rootnode]['kids'])
			nodestotheright = [i for i in tree[tree.rootnode]['kids'] if i>tree.rootnode]
			ssize=max(tree)
			allss+=[ssize]
			#ssizeabc[ssize]=ssizeabc.get(ssize,[[],[],[]])
			#print(nodestotheright)
			if len(nodestotheright)==1:
				c=len(tree[nodestotheright[0]]['span'])
				cc+=[c]
				#ssizeabc[ssize][2]+=[c]
				considss+=[ssize]
				#addlinetotsv(outfile, lcode, 'c', c, ssize)
				#print(1111,count, tree)
			if len(nodestotheright)==2:
				a=len(tree[nodestotheright[0]]['span'])
				aa+=[a]
				#ssizeabc[ssize][0]+=[a]
				#addlinetotsv(outfile, lcode, 'a', a, ssize)
				b=len(tree[nodestotheright[1]]['span'])
				bb+=[b]
				#ssizeabc[ssize][1]+=[b]
				#addlinetotsv(outfile, lcode, 'b', b, ssize)
				considss+=[ssize]
			#i,tree[i]['span'])
			
			#if len(aa)>1 and len(bb)>1:
				#break
		
	#for ssize in sorted(ssizeabc):
		#for i,abc in enumerate(ssizeabc[ssize]):
			#if len(abc)!=0:
				#addlinetotsv(avoutfile, lcode, "abc"[i], sum(abc)/len(abc), ssize)
		
	print('done',lcode)
	return (langNames[lcode], lcode, sum(aa)/len(aa), sum(bb)/len(bb), sum(cc)/len(cc), sum(allss)/len(allss), sum(considss)/len(considss), len(considss))



def oldheavymenz(info):
	
	aa,bb,cc = [],[],[]
	ssizeabc={}
	count=0
	(lcode, langConllFiles) = info
	
	print('doing',lcode)
	
	outfile = openfile(lcode)
	avoutfile = openfile(lcode+'.av')
	
	for inconll in langConllFiles[lcode]:
		print(inconll)
		trees = conll.conllFile2trees(inconll)
		#corpus = inconll.split("/")[-1].split('.')[0]
		
		for tree in trees:
			tree.addspan(exclude=['punct'])
			#print(tree)
			#print(tree.rootnode)
			#print(tree[tree.rootnode]['kids'])
			nodestotheright = [i for i in tree[tree.rootnode]['kids'] if i>tree.rootnode]
			ssize=max(tree)
			ssizeabc[ssize]=ssizeabc.get(ssize,[[],[],[]])
			#print(nodestotheright)
			if len(nodestotheright)==1:
				c=len(tree[nodestotheright[0]]['span'])
				cc+=[c]
				ssizeabc[ssize][2]+=[c]
				addlinetotsv(outfile, lcode, 'c', c, ssize)
				#print(1111,count, tree)
			if len(nodestotheright)==2:
				a=len(tree[nodestotheright[0]]['span'])
				aa+=[a]
				ssizeabc[ssize][0]+=[a]
				addlinetotsv(outfile, lcode, 'a', a, ssize)
				b=len(tree[nodestotheright[1]]['span'])
				bb+=[b]
				ssizeabc[ssize][1]+=[b]
				addlinetotsv(outfile, lcode, 'b', b, ssize)
			#i,tree[i]['span'])
			
			#if len(aa)>1 and len(bb)>1:
				#break
		
	for ssize in sorted(ssizeabc):
		for i,abc in enumerate(ssizeabc[ssize]):
			if len(abc)!=0:
				addlinetotsv(avoutfile, lcode, "abc"[i], sum(abc)/len(abc), ssize)
		
	print('done',lcode)
	return (lcode, sum(aa)/len(aa), sum(bb)/len(bb), sum(cc)/len(cc))


def threadedcomputeheavymens(langConllFiles, direction, xtype, abtype, skipFuncs=['root'], skipLangs=[]):
	
	#langConllFiles={'sv':langConllFiles['sv'], 'fr':langConllFiles['fr']}
	#langConllFiles={'fr':langConllFiles['fr']}
	#langConllFiles={'sv':langConllFiles['sv']}
	#print(77777777777,len(langConllFiles['sv']))
	ti = time.time()
	pool = multiprocessing.Pool(psutil.cpu_count()) # *2 -1
	#pool = multiprocessing.Pool(1) # *2 -1

	
	infotodo = [(lcode, langConllFiles, direction, xtype, abtype) for lcode in langConllFiles if lcode not in skipLangs]
	#print(infotodo)
	#qsdf
	pbar = tqdm.tqdm(total=len(infotodo))
	results = []
	for res in pool.imap_unordered(newheavymenz, infotodo):
		results.append(res)
		#print("results",results)
		pbar.update()
	print ("it took",time.time()-ti,"seconds")
	print ("\n\n\n====================== finished reading in. \n combining...")
	print ("writing...", len(results))
	outfile=open('language.abc.'+version+'.'+direction+'.'+xtype+'.'+abtype+'.tsv','w')
	outfile.write('\t'.join(['language','lcode','a','b','c','allss','considss', 'considnr'])+'\n')
	for (language, code, a,b,c, allss, considss, considnr) in sorted(results):
		outfile.write('\t'.join([str(x) for x in [language, code, a,b,c, allss, considss, considnr]])+'\n')
	
	print ("it took",time.time()-ti,"seconds")
	#pbar.update()
	#print(pbar)




def go(groupByLanguage=True):


	#avoutfile=open("avheavymenz.tsv","w")
	#addlinetotsv(avoutfile, "corpus", "type", "avconstsize", 'sentencesize')


	#langConllFiles=getAllConllFiles("ud-treebanks-v"+version+"/", groupByLanguage=groupByLanguage)
	langConllFiles=getAllConllFiles("sud-treebanks-v"+version+"/", groupByLanguage=groupByLanguage)
	if groupByLanguage:
		for code in langConllFiles:
			if code not in langNames : print ("can't find the language", code,langConllFiles[code])
	#print(langConllFiles)
	#qsdf
	print(len(langConllFiles),'languages')
	
	#qsdf
	for direction in ["left", "right"]:
		for xtype in ["root", "VERB", "NOUN-PROPN", "content-word", "any"]:
			for abtype in ["comp", "mod", "any"]:
				threadedcomputeheavymens(langConllFiles, direction, xtype, abtype, skipFuncs=['root'], skipLangs=[])




# findSampleSentence('en')
# qsdf


# xtype = "root"
# abtype = "any"
# go()

# langConllFiles=getAllConllFiles("sud-treebanks-v"+version+"/", groupByLanguage=True)
# infotodo = [(lcode, langConllFiles, "abc.languages.longfile.v2.4.tsv") for lcode in langConllFiles]
# langConllFiles = {k:v for (k,v) in langConllFiles.items() if k == "cs"}
# newnewheavymenz(langConllFiles, "abc.languages.longfile.v2.7.tsv_2")
