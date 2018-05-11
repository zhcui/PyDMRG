import numpy as np
import time
import mps_opt
import matplotlib.pyplot as plt 
from sys import argv

#-----------------------------------------------------------------------------
# In this script, we use the mpo module to calculation the hamiltonian
# for various models (1D SEP, 2D SEP, 1D Heis, 2D Heis) and print each of
# these to the terminal
#-----------------------------------------------------------------------------

# Set Plotting parameters
plt.rc('text', usetex=True)
plt.rcParams['text.latex.preamble'] = [r'\boldmath']
plt.rc('font', family='serif')
plt.rcParams['text.latex.unicode']=False
np.set_printoptions(suppress=True)
np.set_printoptions(precision=2)
np.set_printoptions(linewidth=100)
plt.style.use('fivethirtyeight') #'fivethirtyeight') #'ggplot'

#-----------------------------------------------------------------------------
# 2D WASEP
#-----------------------------------------------------------------------------
N=3
n_points = 10
E = 10
px = 1/2*np.exp(-E/N)
qx = 1/2*np.exp(E/N)
s = np.linspace(-10,1,30)
s = np.array([-10])
CGF_dmrg = np.zeros(s.shape,dtype=np.complex128)
for i in range(len(s)):
    if s[i] > -20 and s[i] < 0:
        target_state = 2
    else:
        target_state = 0
    x = mps_opt.MPS_OPT(N = [N,N],
                        hamType = "sep_2d",
                        periodic_x = True,
                        periodic_y = True,
                        maxBondDim = 100,
                        maxIter = 10,
                        verbose = 5,
                        target_state = target_state,#target_state,
                        add_noise = False,
                        #plotConv = True,
                        #plotExpVals = True,
                        hamParams = (qx,px,1/2,1/2,0,0,0,0,0,0,0,0,[s[i]/N,0]))
    print('Performing Calculation for s = {}'.format(s[i]))
    CGF_dmrg[i] = x.kernel()
    print('Final Density Profile = \n{}'.format(x.calc_occ))
