#  The Co-Effect of Menzerath’s Law and Heavy Constituent Shift in Natural Languages (Qualico paper)
# files download from https://nextcloud.ilpga.fr/index.php/s/gTMGsQ2yqzPyBZc?path=%2F , adapted for typometrics

## Important scripts

Main table (very long) built using the newmenzerath.py script

```python
version = "2.7
langConllFiles=getAllConllFiles("sud-treebanks-v"+version+"/", groupByLanguage=True)
newnewheavymenz(langConllFiles, "abc.languages.longfile.v2.7.tsv")
```


Then the table is put into the appropriate format (very large) for the typometrics site using the dataAnalysis.py script

```python
version="2.7"
main_dataframe = pd.read_csv("abc.languages.longfile.v{}.tsv".format(version), sep="\t")
outfile = "results_pandas/tables/abc.languages.v{}_typometricsformat_3.tsv".format(version)
makeLargeTable(main_dataframe, outfile)
```

## Important tables

+ abc.languages.longfile.v2.7.tsv
+ results_pandas/tables/abc.languages.v2.7_typometricsformat_3.tsv
+ results_pandas/tables/for_the_paper/abc.meanweights.languages.v2.7.csv
+ results_pandas/tables/for_the_paper/abc.number-of-occurences.languages.v2.7.csv