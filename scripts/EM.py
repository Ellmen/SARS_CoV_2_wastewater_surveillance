#!/usr/bin/python3
import pandas as pd, numpy as np, time, sys, re
import feather as ft

dfD_path = "test_input/dfD.feather"
dfN_path = "test_input/dfN.feather"
SID_path = "test_input/SID.feather"

output_reads_filepath = "output.txt" # sys.argv[1]
eliminated_filepath = "test_input/eliminated.txt"

t0 = time.time()
output_mismatch_table_old = pd.read_csv(output_reads_filepath, sep="\t", header=0)
readin_time = time.time() - t0
print("Read in output mismatch reads", readin_time)

output_mismatch_table_old.rename(columns={output_mismatch_table_old.columns[0]:"read"}, inplace=True)
eliminated = pd.read_csv(eliminated_filepath, sep="\n", header=0)

print(output_mismatch_table_old.size)
print("col old: ", output_mismatch_table_old.columns)
for e in eliminated:
        print(e)
        print(output_mismatch_table_old[(output_mismatch_table_old["read"] == e)].index)
        output_mismatch_table = output_mismatch_table_old.drop(output_mismatch_table_old[(output_mismatch_table_old['read'] == e)].index)
print(output_mismatch_table.size)

# Get names of strains
print(output_mismatch_table.columns)
SID = pd.DataFrame(data=list(output_mismatch_table.columns[2:]))
SID = SID.rename(columns = {0 : "SID"})
ft.write_dataframe(SID, SID_path, compression='uncompressed')

# Rename labels for names of strains 
n = len(output_mismatch_table.columns) - 1

#col_names = ["read", "blockSizes"]
output_mismatch_table.rename(columns = {0 : "read", 1: "blockSizes"})
#col_names.extend(np.arange(n - 1))
#col_names = [str(n) for n in col_names]
#output_mismatch_table.columns = col_names
reads_col = output_mismatch_table["read"]

# output_mismatch_table = output_mismatch_table.rename(columns={x:y for x,y in zip(output_mismatch_table.columns,range(0, n + 1))})
## dfN
dfN_col = output_mismatch_table["blockSizes"]
dfN_col = pd.DataFrame(data=dfN_col)
dfN = pd.concat([reads_col, pd.concat([dfN_col] * (n-1), axis=1, ignore_index=True)], axis=1)
col_names = output_mismatch_table.columns[1:n+1]
col_names.insert(0, "read")
dfN.columns = col_names
print("col_names: ", col_names)

ft.write_dataframe(dfN, dfN_path, compression='uncompressed')
print("dfN: ", dfN)

## dfD
dfD = pd.concat([reads_col,output_mismatch_table.iloc[:,2:n+1]],axis = 1)
ft.write_dataframe(dfD, dfD_path, compression='uncompressed')
print("dfD: ", dfD)
