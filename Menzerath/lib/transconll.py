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

import collections, re
from itertools import chain, combinations
#from . import conll
import conll

debug=False
#debug=True


def powerset(iterable):
	"""
	powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
	"""
	xs = list(iterable)
	# note we return an iterator rather than a list
	return chain.from_iterable(combinations(xs,n) for n in range(len(xs)+1))

class TransGrammar():
	"""
	
	"""
	def __init__(self, transconll):
		self.transrules=[]
		doubleEmptyLine=re.compile("\n\s*\n\s*\n+")
		emptyLine=re.compile("\n\s*\n+")
		for ruleblock in doubleEmptyLine.split(transconll.strip()):
			inconll, outconll = emptyLine.split(ruleblock.strip())
			trees,outtree = self.checkGrammar(inconll, outconll)
			for tree in trees:
				#self.transrules+=[TransRule(tree,outtree)]
				try:
					self.transrules+=[TransRule(tree,outtree)]
				except Exception as e:
					print(str(e))
					raise TransRuleException("failed to read rule:\n"+ruleblock+"\nProbably wrong index, possibly pointing to an optional node\n"+str(e))
				
	def __repr__(self):
		return "TransGrammar with "+str(len(self.transrules))+" rules"
	
	
	def transform(self, othertree):
		for transrule in self.transrules:
			if debug: 
				print("doing",transrule)
				print("on:",othertree.conllu())
			matches = transrule.transform(othertree)
			if debug: 
				print("***")
				for match in matches:
					print("===",match)
		
	def checkGrammar(self, inconll, outconll):
		oblis, optis, comments, outs = [], [], [], []
		for i,li in enumerate(inconll.split("\n")):
			li=li.strip()
			if li[0]=="#": comments+=[(i,li)]
			elif li[0]=="?": optis+=[(i,li[1:])]
			else: oblis+=[(i,li)]
		for i,li in enumerate(outconll.split("\n")):
			li=li.strip()
			if li[0]=="#": continue
			else: outs+=[li]
		selection=oblis+optis
		realinconll="\n".join(li for (i,li) in sorted(comments+selection))
		tree = conll.conll2tree(realinconll)
		outtree=conll.conll2tree(outconll)
		# check
		assert(len(oblis+optis)==len(outs)) # in and out rules have the same number of elements
		assert(sorted(tree)==sorted(outtree))
		rootnodes=[]
		for i in sorted(tree):
			node = tree[i]                        
			govs=node.get("gov",{})
			assert(len(govs)<=1) # single governor
			assert(govs=={} or list(govs)[0] in tree or list(govs)[0]==0) # only self refs
			if list(govs)[0]==0: rootnodes+=[i]
		assert(len(rootnodes)==1) # has exactly one root
		trees=[]
		for choice in sorted(powerset(set(optis)),key=len,reverse=True):
			if debug: print("choice:",list(choice))
			if not len(choice): choice=[]
			selection=oblis+list(choice)
			realinconll="\n".join(li for (i,li) in sorted(comments+selection))
			trees += [conll.conll2tree(realinconll)]
			
		return trees, outtree	
	
	def adddiff(self, onetree, othertree):
		for i in onetree:
			onenode=onetree[i]
			othernode=othertree.get(i,{})
			if onenode.get('t',None)!=othernode.get('t',None):
				onenode['highlight']=onenode.get('highlight',"")+"highlight "
				othernode['highlight']=othernode.get('highlight',"")+"highlight "
			if onenode.get('tag',None)!=othernode.get('tag',None):
				onenode['highlight']=onenode.get('highlight',"")+"taghighlight "
				othernode['highlight']=othernode.get('highlight',"")+"taghighlight "
			if onenode.get('gov',None)!=othernode.get('gov',None):
				onenode['highlight']=onenode.get('highlight',"")+"dephighlight "
				othernode['highlight']=othernode.get('highlight',"")+"dephighlight "

class TransRuleException(Exception):
    pass

