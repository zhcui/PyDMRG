import numpy as np
import scipy.linalg as la

######## Inputs ##############################
# SEP Model
N = 6
alpha = 0.35  # In at left
beta = 2/3    # Exit at right
s = -1        # Exponential weighting
gamma = 0     # Exit at left
delta = 0     # In at right
p = 1         # Jump right
q = 0         # Jump Left
# Optimization
tol = 1e-5
maxIter = 10
maxBondDim = 16
##############################################

######## Prereqs #############################
# Create MPS
M = []
for i in range(int(N/2)):
    M.insert(len(M),np.ones((2,min(2**(i),maxBondDim),min(2**(i+1),maxBondDim))))
for i in range(int(N/2))[::-1]:
    M.insert(len(M),np.ones((2,min(2**(i+1),maxBondDim),min(2**i,maxBondDim))))
Ml = []
for i in range(int(N/2)):
    Ml.insert(len(Ml),np.ones((2,min(2**i,maxBondDim),min(2**(i+1),maxBondDim))))
for i in range(int(N/2))[::-1]:
    Ml.insert(len(Ml),np.ones((2,min(2**(i+1),maxBondDim),min(2**i,maxBondDim))))
# Create MPO
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
# Create F
F = []
F.insert(len(F),np.array([[[1]]]))
for i in range(int(N/2)):
    F.insert(len(F),np.zeros((min(2**(i+1),maxBondDim),4,min(2**(i+1),maxBondDim))))
for i in range(int(N/2)-1,0,-1):
    F.insert(len(F),np.zeros((min(2**(i),maxBondDim),4,min(2**i,maxBondDim))))
F.insert(len(F),np.array([[[1]]]))
Fl = []
Fl.insert(len(Fl),np.array([[[1]]]))
for i in range(int(N/2)):
    Fl.insert(len(Fl),np.zeros((min(2**(i+1),maxBondDim),4,min(2**(i+1),maxBondDim))))
for i in range(int(N/2)-1,0,-1):
    Fl.insert(len(Fl),np.zeros((min(2**(i),maxBondDim),4,min(2**i,maxBondDim))))
Fl.insert(len(Fl),np.array([[[1]]]))
##############################################

# Make MPS Right Canonical ###################
for i in range(int(N)-1,0,-1):
    M_reshape = np.swapaxes(M[i],0,1)
    (n1,n2,n3) = M_reshape.shape
    M_reshape = np.reshape(M_reshape,(n1,n2*n3))
    (U,s,V) = np.linalg.svd(M_reshape,full_matrices=False)
    M_reshape = np.reshape(V,(n1,n2,n3))
    M[i] = np.swapaxes(M_reshape,0,1)
    M[i-1] = np.einsum('klj,ji,i->kli',M[i-1],U,s)
for i in range(int(N)-1,0,-1):
    M_reshape = np.swapaxes(Ml[i],0,1)
    (n1,n2,n3) = M_reshape.shape
    M_reshape = np.reshape(M_reshape,(n1,n2*n3))
    (U,s,V) = np.linalg.svd(M_reshape,full_matrices=False)
    M_reshape = np.reshape(V,(n1,n2,n3))
    Ml[i] = np.swapaxes(M_reshape,0,1)
    Ml[i-1] = np.einsum('klj,ji,i->kli',M[i-1],U,s)
##############################################

# Calculate Initial F ########################
for i in range(int(N)-1,0,-1):
    F[i] = np.einsum('bxc,ydbe,eaf,cdf->xya',np.conj(M[i]),W[i],M[i],F[i+1])
for i in range(int(N)-1,0,-1):
    Fl[i] = np.einsum('bxc,ydbe,eaf,cdf->xya',np.conj(Ml[i]),W[i],Ml[i],Fl[i+1])
##############################################

