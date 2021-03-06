import numpy as np
import scipy.linalg as la
np.set_printoptions(precision=1,linewidth=250)

######## Inputs ############################################################################
# SEP Model
N = 8
alpha = 0.35  # In at left
beta = 2/3    # Exit at right
s = 1         # Exponential weighting
p = 1         # Jump right
# Optimization
tol = 1e-5
maxIter = 10
maxBondDim = 16
startRightCanonical = True # This currently has to be true...
printlots = True
############################################################################################

######## MPO ###############################################################################
Sp = np.array([[0,1],[0,0]])
Sm = np.array([[0,0],[1,0]])
n = np.array([[0,0],[0,1]])
v = np.array([[1,0],[0,0]])
I = np.array([[1,0],[0,1]])
z = np.array([[0,0],[0,0]])
W = []
W.insert(len(W),np.array([[alpha*(np.exp(-s)*Sm-v),np.exp(-s)*Sp,-n,I]]))
for i in range(N-2):
    W.insert(len(W),np.array([[I,z,z,z],[Sm,z,z,z],[v,z,z,z],[z,np.exp(-s)*Sp,-n,I]]))
W.insert(len(W),np.array([[I],[Sm],[v],[beta*(np.exp(-s)*Sp-n)]]))
############################################################################################

# Exact Diagonalization ####################################################################
H = np.zeros((2**N,2**N))
occ = np.zeros((2**N,N),dtype=int)
sum_occ = np.zeros(2**N)
for i in range(2**N):
    occ[i,:] = np.asarray(list(map(lambda x: int(x),'0'*(N-len(bin(i)[2:]))+bin(i)[2:])))
    sum_occ[i] = np.sum(occ[i,:])
# Calculate Hamiltonian
for i in range(2**N):
    i_occ = occ[i,:]
    for j in range(2**N):
        j_occ = occ[j,:]
        tmp_mat = np.array([[1]])
        for k in range(N):
            tmp_mat = np.einsum('ij,jk->ik',tmp_mat,W[k][:,:,i_occ[k],j_occ[k]])
        H[i,j] += tmp_mat[[0]]
# Diagonalize Hamiltonian
e,lwf_ed,rwf_ed = la.eig(H,left=True)
inds = np.argsort(e)
lwf_ed = lwf_ed[:,inds[-1]]
rwf_ed = rwf_ed[:,inds[-1]]
# Ensure Proper Normalization
# <-|R> = 1
# <L|R> = 1
rwf_ed = rwf_ed/np.sum(rwf_ed)
lwf_ed = lwf_ed/np.sum(lwf_ed*rwf_ed)
print('Exact Diagonalization Energy: {}'.format(e[inds[-1]]))
############################################################################################

# Decompose States into MPS ################################################################
psir = np.zeros([2]*N,dtype=np.complex128)
psil = np.zeros([2]*N,dtype=np.complex128)
occ = np.zeros((2**N,N),dtype=int)
for i in range(2**N):
    occ[i,:] = np.asarray(list(map(lambda x: int(x),'0'*(N-len(bin(i)[2:]))+bin(i)[2:])))
psir = np.reshape(rwf_ed,[2]*N)
psil = np.reshape(lwf_ed,[2]*N)

# Determine Matrix Dimensions
fbd_site = []
mbd_site = []
fbd_site.insert(0,1)
mbd_site.insert(0,1)
for i in range(int(N/2)):
    fbd_site.insert(-1,2**i)
    mbd_site.insert(-1,min(2**i,maxBondDim))
for i in range(int(N/2))[::-1]:
    fbd_site.insert(-1,2**(i+1))
    mbd_site.insert(-1,min(2**(i+1),maxBondDim))
