import pandas as pd

def tsvjson():

	df = pd.read_csv("results_pandas/abc.languages.v2.4.xtype={xtype}.deptype={deptype}.tsv".format(xtype=xtype, deptype=deptype), sep="\t") 
