import pandas as pd
import os,re, glob

from . import newmenzerath
#from newmenzerath import readInLanguageNames


# version="2.5"
# df = pd.read_csv("abc.languages.longfile.v{}.tsv".format(version), sep="\t")


# for x_type in ["root", "any","VERB", "content", "nominal"]:

#     if x_type == "root":
#             data = df[df["headrel"]=="root"]
#     elif x_type == "VERB":
#         data = df[df["headpos"]=="VERB"]
#     elif x_type == "nominal":
#         data = df[df["headpos"].isin(["NOUN", "PROPN"])]
#     elif x_type == "content":
#         data = df[df["headpos"].isin(["NOUN", "PROPN", "ADJ", "ADV", "VERB"])]
#     elif x_type == "any":
#         data = df

#     print("xtype", x_type, len(data))

#     for dep_type in ["content-phrase", "same","any" ]:

#         if dep_type == "any":
#             sub = data
#         elif dep_type == "same":
#             a_b = data[data["type"].isin(["a","b"])]
#             a_b["exists_samerel"] = a_b.duplicated(subset=["lang", "dir", "t_id", "h_id", "deprel"], keep=False)
#             a_b = a_b[a_b["exists_samerel"]==True]
#             a_b = a_b.drop(["exists_samerel"], axis=1)
#             c = data[data["type"]=="c"]
#             sub = pd.concat([a_b,c])
#         elif dep_type == "content-phrase":
#             sub = data[data["cw_inspan"]==True]
#             # print(sub)

#         print("dep_type", dep_type, len(sub))
#         sub.to_csv("results_pandas/abc.languages.v{}.xtype={}.deptype={}.tsv".format(version, x_type, dep_type), sep="\t")

        

# formatting data for the typometrics site
# from very long table to very large table




def makeLargeTable(main_dataframe, output_file):
    langNames, langnameGroup = newmenzerath.readInLanguageNames()
    print("read the table")

    languages = main_dataframe.lang.unique()
    language_names = [langNames[l_code] for l_code in languages]

    new_df = {}

    for num, l_code in enumerate(languages):

        print(num)
        df = main_dataframe[main_dataframe["lang"]==l_code]
        # type of governor
        for x_type in ["root", "any","VERB", "content", "nominal"]:

            if x_type == "any":
                data = df.copy()
            elif x_type == "root":
                data = df[df["headrel"]=="root"]
            elif x_type == "VERB":
                data = df[df["headpos"]=="VERB"]
            elif x_type == "nominal":
                data = df[df["headpos"].isin(["NOUN", "PROPN"])]
            elif x_type == "content":
                data = df[df["headpos"].isin(["NOUN", "PROPN", "ADJ", "ADV", "VERB"])]


            # print("governor type", x_type, data["type"].value_counts())

            # dependent type
            for dep_type in ["any","relevant","content-phrase", "same"]:

                if dep_type == "any":
                    sub = data.copy()

                elif dep_type == "relevant":

                    # for c
                    c = data[(data["type"] == "c") & (data["deprel"].isin(["comp", "mod", "udep", "subj"]))]

                    # for a and b, both must be in the list
                    a_b = data[(data["type"].isin(["a", "b"])) & (data["deprel"].isin(["subj", "mod", "comp", "udep"]))]
                    # print(len(a_b))

                    x = a_b[a_b.duplicated(subset=["lang", "dir", "t_id", "h_id"], keep=False)]
                    # a_b["exists_codep"] = a_b.duplicated(subset=["lang", "dir", "t_id", "h_id"], keep=False)

                    # x = a_b[a_b["exists_codep"]==True]
                    # y = x.drop(["exists_codep"], axis=1)

                    # if x_type == "root":
                    #     print(l_code, len(a_b), a_b["type"].value_counts(), "\n\n")
                    sub = pd.concat([x,c])

                    #print("!!dep_type = relevant \n", sub)

                elif dep_type == "same":
                    a_b = data[data["type"].isin(["a","b"])]
                    # a_b["exists_samerel"] = a_b.duplicated(subset=["lang", "dir", "t_id", "h_id", "deprel"], keep=False)
                    # x = a_b[a_b["exists_samerel"]==True]
                    # y = x.drop(["exists_samerel"], axis=1)
                    x = a_b[a_b.duplicated(subset=["lang", "dir", "t_id", "h_id", "deprel"], keep=False)]
                    # x = a_b[a_b["exists_samerel"]==True]
                    # y = x.drop(["exists_samerel"], axis=1)
                    c = data[data["type"]=="c"]
                    sub = pd.concat([x,c])
                elif dep_type == "content-phrase":

                    # there's a problem with this : what do we do when a has a content word in their span but not b ?
                    # it creates unequal number of occurences for a and b
                    # -> we only keep them if both a and b and a content word in their span
                    a_b = data[(data["type"].isin(["a","b"])) & (data["cw_inspan"]==True)]
                    # a_b["both_have_cw_span"] = a_b.duplicated(subset=["lang", "dir", "t_id", "h_id"], keep=False)
                    # x = a_b[a_b["both_have_cw_span"]==True]
                    # y = a_b.drop(["both_have_cw_span"], axis=1)
                    x = a_b[a_b.duplicated(subset=["lang", "dir", "t_id", "h_id"], keep=False)]
                    # x = a_b[a_b["both_have_cw_span"]==True]
                    # y = a_b.drop(["both_have_cw_span"], axis=1)
                    c = data[(data["type"]=="c")  & (data["cw_inspan"]==True)]
                    sub = pd.concat([x,c])
                    # print(sub)

                

                # direction
                for direction in ["left", "right", "any"]:


                    if direction == "any":
                        sub_1 = sub.copy()
                    else:
                        sub_1 = sub[sub["dir"]==direction]

                    # print("direction", direction, "occurences", len(sub_1))

                    # print(">", x_type, dep_type, direction, sub_1, "\n\n")
                    for config in ["a", "b", "c"]:

                        sub_2 = sub_1[sub_1["type"]==config]
                        # print(l_code, dep_type, config, len(sub_2))

                        # print("configuration", config, "occurences", len(sub_2))
                        # print(sub_2)
                        mean_weight = sub_2["weight"].mean()
                        # print(sub_2, len(sub_2))
                        column = "_".join([config, direction, x_type, dep_type])
                        # print(l_code, column, mean_weight)
                        nb_occurences = len(sub_2["weight"])
                        new_df[column] = new_df.get(column, [])+[round(mean_weight, 2)]
                        new_df["nb_"+column] = new_df.get("nb_"+column, [])+[len(sub_2)]

    print("all done, building the new table")


    col_names = list(new_df)
    final_df = pd.DataFrame(new_df, columns=col_names, index=language_names)
    final_df.to_csv(output_file, sep="\t")