# Decompose Wavefunction from the right -------------------------------------------------
Mr = [] # Ordering (sigma,a_0,a_1)
Ml = []
for i in range(N,1,-1):
    psir = np.reshape(psir,(2**(i-1),-1))
    psil = np.reshape(psil,(2**(i-1),-1))
    (ur,sr,vr) = np.linalg.svd(psir,full_matrices=False)
    (ul,sl,vl) = np.linalg.svd(psil,full_matrices=False)
    # make left eigenvector right-canonical
    Xgauge = np.conj(np.linalg.inv(np.einsum('ij,kj->ki',vr,np.conj(vl))))
    vl_original = vl
    vl = np.dot(Xgauge,vl)
    Br = np.reshape(vr,(fbd_site[i-1],2,mbd_site[i]))
    Bl = np.reshape(vl,(fbd_site[i-1],2,mbd_site[i]))
    Br = Br[:mbd_site[i-1],:,:mbd_site[i]] 
    Bl = Bl[:mbd_site[i-1],:,:mbd_site[i]]
    Br = np.swapaxes(Br,0,1)
    Bl = np.swapaxes(Bl,0,1)
    Mr.insert(0,Br)
    Ml.insert(0,Bl)
    psir = np.einsum('ij,j->ij',ur[:,:mbd_site[i-1]],sr)
    psil = np.einsum('ij,j,jk->ik',ul[:,:mbd_site[i-1]],sl,np.linalg.inv(Xgauge))
Mr.insert(0,np.reshape(psir,(2,1,min(2,maxBondDim))))
Ml.insert(0,np.reshape(psil,(2,1,min(2,maxBondDim))))
##############################################

# Now Calculate State from MPS ###############
occ = np.zeros((2**N,N),dtype=int)
sum_occ = np.zeros(2**N)
for i in range(2**N):
    occ[i,:] = np.asarray(list(map(lambda x: int(x),'0'*(N-len(bin(i)[2:]))+bin(i)[2:])))
    sum_occ[i] = np.sum(occ[i,:])
# Calculate Wavefunction
rwf_dmrg = np.zeros(2**N,dtype=np.complex128)
lwf_dmrg = np.zeros(2**N,dtype=np.complex128)
for i in range(2**N):
    i_occ = occ[i,:]
    tmp_matr = np.array([[1]])
    tmp_matl = np.array([[1]])
    for k in range(N):
        tmp_matr = np.einsum('ij,jk->ik',tmp_matr,Mr[k][i_occ[k],:,:])
        tmp_matl = np.einsum('ij,jk->ik',tmp_matl,Ml[k][i_occ[k],:,:])
    #print(np.sum(tmp_mat-tmp_matl))
    rwf_dmrg[i] = tmp_matr[0,0]
    lwf_dmrg[i] = tmp_matl[0,0]
print('Difference Between Left  ED & MPS WFs: {}'.format(np.sum(np.abs(lwf_dmrg-lwf_ed))))
print('Difference Between Right ED & MPS WFs: {}'.format(np.sum(np.abs(rwf_dmrg-rwf_ed))))
##############################################

# Create F ###################################
F = []
F.insert(len(F),np.array([[[1]]]))
for i in range(int(N/2)):
    F.insert(len(F),np.zeros((min(2**(i+1),maxBondDim),4,min(2**(i+1),maxBondDim))))
for i in range(int(N/2)-1,0,-1):
    F.insert(len(F),np.zeros((min(2**(i),maxBondDim),4,min(2**i,maxBondDim))))
F.insert(len(F),np.array([[[1]]]))
# Calculate Initial Values
for i in range(int(N)-1,0,-1):
    F[i] = np.einsum('bxc,ydbe,eaf,cdf->xya',np.conj(Ml[i]),W[i],Mr[i],F[i+1])
##############################################

# Create Small F #############################
Fs = [None]*(N+1)
Fs[-1] = np.array([1])
for i in range(int(N)-1,-1,-1):
    Fs[i] = np.einsum('ijk,k->j',Mr[i],Fs[i+1])
##############################################

