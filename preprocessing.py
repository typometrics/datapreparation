import os

from statConll_fast import getAllConllFiles, checkLangCode

MB = 1024 * 1024

def split_file(fpath, k):
    dirname = os.path.dirname(fpath)
    print('====\nsplit ', fpath, k)
    fname = os.path.basename(fpath)
    conll_txt = open(fpath).read().strip().split('\n\n')
    len_subf = len(conll_txt)//k

    if '.' in fname:
        fname = '.'.join(fname.split('.')[:-1])

    for i in range(k):
        with open( os.path.join(dirname, f'{fname}_{i}.conllu'), 'w') as f:
            if i+1 != k:
                f.write('\n\n'.join(conll_txt[i*len_subf: (i+1)*len_subf]) + '\n\n' )
            else:
                f.write('\n\n'.join(conll_txt[i*len_subf:] ) + '\n\n' )
    # remove orginal file
    os.system(f'rm {fpath}')


def refact_file(langConllFiles, thred = 10):
    fpath_list = [(lcode, fpath) for lcode in langConllFiles.keys() for fpath in langConllFiles[lcode]]
    for p in fpath_list:
        la, fpath = p

        size_mb = int(os.path.getsize(fpath)/MB)

        if size_mb > thred:
            # split large file to parallelize
            split_file(fpath, size_mb//thred)


if __name__ == "__main__":
    conlldatafolder = 'test1'#"sud-treebanks-v2.11"
    langConllFiles = getAllConllFiles(conlldatafolder, groupByLanguage=True) 
    checkLangCode(langConllFiles)
    refact_file(langConllFiles, 2)

