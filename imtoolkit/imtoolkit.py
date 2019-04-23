# Copyright (c) IMToolkit Development Team
# This toolkit is released under the MIT License, see LICENSE.txt

import os
import sys
import time
import math
import itertools
import numpy as np
from scipy import special
from imtoolkit import *

def main():
    if os.getenv("USECUPY") == "1" and importlib.util.find_spec("cupy") != None:
        print("CuPy-aided GPGPU acceleration is activated in your environment.")
    else:
        print("NumPy is used for all the calculations.")
        print("The use of CUDA and CuPy is recommended.")
        print("> export USECUPY=1")
    print("")
    
    if len(sys.argv) <= 1 or (len(sys.argv) == 2 and "-h" in sys.argv[1]):
        print("Basic usage:")
        print("    > imtoolkit {MODE}_code=index_dm={dic,wen,opt}_ + parameters")
        print("    The execution mode can be switched by the ... ")
        print("")
        print("Usage examples:")
        print("    Check the transmission rate:")
        print("        > imtoolkit RATE_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK")
        print("    Check the IM codewords:")
        print("        > imtoolkit VIEW_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK")
        print("        > imtoolkit VIEW_code=index_dm=wen_M=16_K=8_Q=16_L=1_mod=PSK")
        print("        > imtoolkit VIEW_code=index_dm=opt_M=16_K=8_Q=16_L=1_mod=PSK")
        print("        > imtoolkit VIEWIM_code=index_dm=opt_M=16_K=8_Q=16")
        print("        > imtoolkit VIEWIMTEX_code=index_dm=opt_M=16_K=8_Q=16")
        print("    Check the minimum Euclidean distance of IM codewords:")
        print("        > imtoolkit MED_channel=rayleigh_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK")
        print("        > imtoolkit MED_channel=ofdm_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK")
        print("")
        print("    Spatial modulation over ideal Rayleigh fading channels:")
        print("        > imtoolkit BER_sim=coh_channel=rayleigh_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK_N=1_IT=1e6_snrfrom=0.00_to=50.00_len=11")
        print("        > imtoolkit BERP_sim=coh_channel=rayleigh_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK_N=1_ITo=1e2_ITi=1e4_snrfrom=0.00_to=50.00_len=11")
        print("        > imtoolkit AMI_sim=coh_channel=rayleigh_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK_N=1_IT=1e4_snrfrom=-20.00_to=30.00_len=11")
        print("        > imtoolkit AMIP_sim=coh_channel=rayleigh_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK_N=1_ITo=1e1_ITi=1e3_snrfrom=-20.00_to=30.00_len=11")
        print("")
        print("    Subcarrier-index modulation over ideal frequency-selective OFDM channels:")
        print("        > imtoolkit BER_sim=coh_channel=ofdm_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK_IT=1e6_snrfrom=0.00_to=50.00_len=11")
        print("        > imtoolkit BERP_sim=coh_channel=ofdm_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK_ITo=1e2_ITi=1e4_snrfrom=0.00_to=50.00_len=11")
        print("        > imtoolkit AMI_sim=coh_channel=ofdm_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK_IT=1e5_snrfrom=-20.00_to=30.00_len=11")
        print("        > imtoolkit AMIP_sim=coh_channel=ofdm_code=index_dm=dic_M=2_K=1_Q=2_L=2_mod=PSK_ITo=1e1_ITi=1e4_snrfrom=-20.00_to=30.00_len=11")

        quit()
    
    args = sys.argv[1:]
    for arg in args:
        print("-" * 50)
        print("arg = " + arg)
        params = Parameters(arg)

        # initialize a codebook, which also supports BLAST/OFDM by setting M = K
        meanPower = 1 # For the MIMO scenario, the mean power is normalized to 1
        if params.channel == "ofdm":
            # For the OFDM scenario, the mean power of symbol vectors is normalized to M
            meanPower = params.M
        code = IMCode(params.dm, params.M, params.K, params.Q, params.mod, params.L, meanPower)
        
        # initialize a channel generator
        if params.channel == "rayleigh": # quasi-static Rayleigh fading
            if re.match(r'.*P$', params.mode):
                # Parallel channel
                channel = IdealRayleighChannel(params.ITi, params.M, params.N)
            else:
                # Single channel
                channel = IdealRayleighChannel(1, params.M, params.N)
        elif params.channel == "ofdm": # ideal frequency-selective OFDM channel
            params.N = params.M
            if re.match(r'.*P$', params.mode):
                # Parallel channel
                channel = IdealOFDMChannel(params.ITi, params.M)
            else:
                # Single channel
                channel = IdealOFDMChannel(1, params.M)

        # initialize a simulator
        sim = CoherentMLDSimulator(code.codes, channel)

        start_time = time.time()

        if params.mode == "RATE":
            code.putRate()
        elif params.mode == "MED":
            print("MED = " + str(getMinimumEuclideanDistance(code.codes)))
        elif params.mode == "BER":
            sim.simulateBERReference(params)
        elif params.mode == "BERP":
            sim.simulateBERParallel(params)
        elif params.mode == "AMI":
            sim.simulateAMIReference(params)
        elif params.mode == "AMIP":
            sim.simulateAMIParallel(params)
        elif params.mode == "VIEW":
            print(code.codes)
        elif params.mode == "VIEWIM":
            print(np.array(convertIndsToVector(code.inds, params.M)).reshape(-1, params.Q))
            print("Minimum Hamming distance = %d" % getMinimumHammingDistance(code.inds, params.M))
            print("Inequality L1 = %d" % getInequalityL1(code.inds, params.M))
        elif params.mode == "VIEWIMTEX":
            
            print("$\\A(%d,%d,%d) = [$" % (params.M, params.K, params.Q))
            #[\e_1 ~ \e_2], [\e_1 ~ \e_3], [\e_2 ~ \e_4], [\e_3 ~ \e_4] 
            #for iarr in code.inds:
            #    print(" ~ ".join(["\\e_{%d}" % i for i in iarr]))
            es = [" ~ ".join(["\\e_{%d}" % i for i in iarr]) for iarr in code.inds]
            print(",\n".join(["$[" + e + "]$" for e in es]))
            #print(",".join(["[" + iarrstr + "]\n" for iarrstr in " ~ ".join(["\\e_{%d}" % i for i in iarr])]))
            print("$] \\inbb{B}{%d \\times %d \\times %d}.$" % (params.Q, params.M, params.K))
            

        elapsed_time = time.time() - start_time
        print ("Elapsed time = %.10f seconds" % (elapsed_time))