# Optimization Sweeps ########################
converged = False
iterCnt = 0
E_prev = 0
#density_avg = np.zeros(N)
while not converged:
# Right Sweep ----------------------------
    print('Right Sweep {}'.format(iterCnt))
    for i in range(N-1):
        if True:
            Mr_prev = np.reshape(Mr[i],-1)
            Ml_prev = np.reshape(Ml[i],-1)
        H = np.einsum('jlp,lmin,kmq->ijknpq',F[i],W[i],F[i+1])
        (n1,n2,n3,n4,n5,n6) = H.shape
        H = np.reshape(H,(n1*n2*n3,n4*n5*n6))
        u,vl,vr = la.eig(H,left=True)
        # select max eigenvalue
        max_ind = np.argsort(u)[-1]
        E = u[max_ind]
        vr = vr[:,max_ind]
        vl = vl[:,max_ind]
        print('\tEnergy at site {}= {}'.format(i,E))
        Mr[i] = np.reshape(vr,(n1,n2,n3))
        Ml[i] = np.reshape(vl,(n1,n2,n3))
        # Correct Normalization
        norm_factor = np.einsum('j,ijk,k->',Fs[i-1],Mr[i],Fs[i+1])
        Mr[i] /= norm_factor
        Ml[i] /= np.einsum('ijk,ijk->',Mr[i],np.conj(Ml[i]))
        ## Calculate Local Density
        #density_avg[i] = np.einsum('ijk,il,ljk->',np.conj(Ml[i]),v,Mr[i])
        #print('\t\tAveraged Density[{}] = {}'.format(i,density_avg[i]))
        # Put into Canonical Form
        Mr_reshape = np.reshape(Mr[i],(n1*n2,n3))
        Ml_reshape = np.reshape(Ml[i],(n1*n2,n3))
        (ur,sr,vr) = np.linalg.svd(Mr_reshape,full_matrices=False)
        (ul,sl,vl) = np.linalg.svd(Ml_reshape,full_matrices=False)
        # Gauge Transform of Left State
        Xgauge = np.linalg.inv(np.einsum('ji,jk->ik',np.conj(ur),ul))
        ul = np.dot(ul,Xgauge)
        sl = np.einsum('ij,jk->ik',np.linalg.inv(Xgauge),np.diag(sl))
        Mr[i] = np.reshape(ur,(n1,n2,n3))
        Mr[i+1] = np.einsum('i,ij,kjl->kil',sr,vr,Mr[i+1])
        Ml[i] = np.reshape(ul,(n1,n2,n3))
        Ml[i+1] = np.einsum('ij,jk,lkm->lim',sl,vl,Ml[i+1])
        # Update F and Fs
        F[i+1] = np.einsum('jlp,ijk,lmin,npq->kmq',F[i],np.conj(Ml[i]),W[i],Mr[i])
        Fs[i] = np.einsum('j,ijk->k',Fs[i-1],Mr[i])
# Left Sweep -----------------------------
    print('Left Sweep {}'.format(iterCnt))
    for i in range(N-1,0,-1):
        if printlots:
            Mr_prev = np.reshape(Mr[i],-1)
            Ml_prev = np.reshape(Ml[i],-1)
        H = np.einsum('jlp,lmin,kmq->ijknpq',F[i],W[i],F[i+1])
        (n1,n2,n3,n4,n5,n6) = H.shape
        H = np.reshape(H,(n1*n2*n3,n4*n5*n6))
        u,vl,vr = la.eig(H,left=True)
        # select max eigenvalue
        max_ind = np.argsort(u)[-1]
        E = u[max_ind]
        vr = vr[:,max_ind]
        vl = vl[:,max_ind]
        print('\tEnergy at site {}= {}'.format(i,E))
        Mr[i] = np.reshape(vr,(n1,n2,n3))
        Ml[i] = np.reshape(vl,(n1,n2,n3))
        # Correct Normalization
        norm_factor = np.einsum('j,ijk,k->',Fs[i-1],Mr[i],Fs[i+1])
        Mr[i] /= norm_factor
        Ml[i] /= np.einsum('ijk,ijk->',Mr[i],np.conj(Ml[i]))
        ## Calculate Local Density
        #density_avg[i] = np.einsum('ijk,il,ljk->',np.conj(Ml[i]),v,Mr[i])
        #print('\t\tAveraged Density[{}] = {}'.format(i,density_avg[i]))
        # Put into Canonical Form
        Mr_reshape = np.swapaxes(Mr[i],0,1)
        Mr_reshape = np.reshape(Mr_reshape,(n2,n1*n3))
        Ml_reshape = np.swapaxes(Ml[i],0,1)
        Ml_reshape = np.reshape(Ml_reshape,(n2,n1*n3))
        (ur,sr,vr) = np.linalg.svd(Mr_reshape,full_matrices=False)
        (ul,sl,vl) = np.linalg.svd(Ml_reshape,full_matrices=False)
        # Determine X and Xinv
        Xgauge = np.conj(np.linalg.inv(np.einsum('ij,kj->ki',vr,np.conj(vl))))
        vl = np.dot(Xgauge,vl)
        sl = np.einsum('ij,jk->ik',np.diag(sl),np.linalg.inv(Xgauge))
        Mr_reshape = np.reshape(vr,(n2,n1,n3))
        Ml_reshape = np.reshape(vl,(n2,n1,n3))
        Mr[i] = np.swapaxes(Mr_reshape,0,1)
        Ml[i] = np.swapaxes(Ml_reshape,0,1)
        Mr[i-1] = np.einsum('klj,ji,i->kli',Mr[i-1],ur,sr)
        Ml[i-1] = np.einsum('klj,ji,im->klm',Ml[i-1],ul,sl)
        # Update F
        F[i] = np.einsum('bxc,ydbe,eaf,cdf->xya',np.conj(Ml[i]),W[i],Mr[i],F[i+1])
        Fs[i] = np.einsum('ijk,k->j',Mr[i],Fs[i+1])