class TransRule():
	"""
	individual rule
	intree: MatchTree, 
	outtree: Tree,
	"""
	def __init__(self, intree, outtree):
		
		self.matchtree = MatchTree(intree)
		self.outtree = outtree
		#self.rootid = rootid
		self.outdic={}
		for i in sorted(self.matchtree):
			self.outdic[i]={}
			for a,v in self.outtree[i].items():
				if v=="_" or v=="" or a=='id' or v=={}: continue
				self.outdic[i].update({a:v})
		#print("matchdic:",self.matchdic)
		
	def __repr__(self):
		return "\n".join(["TransRule:",self.matchtree.conllu(),"----",self.outtree.conllu() ])
	
	
	def transform(self, othertree):
		"""
		central function: applies the rule to othertree
		
		"""
		matches=[]
		for mdic in self.matchtree.search(othertree): # for each match
			if debug: print("**trying mdic",mdic)
			variables={}
			corrs={0:0}
			corrs={}
			#.get(gi,list(othertree[oid][a])[0])
			#print(mdic)			
			self.instaVar(mdic, othertree, corrs, variables)
			if debug: print("var",variables,"corrs",corrs)
			self.change(corrs, othertree, variables)
			self.matchtree.addInfo(othertree) # TODO: think about this!
			#print(othertree)
			matches+=[mdic]
		return matches
	
	def instaVar(self, mdic, othertree, corrs, variables):
		"""
		recursive function
		instantiates the $variables for a specific match mdic
		"""
		mid, oid = list(mdic)[0]
		corrs[mid] = oid
		for a,v in self.matchtree[mid].items():
			if isinstance(v, str) and v[0]=='$': variables[a]=othertree[oid].get(a,"_")
		govrel=list(self.matchtree[mid]['gov'].items())[0][1]
		if govrel[0]=='$': variables[govrel]= list(othertree[oid]['gov'].items())[0][1]
		if list(self.matchtree[mid]['gov'].items())[0][0]==0: corrs[0] = list(othertree[oid]['gov'].items())[0][0]
			
		for kidid, kidil in mdic[(mid, oid)].items():
			subdic = sorted(kidil, key=lambda d: sorted(d))[0] # dictionary with lowest keys: no multiple matches!
			self.instaVar( subdic, othertree, corrs, variables)
			
	def change(self, corrs, othertree, variables):
		"""
		applies new values to othertree for a given match
		"""
		for mid, oid in corrs.items():
			if not mid: continue # case 0 (root)
			#print("µµµ",mid, oid,self.outdic[mid])
			for a,v in self.outdic[mid].items():
				if isinstance(v, dict):
					gi,f = list(v.items())[0]
					if f[0]=='$': f=variables[f]
					othertree[oid][a]={corrs[gi]:f}
				else:
					if v[0]=='$': v=variables[v]
					othertree[oid].update({a:v})
					
		
			
		
