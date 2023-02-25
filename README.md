


# how to use
* get the latest version of SUD or UD, unzip
* change the variable *conlldatafolder* in the preprocessing.py file to the name of the folder containing the new conllu files, for example sud-treebanks-v2.11
* in the last line of the preprocessing.py file, you can provide the maximum Mb size of files that should be split to speed up the processing. recommended value: 15
* start preprocessing.py: if language codes are missing, the script will stop, and you'll have to complete the .tsv files. Note that the original .conllu files will be erased.
* change the variable *conlldatafolder* in the statConll_fast.py file to the name of the folder containing the new conllu files. You may want to change also the analysisifolder variable to set the result folder. The variable `thesefuncs` has to be either sudfuncs or udfuncs. in the call of the computeMenzerath function, adapt the version.
* start statConll_fast.py. This may take some time.
* copy the resulting folder together with the updated 3 .tsv files at the root of djangotypometrics. Don't forgot to update the language groups in the [tsv2json.py](https://github.com/typometrics/djangotypometrics/blob/master/typometricsapp/tsv2json.py) file in the backend (djangotypometrics)

# structure of the whole typometrics repositories

There are in general 3 repositories in this project:
### 1) datapreparation
* statconll.py & conll.py : analyse and transform .conllu files in *treebank* folder, stock numerical results in .tsv files in an *-analysis* folder
*see relevant files for more details*
	- in conll.py 
		- class Tree(dict): transform each sentence in .conllu files to a tree, with usual fonctions for dictionary and methodes like conllu() that transfrom a tree to conllu format
		- some fonctions to transform .conllu files to trees and vice versa, fonctions to transform text files to empty .conllu files and to replace node of tree.
		   
	- in statconll.py
		- from 3 .tsv files read languages' code and group, regroupe files in input folder by language. These 3 files have to be updated in the datapreparation and in the backend (djangotypometrics):
			- languageCodes.tsv: code \t name of language
			- myLanguageCodes.tsv: If language is not in languageCodes.tsv or we prefer a shorter name to be used in the graph, the code and the name should be put here
			- languageGroups.tsv: name \t group. Each group name has to be linked to the appearance (color, shape) in the [tsv2json.py](https://github.com/typometrics/djangotypometrics/blob/master/typometricsapp/tsv2json.py) file in the backend (djangotypometrics).
		- for each file in input folder, transform it to tree with conll.py, anayse each sentence (distance, number of relations etc.) and store results in a dict *typesDics*; then write results in files of *foldername-analyse* 
* folders and files for django framwork, almost idem with *djangotypometrics*
    
### 2) djangotypometrics 
backend<br/>
* For each new project created with Django, there are a file manage.py and a folder with the project name, consisting of 5 .py files : <br/> __init__.py, asgi.py, setting.py, urls.py, wsgi.py
* In *typometricsapp*: 
	* urls.py & views.py for url and relevant fct; 
	* *tsv2json.py* : prepare data for scatter plot from .tsv files generated in *-analysis* folder  
* To run in dev etc. read the README.md in 2) 

### 3) quasartypometrics
frontend: vue + quasar<br/>
read the README.md in 3)

3 boot files added: axios.js, backend.js,i18n.js

<br/>
plot data prepared and sent by django
  
  
(launch both backend and frontend to run the project)