# Convergence Test -----------------------
    if np.abs(E-E_prev) < tol:
        print('#'*75+'\nConverged at E = {}'.format(E)+'\n'+'#'*75)
        converged = True
    elif iterCnt > maxIter:
        print('Convergence not acheived')
        converged = True
    else:
        iterCnt += 1
        E_prev = E
##############################################

##############################################
# Now Calculate State from MPS ###############
occ = np.zeros((2**N,N),dtype=int)
sum_occ = np.zeros(2**N)
for i in range(2**N):
    occ[i,:] = np.asarray(list(map(lambda x: int(x),'0'*(N-len(bin(i)[2:]))+bin(i)[2:])))
    sum_occ[i] = np.sum(occ[i,:])
# Calculate Wavefunction
rwf_dmrg = np.zeros(2**N,dtype=np.complex128)
lwf_dmrg = np.zeros(2**N,dtype=np.complex128)
for i in range(2**N):
    i_occ = occ[i,:]
    tmp_matr = np.array([[1]])
    tmp_matl = np.array([[1]])
    for k in range(N):
        tmp_matr = np.einsum('ij,jk->ik',tmp_matr,Mr[k][i_occ[k],:,:])
        tmp_matl = np.einsum('ij,jk->ik',tmp_matl,Ml[k][i_occ[k],:,:])
    #print(np.sum(tmp_mat-tmp_matl))
    rwf_dmrg[i] = tmp_matr[0,0]
    lwf_dmrg[i] = tmp_matl[0,0]
# Ensure Proper Normalization
# <-|R> = 1
# <L|R> = 1
print('\n\nResulting Wavefunctions:')
print('Need for Right Normalization: {}'.format(np.sum(rwf_dmrg)))
print('Need for Left  Normalization: {}'.format(np.dot(lwf_dmrg,rwf_dmrg)))
rwf_dmrg = rwf_dmrg/np.sum(rwf_dmrg)
lwf_dmrg = lwf_dmrg/np.sum(lwf_dmrg*rwf_dmrg)
print('Difference Between Left  ED & DMRG WFs: {}'.format(np.sum(np.abs(lwf_dmrg-lwf_ed))))
print('Difference Between Right ED & DMRG WFs: {}'.format(np.sum(np.abs(rwf_dmrg-rwf_ed))))
print('='*100)
print('Occupation\t\trdmrg\t\t\tred\t\t\tldmrg\t\t\tled')
print('-'*100)
rwf_ind = np.argsort(rwf_dmrg)[::-1]
for i in range(len(rwf_dmrg)):
    print('{}\t{},\t{},\t{},\t{}'.format(occ[rwf_ind[i],:],np.real(rwf_dmrg[rwf_ind[i]]),np.real(rwf_ed[rwf_ind[i]]),np.real(lwf_dmrg[rwf_ind[i]]),np.real(lwf_ed[rwf_ind[i]])))
##############################################