class MatchTree(conll.Tree):
	"""
	
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		#self.update(*args, **kwargs)
		self.rootid = self.addInfo(self)
		self.matchdic={}
		for i in sorted(self):
			#print(self[i])
			self.matchdic[i]={}
			for a,v in self[i].items():
				if v=="_" or v=="" or a=='id' or isinstance(v, dict) or v[0]=='$': continue
				v=v.replace("||","|")
				self.matchdic[i].update({a:re.compile(r'\b('+v+r')\b')})
		#print("matchdic:",self.matchdic)
		
		
		
				
	def search(self, othertree):
		"""
		checks whether self matches somewhere the othertree
		if yes, returns a list of matching dics, if not, returns an empty list
		the list of matching dics is of the form
		[{(3, 4): {1: [{(1, 2): {}}, {(1, 15): {}}], 2: [{(2, 3): {}}]}}]
		which means: One root match at the node 4 of the other tree, 
		my node 1 matches twice: once at 2, and once at 15, 
		my node 2 matches only onde: at node 3
		"""
		self.addInfo(othertree)
		return self.findsubtree(othertree, otherrestriction=sorted(othertree), startid=self.rootid, alreadyMatched=[])
		
	def findsubtree(self, othertree, otherrestriction, startid, alreadyMatched):
		"""
		recursive function
		othertree: tree to search in
		otherrestriction: node ids allowed to search in
		startid: my own node to start matching
		"""
		#print("findsubtree:",otherrestriction,startid,alreadyMatched,"***")
		matchsubtrees=[]
		for i in sorted(set(otherrestriction)-set(alreadyMatched)):
			onode = othertree[i]
			if self.nodematch(self.matchdic[startid], onode):
				if debug:
					print("matched",startid,self.matchdic[startid])
					print ("with:", i, onode)
				tempalma=[i]
				mykids=self[startid].get("kids",{})
				if debug: print("mykids:",mykids)
				msts={}
				for mkid in mykids:
					res=self.findsubtree(othertree, [oid for (oid, of) in onode.get("kids",{}).items() if self.matchdic[mkid]['govrel'].match(of)], mkid, tempalma)
					if res: 
						if debug:print("res:",res,list(res[0])[0][1])
						msts[mkid]=res
						tempalma+=[list(res[0])[0][1]] # adding the last matched id from othertree to tempalma (temporary alreadyMatched)
				if len(msts)==len(mykids):
					matchsubtree={(startid,i):msts}
					matchsubtrees+=[matchsubtree]
					#break # TODO: check this! if breaking here, a rule is only applied once
		#print("returning:",matchsubtrees,"***")				
		return matchsubtrees				
						
		
	def nodematch(self, mymatchnode, othernode):
		for a,v in mymatchnode.items():
			if a in othernode:
				#print("mmm",a,v,othernode[a],v.match(othernode[a]))
				if not v.match(othernode[a]):return False
		return True


		
	def addInfo(self,tree):
		"""
		adding kids and govrel
		"""
		rootid = None
		for i in tree:
			tree[i]['kids'] = {}
			tree[i]['govrel'] = "_"
		for i in sorted(tree):
			for govi,func in tree[i].get("gov",{}).items():
				if govi>0:
					tree[govi]['kids'].update({i:func})
				elif govi==0: rootid = i
				if func[0]!='$': tree[i]['govrel'] = func
		
		return rootid
	


class SearchGrammar():
	"""
	
	"""
	def __init__(self, searchconll):
		self.matchtrees=[]
		doubleEmptyLine=re.compile("\n\s*\n\s*\n+")
		emptyLine=re.compile("\n\s*\n+")
		for inconll in emptyLine.split(searchconll.strip()):
			trees = self.checkGrammar(inconll)
			for tree in trees:
				#print("ùùùù",tree)
				self.matchtrees += [MatchTree(tree)]
				
				
	def __repr__(self):
		return "SearchGrammar with "+str(len(self.matchtrees))+" trees"
	
	def findall(self, othertree):
		"""
		central function: searches in othertree
		returns a list of roots where a match was detected
		"""
		matchroots=[]
		for matchtree in self.matchtrees:
			#print( "***",matchtree,matchtree.search(othertree))
			for mdic in matchtree.search(othertree): # for each match
				if list(mdic)[0][1] in matchroots:
					continue
				if debug: print("ùùù**   found mdic",mdic)
				matchtree.addInfo(othertree) # TODO: think about this!
				self.addHighlight(othertree, mdic)
				matchroots+=[list(mdic)[0][1]]
		return matchroots
		
	def checkGrammar(self, inconll):
		oblis, optis, comments = [], [], []
		for i,li in enumerate(inconll.split("\n")):
			li=li.strip()
			if li[0]=="#": comments+=[(i,li)]
			elif li[0]=="?": optis+=[(i,li[1:])]
			else: oblis+=[(i,li)]
		selection=oblis+optis
		realinconll="\n".join(li for (i,li) in sorted(comments+selection))
		tree = conll.conll2tree(realinconll)
		# check
		rootnodes=[]
		for i in sorted(tree):
			node = tree[i]                        
			govs=node.get("gov",{})
			assert(len(govs)<=1) # single governor
			assert(govs=={} or list(govs)[0] in tree or list(govs)[0]==0) # only self refs
			if list(govs)[0]==0: rootnodes+=[i]
		assert(len(rootnodes)==1) # has exactly one root
		trees=[]
		for choice in sorted(powerset(set(optis)),key=len,reverse=True):
			if debug: print("choice:",list(choice))
			if not len(choice): choice=[]
			selection=oblis+list(choice)
			realinconll="\n".join(li for (i,li) in sorted(comments+selection))
			trees += [conll.conll2tree(realinconll)]
			
		return trees	
	
	def addHighlight(self, othertree, mdic):
		mid, oid = list(mdic)[0]
		onenode=othertree[oid]
		onenode['highlight']="highlight"
		for kidid, kidil in mdic[(mid, oid)].items():
			subdic = sorted(kidil, key=lambda d: sorted(d))[0] # dictionary with lowest keys: no multiple matches!
			self.addHighlight(othertree, subdic)
		

	
	
	
if __name__ == "__main__":
		
	#tr = TransGrammar(open("UDtoSUD.txt").read())
	sg = SearchGrammar(open("search.udauxaux.conllu").read())
	#print(tr.search(conll.conllFile2trees("example.conllu")[0]))
	#tree = conll.conllFile2trees("example.conllu")[0]
	tree = conll.conllFile2trees("../ud-treebanks-v2.1/UD_French-Sequoia/fr_sequoia-ud-test.conllu")[9]
	
	##tr.transform(tree)
	print(sg.findall(tree))
	
	print(tree.conllu())