# Optimization Sweeps ########################
converged = False
iterCnt = 0
E_prev = 0
while not converged:
# Right Sweep ----------------------------
    print('Right Sweep {}'.format(iterCnt))
    for i in range(N-1):
        H = np.einsum('jlp,lmin,kmq->ijknpq',F[i],W[i],F[i+1])
        (n1,n2,n3,n4,n5,n6) = H.shape
        H = np.reshape(H,(n1*n2*n3,n4*n5*n6))
        u,vl,vr = la.eig(H,left=True)
        # select max eigenvalue
        max_ind = np.argsort(u)[-1]
        E = u[max_ind]
        vr = vr[:,max_ind]
        vl = vl[:,max_ind]
        print(vl)
        #print('vr = {}'.format(vr))
        #print('vl = {}'.format(vl))
        print('\tEnergy at site {}= {}'.format(i,E))
        M[i] = np.reshape(vr,(n1,n2,n3))
        Ml[i] = np.reshape(vl,(n1,n2,n3))
        # Right Normalize
        M_reshape = np.reshape(M[i],(n1*n2,n3))
        (U,s,V) = np.linalg.svd(M_reshape,full_matrices=False)
        M[i] = np.reshape(U,(n1,n2,n3))
        M[i+1] = np.einsum('i,ij,kjl->kil',s,V,M[i+1])
        M_reshape = np.reshape(Ml[i],(n1*n2,n3))
        (U,s,V) = np.linalg.svd(M_reshape,full_matrices=False)
        Ml[i] = np.reshape(U,(n1,n2,n3))
        Ml[i+1] = np.einsum('i,ij,kjl->kil',s,V,M[i+1])
        # Update F
        F[i+1] = np.einsum('jlp,ijk,lmin,npq->kmq',F[i],np.conj(M[i]),W[i],M[i])
        Fl[i+1] = np.einsum('jlp,ijk,lmin,npq->kmq',Fl[i],np.conj(Ml[i]),W[i],Ml[i])
# Left Sweep -----------------------------
    print('Left Sweep {}'.format(iterCnt))
    for i in range(N-1,0,-1):
        H = np.einsum('jlp,lmin,kmq->ijknpq',F[i],W[i],F[i+1])
        (n1,n2,n3,n4,n5,n6) = H.shape
        H = np.reshape(H,(n1*n2*n3,n4*n5*n6))
        u,vl,vr = la.eig(H,left=True)
        # select max eigenvalue
        max_ind = np.argsort(u)[-1]
        E = u[max_ind]
        vr = vr[:,max_ind]
        vl = vl[:,max_ind]
        print(vl)
        #print('vr = {}'.format(vr))
        #print('vl = {}'.format(vl))
        print('\tEnergy at site {}= {}'.format(i,E))
        M[i] = np.reshape(vr,(n1,n2,n3))
        Ml[i] = np.reshape(vl,(n1,n2,n3))
        # Right Normalize 
        M_reshape = np.swapaxes(M[i],0,1)
        M_reshape = np.reshape(M_reshape,(n2,n1*n3))
        (U,s,V) = np.linalg.svd(M_reshape,full_matrices=False)
        M_reshape = np.reshape(V,(n2,n1,n3))
        M[i] = np.swapaxes(M_reshape,0,1)
        M[i-1] = np.einsum('klj,ji,i->kli',M[i-1],U,s)
        M_reshape = np.swapaxes(Ml[i],0,1)
        M_reshape = np.reshape(M_reshape,(n2,n1*n3))
        (U,s,V) = np.linalg.svd(M_reshape,full_matrices=False)
        M_reshape = np.reshape(V,(n2,n1,n3))
        Ml[i] = np.swapaxes(M_reshape,0,1)
        Ml[i-1] = np.einsum('klj,ji,i->kli',M[i-1],U,s)
        # Update F
        F[i] = np.einsum('bxc,ydbe,eaf,cdf->xya',np.conj(M[i]),W[i],M[i],F[i+1])
        Fl[i] = np.einsum('bxc,ydbe,eaf,cdf->xya',np.conj(Ml[i]),W[i],Ml[i],Fl[i+1])
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

# Now Calculate State from MPS ###############
occ = np.zeros((2**N,N),dtype=int)
sum_occ = np.zeros(2**N)
for i in range(2**N):
    occ[i,:] = np.asarray(list(map(lambda x: int(x),'0'*(N-len(bin(i)[2:]))+bin(i)[2:])))
    sum_occ[i] = np.sum(occ[i,:])
