### compute distances between 2D graph:

STEP 0<br/>
* for language distribution and DTW:
```bash
python3 distance.py
```
* if distance.py doesn't work, try:
```bash
python3 distance1.py
```

* for stable matching 
```bash
python3 distanceMarry.py
```
<br/>

STEP 1<br/>
#### groups
'distance' is the current measure group,
to change it as 'menzerath' or 'direction'

* open *distance.py* in main fct, line329-331, change the comment '#' of group <br/>
```bash
   group = 'distance' 
    #group = 'direction'
    #group = 'menzerath'
```
* open *distanceMarry.py* in main fct, line293-295, change the comment '#' of group 


#### version
SUD as default version

UD:
* open *tsv2json.py*, at line 100-104, <br/>
```bash
dfsSUD = getRawData(sudFolder)
#dfsUD = getRawData(udFolder, sud = False)
dfs = dfsSUD #1162 min = 60 
#dfs = dfsUD #928 minnonzero = 60
```
<br/>
put them as follows:<br/>

```bash
#dfsSUD = getRawData(sudFolder)
dfsUD = getRawData(udFolder, sud = False)

#dfs = dfsSUD #1162 min = 60 
dfs = dfsUD #928 minnonzero = 60 
```

* open *distance.py* in main fct, line321, change version as **ud**
* open *distanceMarry.py* in main fct, line288, change version as **ud**

