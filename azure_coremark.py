vm_size =["A5","A5","A6","A7","Basic_A0","Basic_A1","Basic_A2","Basic_A3","Basic_A4","ExtraLarge","ExtraSmall","Large","Medium","Small","Standard_D1","Standard_D1_v2","Standard_D11","Standard_D11_v2","Standard_D12","Standard_D12_v2","Standard_D13","Standard_D13_v2","Standard_D14","Standard_D14_v2","Standard_D2","Standard_D2_v2","Standard_D3","Standard_D3_v2","Standard_D4","Standard_D4_v2","Standard_D5_v2","Standard_DS1","Standard_DS11","Standard_DS12","Standard_DS13","Standard_DS14","Standard_DS2","Standard_DS3"]

import os, sys

for size in vm_size:
    pkb_param="/home/xfy1dvr/projects/PerfKitBenchmarker/pkb.py"
    sys.argv =['--cloud=Azure','--benchmarks=coremark', '--cloud=Azure',  '--machine_type=' + size]
    #pkb_param="/home/xfy1dvr/projects/PerfKitBenchmarker/pkb.py --cloud=Azure --benchmarks=coremark --machine_type=" + size
    execfile(pkb_param)


