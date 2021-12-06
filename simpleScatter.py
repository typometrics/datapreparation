# -*- coding: utf-8 -*-
#! usr/bin/python3
# dependencies:
# pip3 install pandas seaborn scipy matplotlib psutil tqdm
# sudo apt install librsvg2-bin

# standard libraries:
import os, codecs, re, sys, multiprocessing, random
# to install with pip:
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib import gridspec
#try: 
import psutil 
import pandas as pd
from scipy.stats.stats import spearmanr, pearsonr, describe
import seaborn as sns
#except: pass
import tqdm
#to install from github
from adjustText import adjust_text

from statConll import readInLanguageNames
####################################################################################### 

# where is the data?
#baseDataDir = "byLangData2.1/"
baseDataDir = "udsnapshot/"
#baseDataDir = "byCorpData/"
#baseDataDir = "resultsSUD2.2/"
#baseDataDir = "resultsUD2.2/"
#baseDataDir = "resultskimsoldSUD/"
baseDataDir = "ud-treebanks-v2.9-analysis/"



langNames, langnameGroup = readInLanguageNames()
print(langnameGroup)

groupColors={"Indo-European-Romance":'brown',"Indo-European-Baltoslavic":'purple',"Indo-European-Germanic":'olive',"Indo-European":'royalBlue',"Sino-Austronesian":'limeGreen', "Agglutinating":'red'}
groupMarkers={"Indo-European-Romance":'<',"Indo-European-Baltoslavic":'^',"Indo-European-Germanic":'v',"Indo-European":'>',"Sino-Austronesian":'s', "Agglutinating":'+'}
#filled_markers = ('o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'X')
#fillstyles = ('full', 'left', 'right', 'bottom', 'top', 'none')
#for l in sorted(langnameGroup):	print '"'+l+'":"'+langnameGroup[l]+'", ',

#######################################################################################

#subject object circ dependent total
twoDimImportants="subject object circ dependent subject-PRON subject-NOUN VERB-object-NOUN VERB-object-PRON VERB-circ ADP-object NOUN-dependent VERB-dependent ADJ-dependent ADV-dependent".split()

standardUDFunctions="nsubj obj iobj csubj ccomp xcomp obl vocative expl dislocated advcl advmod discourse aux cop mark nmod appos nummod acl amod det clf case conj cc fixed flat compound list parataxis orphan goeswith reparandum punct root dep".split()

twoDimImportantsUD="nsubj obj iobj csubj ccomp xcomp obl advcl advmod aux cop mark nmod amod det case".split()




############################################################################ basic functions
#######################################################################################

def combinePositives(newname, oldnames, dfPositive, dfFreq):
	"""
	adds a new column to the two df, combining two columns under the newname
	"""
	for func in oldnames:
		if func not in dfFreq: print(func, "not in dfFreq. ignoring it.")
		if func not in dfPositive: print(func, "not in dfPositive. ignoring it.")
	totalfraction = sum( [dfFreq.get(func,0) for func in oldnames] )
	totalpos = sum( [dfFreq.get(func,0)*dfPositive.get(func,0) for func in oldnames] )
	dfFreq[newname] = totalfraction
	dfPositive[newname] = totalpos / totalfraction
	return dfPositive, dfFreq

def addColumn(newname, fromName, dfPositive, dfFreq, dfPosiCfc, dfFreqCfc):
	"""
	creates a new column newname in dfPositive and dfFreq, copying fromName from fromDf
	"""
	dfPositive[newname]=dfPosiCfc[fromName]
	dfFreq[newname]=dfFreqCfc[fromName]
	return dfPositive, dfFreq

def combineMatchCfc(newname, fromRegex, dfPositive, dfFreq, dfPosiCfc, dfFreqCfc):
	"""
	columns in cfc look like this: ADJ-acl->PRON
	"""
	columnsToCombine=[]
	for i in dfPosiCfc:
		if fromRegex.search(i):
			columnsToCombine+=[i]
	#print "columnsToCombine",columnsToCombine
	totalfraction = sum( [dfFreqCfc[cfc] for cfc in columnsToCombine] )
	totalpos = sum( [dfFreqCfc[cfc]*dfPosiCfc[cfc] for cfc in columnsToCombine] )
	dfFreq[newname] = totalfraction
	dfPositive[newname] = totalpos / totalfraction
	return dfPositive, dfFreq