# Calculate Wavefunction
rwf_dmrg = np.zeros(2**N,dtype=np.complex128)
for i in range(2**N):
    i_occ = occ[i,:]
    tmp_mat = np.array([[1]])
    for k in range(N):
        tmp_mat = np.einsum('ij,jk->ik',tmp_mat,M[k][i_occ[k],:,:])
    #print(np.sum(tmp_mat-tmp_matl))
    rwf_dmrg[i] = tmp_mat[0,0]
##############################################

# Calculate State via ED #####################
H = np.zeros((2**N,2**N))
occ = np.zeros((2**N,N),dtype=int)
sum_occ = np.zeros(2**N)
for i in range(2**N):
    occ[i,:] = np.asarray(list(map(lambda x: int(x),'0'*(N-len(bin(i)[2:]))+bin(i)[2:])))
    sum_occ[i] = np.sum(occ[i,:])
# Calculate Hamiltonian Methods
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
lwf_ed =lwf_ed[:,inds[-1]]
rwf_ed = rwf_ed[:,inds[-1]]
lwf_ed = lwf_ed/np.sum(lwf_ed*rwf_ed)
##############################################

# Decompose ED into MPS ######################
# Convert Wavefunction into ND Array
psi = np.zeros([2]*N,dtype=np.complex128)
occ = np.zeros((2**N,N),dtype=int)
for i in range(2**N):
    occ[i,:] = np.asarray(list(map(lambda x: int(x),'0'*(N-len(bin(i)[2:]))+bin(i)[2:])))
for i in range(2**N):
    psi[tuple(occ[i,:])] = rwf_ed[i]
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
# Decompose Wavefunction from the right
Ma = [] # Ordering (sigma,a_0,a_1)
for i in range(N,1,-1):
    psi = np.reshape(psi,(2**(i-1),-1))
    (u,s,v) = np.linalg.svd(psi,full_matrices=False)
    B = np.reshape(v,(fbd_site[i-1],2,mbd_site[i]))
    B = B[:mbd_site[i-1],:,:mbd_site[i]] 
    B = np.swapaxes(B,0,1)
    Ma.insert(0,B)
    psi = np.einsum('ij,j->ij',u[:,:mbd_site[i-1]],s)
Ma.insert(0,np.reshape(psi,(2,1,min(2,maxBondDim))))
for i in range(len(Ma)):
    print('\n\n')
    print('DMRG (R):{}'.format(M[i].shape))
    print(np.abs(M[i]))
    print('ED (R):{}'.format(Ma[i].shape))
    print(np.abs(Ma[i]))
    print(np.sum(np.sum(np.sum(np.abs(np.abs(Ma[i])-np.abs(M[i]))))))
##############################################


# Decompose ED into left MPS #################
# Convert Wavefunction into ND Array
psi = np.zeros([2]*N,dtype=np.complex128)
occ = np.zeros((2**N,N),dtype=int)
for i in range(2**N):
    occ[i,:] = np.asarray(list(map(lambda x: int(x),'0'*(N-len(bin(i)[2:]))+bin(i)[2:])))
for i in range(2**N):
    psi[tuple(occ[i,:])] = lwf_ed[i]
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
# Decompose Wavefunction from the right
Mla = [] # Ordering (sigma,a_0,a_1)
for i in range(N,1,-1):
    psi = np.reshape(psi,(2**(i-1),-1))
    (u,s,v) = np.linalg.svd(psi,full_matrices=False)
    B = np.reshape(v,(fbd_site[i-1],2,mbd_site[i]))
    B = B[:mbd_site[i-1],:,:mbd_site[i]] 
    B = np.swapaxes(B,0,1)
    Mla.insert(0,B)
    psi = np.einsum('ij,j->ij',u[:,:mbd_site[i-1]],s)
Mla.insert(0,np.reshape(psi,(2,1,min(2,maxBondDim))))
for i in range(len(Mla)):
    print('\n\n')
    print('DMRG (L):{}'.format(Ml[i].shape))
    print(np.abs(Ml[i]))
    print('ED (L):{}'.format(Mla[i].shape))
    print(np.abs(Mla[i]))
    print(np.sum(np.sum(np.sum(np.abs(np.abs(np.real(Mla[i]))-np.abs(np.real(Ml[i])))))))
##############################################


