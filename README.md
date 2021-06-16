There are in general 3 repositories in this project:
### 1) datapreparation
* statconll.py & conll.py : analyse and transform .conllu files in *treebank* folder, stock numerical results in .tsv files in an *-analysis* folder
*see relevant files for more details*
	- in conll.py 
		- class Tree(dict): transform each sentence in .collu files to a tree, with usuel fonction for dictionary and methodes like conllu() that transfrom a tree to conllu format
		- some fonctions to transform .conllu files to trees and vice versa, fonctions to transform text files to empty .conllu files and to replace node of tree.
		   
	- in statconll.py
		-from 3 .tsv files read languages' code and group, regroupe files in input folder by language
		-for each file in input folder, transform it to tree with conll.py, anayse each sentence(distance, number of relations etc.) and store results in a dict *typesDics*; then write results in files of *foldername-analyse* 
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

3 boot files added
<br/>
plot data prepared and sent by django
  
  
(lanch both backend and frontend to run the project)







