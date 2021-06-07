There are in general 3 repositories in this project:
### 1) datapreparation
* statconll.py & conll.py : analyse and transform .conllu files in *treebank* folder, stock numerical results in .tsv files in an *-analysis* folder
	- in conll.py 
	- in statconll.py
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