def completeDf():
	"""
	read dataframes and add useful columns
	"""
	
	# read in:
	dfPositive = pd.read_csv(baseDataDir+"positive-direction.tsv",sep='\t',index_col=0)
	
	# simfunc.tsv contains the percentage per function and the absolute number in total!
	dfFreq = pd.read_csv(baseDataDir+"simfunc.tsv",sep='\t',index_col=0)
	
	dfPosiCfc = pd.read_csv(baseDataDir+"posdircfc.tsv",sep='\t',index_col=0)
	dfFreqCfc = pd.read_csv(baseDataDir+"cfc.tsv",sep='\t',index_col=0)
	dfPosiCf = pd.read_csv(baseDataDir+"posdircf.tsv",sep='\t',index_col=0)
	dfFreqCf = pd.read_csv(baseDataDir+"cf.tsv",sep='\t',index_col=0)
	dfDist = pd.read_csv(baseDataDir+"simfunc-dist-noroot.tsv",sep='\t',index_col=0)
	#dfTimes = pd.read_csv(baseDataDir+"funcTIMESdist.tsv",sep='\t',index_col=0)
	dfAbs = pd.read_csv(baseDataDir+"abs-simfunc-dist-noroot.tsv",sep='\t',index_col=0)

	# add columns:
	dfPositive, dfFreq = combinePositives("subject",["nsubj","csubj"], dfPositive, dfFreq)
	dfPositive, dfFreq = combineMatchCfc("subject-PRON",re.compile(r"(n|c)?subj-PRON"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = combineMatchCfc("subject-NOUN",re.compile(r"(n|c)?subj-NOUN"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	
	dfPositive, dfFreq = combineMatchCfc("VERB-subject-PRON",re.compile(r"VERB-(n|c)?subj-PRON"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	
	
	#print dfPositive
	dfPositive["antiaux"]=100-dfPositive["aux"] # = inverse of aux
	dfFreq["antiaux"]=dfFreq["aux"] 
	dfPositive["anticop"]=100-dfPositive["cop"] # = inverse of cop
	dfFreq["anticop"]=dfFreq["cop"] 
	dfPositive["anticase"]=100-dfPositive["case"] # = inverse of case
	dfFreq["anticase"]=dfFreq["case"] 
	dfPositive["antimark"]=100-dfPositive["mark"] # = inverse of mark
	dfFreq["antimark"]=dfFreq["mark"] 
	dfPositive["anticc"]=100-dfPositive["cc"] # = inverse of cc
	dfFreq["anticc"]=dfFreq["cc"] 
	
	#object = obj+iobj+ccomp+xcomp+antiaux+anticop+anticase+antimark+anticc
	dfPositive, dfFreq = combinePositives("object",["obj","iobj","ccomp","xcomp","antiaux","anticop","anticase","antimark","anticc"], dfPositive, dfFreq)
	#NOUN-object-VERB (VERB is obligatory because we added lots of other things to object such as prepositional objects) - i'm using this regex to look in the cfc: VERB-(obj|iobj|ccomp|xcomp)->NOUN
	dfPositive, dfFreq = combineMatchCfc("VERB-object-NOUN",re.compile(r"VERB-(obj|iobj|ccomp|xcomp)-NOUN"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = combineMatchCfc("VERB-object-VERB",re.compile(r"VERB-(obj|iobj|ccomp|xcomp)-VERB"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	#PRON-object-VERB
	dfPositive, dfFreq = combineMatchCfc("VERB-object-PRON",re.compile(r"VERB-(obj|iobj|ccomp|xcomp)-PRON"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	#circ = advmod + advcl 
	dfPositive, dfFreq = combinePositives("circ",["advmod","advcl"], dfPositive, dfFreq)
	
	
	#Faire plutot un truc modifier avec aussi les Xmod et acl et det
	#micro = object + modifier + obl + expl
	#Macrosyntax = dislocated + vocative + discourse
	#Dependent = subject + micro + macro
	
	#first -advmod-VERB and -advcl-VERB 
	#addColumn('VERB-advmod', 'VERB', 'advmod', dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = addColumn("VERB-advmod","VERB-advmod", dfPositive, dfFreq, dfPosiCf, dfFreqCf)
	dfPositive, dfFreq = addColumn("VERB-advcl","VERB-advcl", dfPositive, dfFreq, dfPosiCf, dfFreqCf)
	#dfPositive, dfFreq = addColumn("ADP-obj","ADP-obj", dfPositive, dfFreq, dfPosiCf, dfFreqCf)
	#dfPositive, dfFreq = addColumn(u"←nmod‒NOUN","NOUN-nmod", dfPositive, dfFreq, dfPosiCf, dfFreqCf)
	#then circ-VERB (ancien adCirc) 
	dfPositive, dfFreq = combinePositives("VERB-circ",["VERB-advmod","VERB-advcl"], dfPositive, dfFreq)
	
	#-object-ADP (rappel: = anticase = objectOfAdposition)
	dfPositive[u"ADP-object"]=dfPositive["anticase"]
	dfFreq[u"ADP-object"]=dfFreq["anticase"]
	
	dfPositive["ADP-object-NOUN"]=100-dfPosiCfc["NOUN-case-ADP"] # = inverse of case
	dfFreq["ADP-object-NOUN"]=dfFreqCfc["NOUN-case-ADP"] 
	
	
	
	#dependent = syntagmatic = hypotactic = all syntagmatic relations = for comparison with tesnière
	#= subject + object + circ +obl +'dislocated', 'vocative, expl, nummod, nmod, amod, discourse, acl, det
	#= all \ conj, fixed, flat, compound, list, parataxis, orphan, goeswith, reparandum, punct, root, dep, clf, appos
	#u'subject',  u'object',
	#dfPositive, dfFreq = combinePositives(u"dependent",[ u'circ', 'obl', 'dislocated', 'vocative', 'expl', 'nummod', 'nmod', 'amod', 'discourse', 'acl', 'det'], dfPositive, dfFreq)
	dfPositive, dfFreq = combinePositives("dependent","subject object circ obl dislocated vocative expl nummod nmod amod discourse acl det".split(), dfPositive, dfFreq)
	#dfPositive, dfFreq = combinePositives(u"dependent","subj object iobj ccomp xcomp aux cop case mark cc advmod advcl obl dislocated vocative expl nummod nmod amod discourse acl det".split(), dfPositive, dfFreq)
	#dfAbs, dfFreq = combinePositives("dependent","nsubj csubj obj iobj ccomp xcomp antiaux anticop anticase antimark anticc advmod advcl obl dislocated vocative expl nummod nmod amod discourse acl det".split(), dfAbs, dfFreq)
	
	depe='(n|c)?subj|obj|iobj|ccomp|xcomp|advmod|advcl|obl|dislocated|vocative|expl|nummod|nmod|amod|discourse|acl|det' # no need for antiaux anticop anticase antimark anticc because we add categories
	dfPositive, dfFreq = combineMatchCfc("NOUN-dependent",re.compile(r"NOUN-("+depe+")-"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = combineMatchCfc("VERB-dependent",re.compile(r"VERB-("+depe+")-"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = combineMatchCfc("ADJ-dependent",re.compile(r"ADJ-("+depe+")-"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = combineMatchCfc("ADJ-dependent-ADV",re.compile(r"ADJ-("+depe+")-ADV"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = combineMatchCfc("ADV-dependent",re.compile(r"ADV-("+depe+")-"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = combineMatchCfc("ADV-dependent-ADV",re.compile(r"ADV-("+depe+")-ADV"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = combineMatchCfc("NOUN-dependent-NOUN",re.compile(r"NOUN-("+depe+")-NOUN"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)
	dfPositive, dfFreq = combineMatchCfc("NOUN-dependent-ADJ",re.compile(r"NOUN-amod-ADJ"), dfPositive, dfFreq, dfPosiCfc, dfFreqCfc)

	#nsubj csubj 
	dfAbs["freq"]=dfFreq["total"]
	
	for df in dfPositive, dfPosiCfc, dfFreq, dfDist, dfAbs :
		df.sort_index(inplace=True)
	
	return dfPositive, dfPosiCfc, dfFreq, dfDist, dfAbs

def SUDdf():
	"""
	read dataframes and add useful columns
	"""
	
	# read in:
	dfPositive = pd.read_csv(baseDataDir+"positive-direction.tsv",sep='\t',index_col=0)
	
	# simfunc.tsv contains the percentage per function and the absolute number in total!
	dfFreq = pd.read_csv(baseDataDir+"simfunc.tsv",sep='\t',index_col=0)
	
	dfPosiCfc = pd.read_csv(baseDataDir+"posdircfc.tsv",sep='\t',index_col=0)
	dfFreqCfc = pd.read_csv(baseDataDir+"cfc.tsv",sep='\t',index_col=0)
	dfPosiCf = pd.read_csv(baseDataDir+"posdircf.tsv",sep='\t',index_col=0)
	dfFreqCf = pd.read_csv(baseDataDir+"cf.tsv",sep='\t',index_col=0)
	dfDist = pd.read_csv(baseDataDir+"simfunc-dist-noroot.tsv",sep='\t',index_col=0)
	#dfTimes = pd.read_csv(baseDataDir+"funcTIMESdist.tsv",sep='\t',index_col=0)
	dfAbs = pd.read_csv(baseDataDir+"abs-simfunc-dist-noroot.tsv",sep='\t',index_col=0)
	
	dfPositive["anticc"]=100-dfPositive["cc"] # = inverse of cc
	dfFreq["anticc"]=dfFreq["cc"] 
	# SUD: add columns: dep, comp, mod, and subj and the original UD relations cc, det, discourse, dislocated, expl, and vocative
	dfPositive, dfFreq = combinePositives("dependent",["dep", "comp", "mod", "subj", "anticc", "det", "dislocated", "expl", "vocative"], dfPositive, dfFreq)
	#dfAbs, dfFreq = combinePositives("timsyntagmatic",["dep", "comp", "mod", "subj", "cc", "det", "discourse", "dislocated", "expl", "vocative"], dfAbs, dfFreq)
	# UD: add columns acl, advcl, advmod, amod, aux, case, ccomp, cop, csubj, iobj, mark, nmod, nsubj, nummod, obj, obl, xcomp
	#dfPositive, dfFreq = combinePositives("timsyntagmatic",["acl", "advcl", "advmod", "amod", "aux", "case", "ccomp", "cop", "csubj", "iobj", "mark", "nmod", "nsubj", "nummod", "obj", "obl", "xcomp", "cc", "det", "discourse", "dislocated", "expl", "vocative", "subj"], dfPositive, dfFreq)
	#dfAbs, dfFreq = combinePositives("timsyntagmatic",["acl", "advcl", "advmod", "amod", "aux", "case", "ccomp", "cop", "csubj", "iobj", "mark", "nmod", "nsubj", "nummod", "obj", "obl", "xcomp", "cc", "det", "discourse", "dislocated", "expl", "vocative", "subj"], dfAbs, dfFreq)
	
	
	#dfAbs["freq"]=dfFreq["total"]
	
	#for df in dfPositive, dfPosiCfc, dfFreq, dfDist, dfAbs :
		#df.sort_index(inplace=True)
	
	return dfPositive, dfPosiCfc, dfFreq, dfDist, dfAbs


def combineDataByLanguageGroup(dfAbs):
	"""
	creates new file with language groups counted together
	"""
	fs = standardUDFunctions[:]+['total','dependent']
	fs.remove('root')
	d=dfAbs[fs].multiply(dfAbs["freq"], axis="index")
	d['group']=[langnameGroup[langname] for langname in dfAbs.index]
	d['freq']=dfAbs["freq"]
	dfAbsGroups = d.groupby(['group']).sum()
	dfAbsGroups=dfAbsGroups[fs].divide(dfAbsGroups["freq"], axis="index")
	dfAbsGroups.to_csv("absGroups.tsv", sep='\t')
	return dfAbsGroups 


def findBiggestDiff(lang1, lang2, df): #=
	"""
	ranks differences between two languages
	"""
	oneDimTodo = [ column for column in df if '←' in column] + [ column for column in standardUDFunctions if column in df]
	for v,f in sorted([(abs(df[column][lang1]-df[column][lang2]),column) for column in oneDimTodo], reverse=True):
		print(v,f,lang1,":",df[f][lang1],lang2,":",df[f][lang2])
		 
def combineSvgs(pattern='bidimscat', figurefolder='figures'):
	"""
	combines svg files with pattern in figurefolder into one big pdf
	"""
	os.chdir(figurefolder)
	#os.system('rsvg-convert -f pdf -o histogrammes.pdf barchart*.svg')
	os.system('rsvg-convert -f pdf -o '+pattern+'.pdf '+pattern+'*.svg')


############################################################################ histograms
#######################################################################################

def histogram(dfPositive, dfFreq, functionname, show=False):
	"""
	creates a histogram for one column
	"""
	title="% of → {functionname}".format(functionname=functionname) 
	fig,ax = plt.subplots(figsize=(10, 10))
	
	dfFreq["histogramSortData"]=dfPositive[functionname]
	dfFreq = dfFreq.sort_values("histogramSortData", ascending=False)
	dfPositive = dfPositive.sort_values(functionname, ascending=False)
	#print dfFreq[functionname]
	freq=dfFreq[functionname]*dfFreq["total"]	
	#print freq
	c=[groupColors.get(langnameGroup[label],'k') for label in dfPositive.index]
	#print dfPositive[functionname]
	#qsdf
	ax.barh(list(range(len(dfPositive.index))), dfPositive[functionname], height=0.8, color=c, alpha=.5, edgecolor='darkGray')
	ax.set_yticks(list(range(len(dfPositive.index))), minor=False) # set the y major ticks to be all languages
	ax.set_yticklabels(dfPositive.index, fontsize=9) #replace the name of the x ticks with the language names
	plt.gca().invert_yaxis() # start to count on top
	ax.set_xticks([50,100], minor=False) # only the 50% is major
	ax.set_xticks([10,20,30,40,50,60,70,80,90,100], minor=True) # all 10th are minor
	
	for i, v in enumerate(freq.fillna(0).round(0)):
		ax.text(1, i + .29, str(int(v)), color='royalBlue', alpha=.5) # , fontweight='bold'
	
	plt.grid(which='both', axis='x',alpha=.5) # draw grid
	ax.set_title(title)
	plt.savefig('./figures/barchart-percentage-rightbranching-{functionname}.svg'.format(functionname=functionname), format="svg") #, dpi=300)
	if show: plt.show()
	plt.close(fig)

def numTokHistogram(dfFreq, show=False):
	title="number of tokens"
	fig,ax = plt.subplots(figsize=(10, 10))	
	dfFreq = dfFreq.sort_values("total", ascending=False)
	c=[groupColors.get(langnameGroup[label],'k') for label in dfPositive.index]
	ax.barh(list(range(len(dfFreq.index))), dfFreq["total"], height=0.8, color=c, alpha=.5, edgecolor='darkGray')
	ax.set_yticks(list(range(len(dfPositive.index))), minor=False) # set the y major ticks to be all languages
	ax.set_yticklabels(dfPositive.index, fontsize=9) #replace the name of the x ticks with the language names
	plt.gca().invert_yaxis() # start to count on top
	for i, v in enumerate(dfFreq["total"]):
		ax.text(v+1, i + .29, str(int(v/1000))+"k", color='royalBlue', alpha=.5) # , fontweight='bold'
	
	plt.grid(which='both', axis='x',alpha=.5) # draw grid
	ax.set_title(title)
	plt.savefig('./figures/barchart-tokens.svg', format="svg") #, dpi=300)
	if show: plt.show()
	plt.close(fig)


############################################################################ unidim scatters
#######################################################################################

def allOneDims(df,ty="-direction"): #=dfPositive,
	oneDimTodo = [ column for column in df if '-' in column] + ['dependent'] + [ column for column in standardUDFunctions if column in df]+['NOUN-dependent-ADJ', 'ADP-object', 'ADP-object-NOUN', 'VERB-subject-PRON']
	
	pool = multiprocessing.Pool(psutil.cpu_count()*2)
	
	pbar = tqdm.tqdm(total=len(oneDimTodo))
	limits=True
	show=False
	todos = [(df.index, df[column], column+ty, limits, show) for column in oneDimTodo]
	
	for res in pool.imap_unordered(oneDimScatter, todos): # [0]
		pbar.update()
	
	#for column in oneDimTodo:
		#oneDimScatter(df.index, df[column], column+ty, limits=True, show=False) # .decode('utf-8')
		#break
	


#def oneDimScatter(languageNames, col, title, limits=True, show=False):
def oneDimScatter(info):
	#with plt.xkcd(): # uncomment to make it look funny :)
		"""
		languageNames: all the language names: dfPositive.index
		col: the values per language: dfPositive["dependent"], 
		the title of the plot: "dependent", 
		show: pop up a window to show the graph? show=False
		limits: if given, will fix the limit, if not automatically determined
		"""
		#df = dfPositive["subject"]
		languageNames, col, title, limits, show = info
		adjust = False 
		#adjust = True 
		#graphdirection = "vertical" 
		graphdirection = "horizontal" 
		#graphdirection = "rank" 
		#mini = 500000
		#freq=dfFreq[title]*dfFreq["total"]
		# showLanguageNames = False
		showLanguageNames = True
		texts=[]
		print("oneDimScatter",title)
		plt.rcParams['svg.fonttype'] = 'none'
		
		c=[groupColors.get(langnameGroup[label],'k') for i,label in enumerate(languageNames) if str(col[i])!="nan"]
		col=col.dropna( axis=0, how='any') # remove NaN values
		if graphdirection=="horizontal":
			fig, aa = plt.subplots(figsize=(10, 7))
			aa.axes.get_yaxis().set_visible(False)
			if limits!=None:
				plt.ylim(-10,0.2)
				plt.xlim(-2,102)
			aa.scatter( col, [0 for _ in col], c=c, alpha=0.5, edgecolors='none') # put the dots
			aa.spines['left'].set_visible(False)
			aa.spines['right'].set_visible(False)
			aa.spines['bottom'].set_visible(False)
			aa.xaxis.set_label_position('top') 
			aa.xaxis.set_ticks_position('top')
			aa.set_xticks([0,10,20,30,40,50,60,70,80,90,100], minor=False)
			aa.set_xlabel(title)
			if showLanguageNames:
				already=[]
				for label, x in zip(col.index, col):
					# texts+=[aa.text(x,-.1,label, color=groupColors.get(langnameGroup[label],'k'), fontsize=7,  rotation=270)] # put the labels
					tooclose = False
					for xx in already:
						if abs(x-xx)<.5:
							tooclose = True
					if not tooclose:
						texts+=[aa.text(x,-.1,label, color=groupColors.get(langnameGroup[label],'k',), fontsize=6,  rotation=270, ha='center', va='top')] # put the labels
						already+=[x]

			if adjust:
				adjust_text(texts, col, [0 for _ in col],
					expand_text=(1, 1), ha='center', va='top',force_text=.6,lim=277,
					autoalign='', only_move={'points':'y', 'text':'y'})
		elif graphdirection=="rank":
			fig, aa = plt.subplots()
			aa.axes.get_xaxis().set_visible(False)
			aa.spines['top'].set_visible(False)
			aa.spines['right'].set_visible(False)
			aa.spines['bottom'].set_visible(False)
			aa.yaxis.set_label_position('left') 
			aa.yaxis.set_ticks_position('left')
			aa.set_xticks([0,50,100], minor=False)
			#aa.set_xlabel(title)
			aa.set_ylabel(title)
			#if limits:
			plt.ylim(-2,102)
			plt.xlim(-2,102)
			
			col.sort_values(inplace=True)
			#print col.index
			c=[groupColors.get(langnameGroup[label],'k') for i,label in enumerate(col.index) if str(col[i])!="nan"]
			aa.scatter( [i for i in range(len(col))], col, c=c, alpha=0.5, edgecolors='none') 
		
			
			for i, (label, x) in enumerate(zip(col.index, col)):
				texts+=[aa.text(i,-1,label, color=groupColors.get(langnameGroup[label],'k'), fontsize=5,  rotation=90)] 
			plt.tight_layout()
			if adjust: # , lim=277
				adjust_text(texts, [1 for _ in col], col,
					expand_text=(1, 1), ha='center', va='bottom',force_text=.6,lim=277,
					autoalign='', only_move={'points':'y', 'text':'y'})
		#if graphdirection=="horizontal":
		else:
			fig, aa = plt.subplots(figsize=(7, 10))
			aa.axes.get_xaxis().set_visible(False)
			aa.spines['top'].set_visible(False)
			aa.spines['right'].set_visible(False)
			aa.spines['bottom'].set_visible(False)
			aa.yaxis.set_label_position('left') 
			aa.yaxis.set_ticks_position('left')
			aa.set_yticks([0,50,100], minor=False)
			#if limits:
			plt.ylim(-2,102)
			plt.xlim(-2,102)
			aa.scatter( [0.2 for _ in col], col, c=c, alpha=0.5, edgecolors='none') 
		
			
			for label, x in zip(col.index, col):
				texts+=[aa.text(3,x,label, color=groupColors.get(langnameGroup[label],'k'), fontsize=8,  rotation=0)] 
			plt.tight_layout()
			if adjust: # , lim=277
				adjust_text(texts, [1 for _ in col], col,
					expand_text=(1, 1), ha='left', va='baseline',force_text=.6, lim=99,
					autoalign='', only_move={'points':'x', 'text':'x'})
		#if graphdirection=="horizontal":
			
		#else:
			#for label, x in zip(col.index, col):
				#texts+=[aa.text(5,x,label, color=groupColors.get(langnameGroup[label],'k'), fontsize=8,  rotation=0)] 
		#print(col)
		
		plt.savefig('./figures/unidimscatter-{cols}.svg'.format(cols=title), format="svg") #, dpi=300)
		if show: plt.show()
		plt.close(fig)
		
	

############################################################################ bidim scatters
#######################################################################################
# pas de noir à l'extérieur noir sur 0 et 100



def allTwoDims(dfPositive, dfFreq):
	#counter=0
	#twoDimTodo = [ column for column in dfPositive if u'←' in column] + [ column for column in standardUDFunctions if column in dfPositive] 
	twoDimTodo = twoDimImportants + twoDimImportantsUD
	#twoDimTodo = twoDimImportantsUD
	pbar = tqdm.tqdm(total=len(twoDimTodo)**2-len(twoDimTodo))
	for c,f in enumerate(twoDimTodo): 
		for cc,ff in enumerate(twoDimTodo): 
			if c!=cc:
			#if c<cc:
				#counter+=1
				#print "doing",f,ff,counter,"/",len(twoDimTodo)**2-len(twoDimTodo)
				scatter(dfPositive.index, dfPositive[f], dfPositive[ff],f, ff, dfFreq, mini=5, minimalistic=True, sidegraphs=False, limits=(-10,110), show=False)
				pbar.update()
				#break
		#break

def allTwoDimsKde(dfPositive, dfFreq):
	twoDimTodo = twoDimImportants + twoDimImportantsUD
	#twoDimTodo = twoDimImportantsUD
	pbar = tqdm.tqdm(total=len(twoDimTodo)**2-len(twoDimTodo))
	for c,f in enumerate(twoDimTodo): 
		for cc,ff in enumerate(twoDimTodo): 
			if c!=cc:
				kde(dfPositive,f,ff)
				#dfPositive['VERB-object-PRON'], dfPositive['VERB-object-NOUN'], dfPositive
				pbar.update()

def scatter(languageNames, col1, col2, label1, label2, dfFreq, limits=(0,100), mini=50, showUnderMini=False, minimalistic=False, sidegraphs=True, show=False, labels=True):
	"""
	languageNames: used as labels in the scatter
	col1, col2: the relevant data
	label1, label2: the x and y labels, also used to look up the right column in the dfFreq (frequency dataframe)
	limits: if True fix the limits from 0 to 100, if not automatic
	show: pop up graph after production, if False: only saves the figure without showing it
	mini: threashold under which the dots become gray X (or disappear)
	showUnderMini: if True: shows in gray, otherwise none
	minimalistic: remove numbers and ticks
	sidegraphs: one-dimensional sidegraphs. don't work with adjust_text
	
	"""
	
	thisdf = col1.to_frame().join(col2).dropna(axis=0, how='any')# remove NaN values
	col1=thisdf[label1]
	col2=thisdf[label2]
	#print(col1)
	#print(col2)
	#qsdf
	c=[groupColors.get(langnameGroup[label],'k') for label in languageNames]
	m=[groupMarkers.get(langnameGroup[label],'o') for label in languageNames]
	
	try:
		freq1=dfFreq[label1]*dfFreq["total"]
		freq2=dfFreq[label2]*dfFreq["total"]
	except:
		# any freq to draw all points (freq high enough to pass the test)
		freq1 = pd.DataFrame(mini, index=list(range(len(col1))), columns=list(range(1)))[0]
		freq2 = pd.DataFrame(mini, index=list(range(len(col1))), columns=list(range(1)))[0]
	#label1, label2 ="syntagmatic UD dependency distance ","syntagmatic pure syntactic dependency distance" # manual labels if necessary
	
	plt.rcParams['svg.fonttype'] = 'none'
	
	if sidegraphs:
		fig = plt.figure(figsize=(10,10)) 
		gs = gridspec.GridSpec(2, 2, width_ratios=[1, 25],height_ratios=[25, 1]) 
		aa = plt.subplot(gs[0])
		bb = plt.subplot(gs[3])
		ax = plt.subplot(gs[1])
	else:
		fig, ax = plt.subplots(figsize=(10,10)) 
	
	ax.spines['top'].set_visible(False)
	ax.spines['right'].set_visible(False)
	ax.spines['bottom'].set_visible(False)
	ax.spines['left'].set_visible(False)
	ax.get_xaxis().set_ticks([])
	ax.get_yaxis().set_ticks([])
	ax.tick_params(width=0) # , length=0 , color="white"
	#plt.tick_params(top='off', bottom='off', left='off', right='off', labelleft='off', labelbottom='on')
	li,la = limits
	if limits:
		plt.xlim(li,la)
		plt.ylim(li,la)
		ax.set_xlim([li,la])
		ax.set_ylim([li,la])
		if sidegraphs:
			aa.set_xlim([0, 1])
			aa.set_ylim([li,la])
			bb.set_xlim([li,la])
			bb.set_ylim([0, 1])
			
		
	for xx, yy, cc, mm, f1, f2 in zip(col1, col2, c, m, freq1, freq2):
		if f1<mini or f2<mini: 	
			if showUnderMini: ax.scatter(xx, yy, marker="x", c="lightGray", alpha=0.5)
		else:			ax.scatter(xx, yy, marker=mm, c=cc)
	if sidegraphs:
		aa.scatter([0.5 for _ in col1], col2, c=c, alpha=0.5) # 
		bb.scatter(col1, [0.5 for _ in col2], c=c, alpha=0.5) # 
	ax.set_xlabel(label1)
	ax.set_ylabel(label2)
	texts=[]
	if labels:
		for label, x, y, f1, f2 in zip(languageNames, col1, col2, freq1, freq2):
			if f1<mini or f2<mini: 	
				#texts+=[ax.annotate(label, xy=(x, y), fontsize=8, color="lightGray",xytext=(5,5),textcoords='offset points', alpha=0.5)]
				if showUnderMini: texts+=[ax.text(x, y, label, color="lightGray", fontsize=8, alpha=0.5)] # for adjustText
			else: 			
				#texts+=[ax.annotate(label, xy=(x, y), fontsize=8, color=groupColors.get(langnameGroup[label],'k'),xytext=(5,5), arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5),textcoords='offset points')] # without adjustText
				texts+=[ax.text(x, y, label, color=groupColors.get(langnameGroup[label],'k'), fontsize=8)] # for adjustText
		
	title=label1+" ∷ "+label2
	if minimalistic:
		ax.set_xticks([0,50,100], minor=False) # only the 50% is major
		ax.set_xticks([0,25,50,75,100], minor=True) # all 25% are minor
		ax.set_yticks([0,50,100], minor=False) # only the 50% is major
		ax.set_yticks([0,25,50,75,100], minor=True) # all 25% are minor
		ax.grid(which='both', axis='both',alpha=.5) # draw grid
		if sidegraphs:
			aa.set_xticks([], minor=False) 
			aa.set_yticks([], minor=False)
			bb.set_xticks([], minor=False) 
			bb.set_yticks([], minor=False)

	#pear,pval=pearsonr(col1, col2)
	spear,pval=spearmanr(col1, col2)
	#print("pp",pear,pval, title+((" r:"+str(round(pear*100))+"%") if pear>0 else "")+ " p:"+str(round(pval,4)))
	ax.set_title(title+(("  ρ:"+str(round(spear*100))+"%") if spear>0 else "")+ " p:"+str(round(pval,4)), y=1.05)
	ax.plot([0, 100], [0, 100], transform=ax.transData,alpha=.5, color="lightGray") # diagonal (all figure: 0, 1, transform=ax.transAxes
		
	print("***",title)
	
	adjust_text(texts, col1, col2, lim=33, # precision=0,
            force_text=(0.1, 0.5), force_points=(0.1, 0.5),
            expand_text=(1, 1), expand_points=(1, 1),
            arrowprops=dict(arrowstyle='-', color='gray', alpha=.5))
	
	plt.savefig('./figures/bidimscatter-{cols}.svg'.format(cols=title), format="svg") #, dpi=300)
	if show: plt.show()
	plt.close(fig)


def kde(df, x, y):
	title=x+" ∷ "+y
	with sns.axes_style('white'):
		sns.jointplot(df[x],df[y],df, xlim=(0,100), ylim=(0,100), kind='kde');
	plt.savefig('./figures/kde-{cols}.svg'.format(cols=title), format="svg") #, dpi=300)
	plt.close(fig)
	
	
	
def scatterFileColumns(filename, col1, col2, show=False):
	"""
	function allows to directly show the scatter for two columns of a given file
	"""
	df = pd.read_csv(filename,sep='\t',index_col=0)
	scatter(df.index,df[col1],df[col2],col1,col2, show, limits=(0,3))



def randomDistr(col, tries=10000):
	#print len(col)
	#for i in range(44):print random.randrange(len(col))
	pears = []
	for ti in range(tries):
		col1 = [random.choice(col) for i in range(len(col))]
		col2 = [random.choice(col) for i in range(len(col))]
		pear,pval=pearsonr(col1, col2)
		pears += [pear]
	#print pears
	print(describe(pears).mean)
	df = pd.DataFrame({  'pears': pears })
	print (df.describe())
	hist = df.hist(bins=100)
	plt.show()


############################################################################ main:
#######################################################################################




if __name__ == '__main__':
	###################################################################
	###################################################################
	#####UD
	# dfPositive, dfPosiCfc, dfFreq, dfDist, dfAbs = completeDf()
	###################################################################
	#interestingColumns = sorted([col for col in dfPositive.columns if col in standardUDFunctions + "subject object circ dependent total".split() or "-" in col or "anti" in col])
	##interestingColumns = [col for col in dfPositive.columns if col in standardUDFunctions + "subject object circ dependent total".split() or "-" in col or "anti" in col]
	#dfPositive[interestingColumns].to_csv("dfPositive.tsv", sep='\t', encoding='utf-8') # write out the complete dataframe
	
	####SUD
	#dfPositive, dfPosiCfc, dfFreq, dfDist, dfAbs = SUDdf()
	# dfPositive.to_csv("dfPositive.tsv", sep='\t', encoding='utf-8') # write out the complete dataframe
	# dfAbs.to_csv("dfAbs.tsv", sep='\t', encoding='utf-8') # write out the complete dataframe

	#### example usages: ###################################################
	
	#dff = pd.read_csv("synt.stat.tsv",sep='\t',index_col=1)
	#rdfAbs['freq']=dfFreq.drop(["OldFrench"])['total']
	#with pd.option_context('display.max_rows', None, 'display.max_columns', 3):
		#print dfAbs["total"]
	#rdfPositive.to_csv("rdfPositive.tsv", sep='\t', encoding='utf-8')
	#print({a:round(v,2) for a,v in dfPositive['subject'].to_dict().items()})
	#combineDataByLanguageGroup(rdfAbs)
	#findBiggestDiff("Naija","English", dfPositive)
	#findBiggestDiff("Italian","French", dfPositive)
	
	############################## histograms:
	#histogram(dfPositive, dfFreq,"subject", show=True)
	#numTokHistogram(dfFreq, show=False)
	#for func in dfPositive.columns: print "bar",func; histogram(dfPositive, dfFreq, func)
	#for func in importants: print "bar",func; histogram(dfPositive, dfFreq, func)
		
	############################## one dims:	
	
	### important for doing the one dim scatter:
	#allOneDims(dfPositive)
	#combineSvgs(pattern='unidimscat')
	
	### other function use:
	#languageNames, col, title, limits, show = info
	#oneDimScatter( (dfPositive.index, dfPositive["dependent"], "dependent", True, True) )
	#oneDimScatter(dfPositive.index, dfPositive["NOUN-object-VERB"], "NOUN-object-VERB", dfFreq, show=False)	
	#oneDimScatter( (dfPositive.index, dfPositive["NOUN-dependent-ADJ"], "NOUN-dependent-ADJ", True, False) )
	df = pd.read_csv(baseDataDir+"funcGov.tsv",sep='\t',index_col=0)
	print(df)
	oneDimScatter( (df.index, df["tree"], "tree", True, True) )
	
	############################## random:
	
	#randomDistr( dfPositive["dependent"])
	#randomDistr( dfPositive["ADP-object-NOUN"])

	############################## two dims:	
	

	### important for doing the two dim scatter:
	################### most important two lines!!!!!
	# allTwoDims(dfPositive, dfFreq)
	# combineSvgs(pattern='bidimscat')
	
	### other function use:
	#scatter(dfPositive.index, dfPositive[f], dfPositive[ff],f, ff, dfFreq, mini=50, minimalistic=True, sidegraphs=False, limits=(-10,110), show=False)
	#scatter(dfPositive.index, dfPositive['dependent'], dfPositive['antiaux'],'dependent', 'antiaux', dfFreq, mini=50, minimalistic=True, sidegraphs=False, limits=(-10,110), show=False)
	#scatter(dfPositive.index, dfPositive['subject-NOUN'], dfPositive['VERB-object-NOUN'],'subject-NOUN', 'VERB-object-NOUN', dfFreq, mini=10, minimalistic=True, sidegraphs=False, limits=(-10,110), show=False)
	#scatter(dfPositive.index, dfPositive['VERB-object-PRON'], dfPositive['VERB-object-NOUN'],'VERB-object-PRON', 'VERB-object-NOUN', dfFreq, mini=10, minimalistic=True, sidegraphs=False, limits=(-10,110), show=False, labels=False)


	#allTwoDimsKde(dfPositive, dfFreq)
	#combineSvgs(pattern='kde')
	#plt.show()
	
	#scatterFileColumns("udsnapshot/positive-direction.tsv","obj","xcomp", show=True)
	#scatterFileColumns("positive-direction.tsv","obj","ccomp")
	#scatterFileColumns("sududdist.tsv","SUD dependency distance","UD dependency distance")		

	#scatter(df.index,df["syntdist"]-1,dff["syntdist"]-1,"syntdist","syntdist", dfFreq, limits=(0,3), show=True)
	
	
	#scatter(dfPosiCfc.index, objects, dfPosiCfc["NOUN-amod->ADJ"],"object", "NOUNamodADJ")
	#scatter(timrdfAbs.index, timdfAbs["dependent"], timrdfAbs["dependent"], "dependent", "dependent", dfFreq, limits=(.5,3), show=True, mini=50, minimalistic=False)
	#scatter(timrdfAbs.index, dfAbs["dependent"], rdfAbs["dependent"], "dependent", "dependent", dfFreq, limits=(1.5,4), show=True, mini=50, minimalistic=False)



