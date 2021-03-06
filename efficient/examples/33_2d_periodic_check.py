import numpy as np
import time
import mps_opt
import matplotlib.pyplot as plt

#-----------------------------------------------------------------------------
# Ensure that the 2D sep calculations are correct by doing a tasep calculation
# aligned in all four possible directions. Compare the results to ensure the 
# resulting energies are coincident.
#-----------------------------------------------------------------------------

# Set Plotting parameters
plt.rc('text', usetex=True)
plt.rcParams['text.latex.preamble'] = [r'\boldmath']
plt.rc('font', family='serif')
plt.rcParams['text.latex.unicode']=False
np.set_printoptions(suppress=True)
np.set_printoptions(precision=100)
plt.style.use('ggplot') #'fivethirtyeight') #'ggplot'

Nx = 8
Ny = 8
s = -1
a = 0.35
b = 2/3
x = mps_opt.MPS_OPT(N=Nx,
                    hamType="tasep",
                    plotConv = True,
                    plotExpVals = True,
                    periodic_x = True,
                    add_noise=False,
                    hamParams=(a,s,b))
x.kernel()
x1 = mps_opt.MPS_OPT(N=[Nx,Ny],
                    hamType="sep_2d",
                    periodic_x=True,
                    add_noise = False,
                    hamParams = (0,1,a,0,0,b,0,0,0,0,0,0,s))
E1 = x1.kernel()
x2 = mps_opt.MPS_OPT(N=[Nx,Ny],
                     hamType="sep_2d",
                     periodic_x = True,
                     add_noise = False,
                     hamParams = (1,0,0,a,b,0,0,0,0,0,0,0,-s))
E2 = x2.kernel()
x3 = mps_opt.MPS_OPT(N=[Ny,Nx],
                     hamType="sep_2d",
                     periodic_y=True,
                     add_noise = False,
                     hamParams = (0,0,0,0,0,0,1,0,0,a,b,0,-s))
E3 = x3.kernel()
x4 = mps_opt.MPS_OPT(N=[Ny,Nx],
                     hamType="sep_2d",
                     periodic_y = True,
                     add_noise = False,
                     hamParams = (0,0,0,0,0,0,0,1,a,0,0,b,s))
E4 = x4.kernel()