def means(df_path, df_language_path):
    df = pd.read_csv(df_path, sep="\t")

    # governor are roots and dependents on the right
    data = df[(df["headpos"]=="VERB") & (df["dir"]=="right")]

    # dependents are relevant
    c = data[(data["type"] == "c") & (data["deprel"].isin(["comp", "mod", "udep", "subj"]))]
    a_b = data[(data["type"].isin(["a", "b"])) & (data["deprel"].isin(["subj", "mod", "comp", "udep"]))]
    # for a and b, both need to be relevant, so we make sure their friend has not been filtered out
    x = a_b[a_b.duplicated(subset=["lang", "dir", "t_id", "h_id"], keep=False)]
    sub = pd.concat([x,c])
    print("averaged over trees")
    y = sub.groupby(["type"])["weight"].mean()
    print(y)


    print("averaged over languages")
    df = pd.read_csv(df_language_path, sep="\t")
    a = df["a_right_VERB_relevant"]
    c = df["c_right_VERB_relevant"]
    m_a = round(a.mean(), 2)
    m_c = round(c.mean(), 2)
    print("a", m_a, "c", m_c)

if __name__ == "__main__":
    pass
    version="2.8_sud"
    outputFolder = "MenRes"
    Path(outputFolder).mkdir(parents=True, exist_ok=True)

    main_dataframe = pd.read_csv("abc.languages.longfile.v{}.tsv".format(version), sep="\t")
    # # main_dataframe = pd.read_csv("/home/marine/Téléchargements/todel.csv", sep="\t")
    #outfile = "results_pandas/tables/abc.languages.v{}_typometricsformat_4.tsv".format(version) 

    outfile = outputFolder + "/abc.languages.v{}_typometricsformat_4.tsv".format(version)
    makeLargeTable(main_dataframe, outfile)

    #means("abc.languages.longfile.v{}.tsv".format(version), outfile)
