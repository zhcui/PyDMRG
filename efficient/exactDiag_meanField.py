import numpy as np
from scipy.linalg import eig as fullEig
from numpy.linalg import norm

class exactDiag:

    def __init__(self, L=10, alpha=0.35, gamma=0,
                 beta=2/3, delta=0, s=-1, p=1, q=0,
                 clumpSize=10, maxIter=10000, tol=1e-10):
        self.L = L
        self.in_l = alpha
        self.out_r = gamma
        self.out_l = beta
        self.in_r = delta
        self.j_r = p
        self.j_l = q

        self.in_l = alpha
        self.out_r = beta
        self.out_l = delta
        self.in_r = gamma

        self.s = s
        self.clumpSize = clumpSize
        self.maxIter = maxIter
        self.tol = tol

    def kernel(self):
        # Extract info
        L = self.L
        a = self.in_l #Insert Left (0.9)
        g = self.out_r #Insert Right (.1
        b = self.out_l  #Exit Left (0.9)
        d = self.in_r #Exit Right (0.1)
        s = self.s
        p = self.j_r
        q = self.j_l
        clumpSize = self.clumpSize

        # Currents
        pw = p*np.exp(-s)
        qw = q*np.exp(s)
        aw = a*np.exp(-s)
        bw = b*np.exp(-s)
        gw = g*np.exp(s)
        dw = d*np.exp(s)

        # Some Containers
        sproj = np.zeros((int(L/clumpSize), 2**clumpSize),dtype=np.complex128)
        isproj = np.zeros((int(L/clumpSize), 2**clumpSize),dtype=np.complex128)

        # Create Initial Guess
        self.nv = 0.5*np.ones(L,dtype=np.complex128)
        cdv = 0.5*np.ones(L,dtype=np.complex128)
        cv = 0.5*np.ones(L,dtype=np.complex128)

        # Create Operators
        m1 = np.array([[-a,gw],[aw,-g]])
        m1 = np.kron(m1,np.eye(2**(clumpSize-1)))

        mL = np.array([[-d,bw],[dw,-b]])
        mL = np.kron(np.eye(2**(clumpSize-1)),mL)

        mi = np.array([[0,0, 0, 0],
                       [0,-q,pw,0],
                       [0,qw,-p,0],
                       [0,0, 0, 0]])
        if clumpSize > 2:
            mc = np.zeros((2**clumpSize,2**clumpSize))
            for i in range(clumpSize-1):
                left = i
                right = clumpSize-(i+2)
                if left is 0:
                    mc += np.kron(mi,np.eye(2**right))
                elif right is 0:
                    mc += np.kron(np.eye(2**left),mi)
                else:
                    mc += np.kron(np.kron(np.eye(2**left),mi),np.eye(2**right))
        else:
            mc = mi

        # Individual Observables
        cop = np.zeros((2**clumpSize,2**clumpSize,clumpSize))
        cdop = np.zeros((2**clumpSize,2**clumpSize,clumpSize))
        nop = np.zeros((2**clumpSize,2**clumpSize,clumpSize))
        for i in range(clumpSize):
            im = i
            ip = clumpSize-(i+1)
            if im is 0:
                cop[:,:,i] = np.kron(np.array([[0,1],[0,0]]),np.eye(2**ip))
                cdop[:,:,i] = np.kron(np.array([[0,0],[1,0]]),np.eye(2**ip))
                nop[:,:,i] = np.kron(np.array([[0,0],[0,1]]),np.eye(2**ip))
            elif ip is clumpSize-1:
                cop[:,:,i] = np.kron(np.eye(2**im),np.array([[0,1],[0,0]]))
                cdop[:,:,i] = np.kron(np.eye(2**im),np.array([[0,0],[1,0]]))
                nop[:,:,i] = np.kron(np.eye(2**im),np.array([[0,0],[0,1]]))
            else:
                cop[:,:,i] = np.kron(np.kron(np.eye(2**im),np.array([[0,1],[0,0]])),np.eye(2**ip))
                cdop[:,:,i] = np.kron(np.kron(np.eye(2**im),np.array([[0,0],[1,0]])),np.eye(2**ip))
                nop[:,:,i] = np.kron(np.kron(np.eye(2**im),np.array([[0,0],[0,1]])),np.eye(2**ip))

        if L is clumpSize: self.maxIter = 1

        for iterCnt in range(self.maxIter):
            nv_new = np.zeros(L,dtype=np.complex128)
            cv_new = np.zeros(L,dtype=np.complex128)
            cdv_new = np.zeros(L,dtype=np.complex128)
            lam = np.zeros((int(L/clumpSize),2**clumpSize),dtype=np.complex128)
            Ms = np.zeros((2**clumpSize,2**clumpSize,int(L/clumpSize)))
            for clump in range(int(L/clumpSize)):
                leftClump = (clump)*clumpSize
                rightClump = (clump)*clumpSize+clumpSize-1
                # Couple left side
                if clump is 0:
                    leftSide = m1
                else:
                    leftSide = np.array([[-p*self.nv[leftClump-1],qw*cdv[leftClump-1]],
                                         [pw*cv[leftClump-1],-q*(1-self.nv[leftClump-1])]])
                    leftSide = np.kron(leftSide,np.eye(2**(clumpSize-1)));
                # Couple Right Side
                rightSide = np.zeros((2,2))
                if clump is int(L/clumpSize-1):
                    rightSide = mL
                else:
                    rightSide = np.array([[-q*self.nv[rightClump+1],pw*cdv[rightClump+1]],
                                          [qw*cv[rightClump+1],-p*(1-self.nv[rightClump+1])]])
                    rightSide = np.kron(np.eye(2**(clumpSize-1)),rightSide)
                # Create Main Matrix
                M = mc+leftSide+rightSide
                # Diagonalize Main Matrix
                u,v = fullEig(M)
                # Select largest eigenvalue
                v = v[:,np.argsort(u)]
                u = np.sort(u)
                # Check to see which one has a low imaginary value
                ind = -1
                curEig = -1e3
                for i in range(len(u)):
                    if (np.imag(u[i]) < 1e-8) and u[i] > curEig:
                        ind = i
                        curEig = u[ind]
                u = u[ind]
                lam[clump,0] = u
                # Calculate Expectation Values
                iv = np.linalg.inv(v)
                self.lpsi = iv[ind,:]
                self.rpsi = v[:,ind]
                for s in range(clumpSize):
                    nv_new[(clump)*clumpSize+s] = np.dot(self.lpsi,np.dot(nop[:,:,s],self.rpsi))
                    cv_new[(clump)*clumpSize+s] = np.dot(self.lpsi,np.dot(cop[:,:,s],self.rpsi))
                    cdv_new[(clump)*clumpSize+s] = np.dot(self.lpsi,np.dot(cdop[:,:,s],self.rpsi))
                sproj[clump,:] = v[:,ind]
                isproj[clump,:] = iv[ind,:]
            # Determine change in values
            nvdiff = norm(nv_new-self.nv);
            cvdiff = norm(cv_new-cv);
            cdvdiff = norm(cdv_new-cdv);
            # Update Values
            self.nv = nv_new
            cv = cv_new
            cdv = cdv_new
            # Check for convergence
            if (nvdiff<self.tol) and (cvdiff<self.tol) and (cdvdiff<self.tol):
                print('\n')
                print('Mean Field Convergence Achevied after {} iterations'.format(iterCnt))
                print('='*50)
                break
        if L is clumpSize: 
            print('\n')
            print('Exact Diagonalization Results Obtained')
            print('='*50)
        # Calculate Energy
        # Intra Clump
        E = 0
        for clump in range(int(L/clumpSize)):
            self.lpsi = isproj[clump,:]
            self.rpsi = sproj[clump,:]
            m = mc.copy() # Why do I have to copy here!!!???!!!???
            if clump is 0:
                m += m1
            if clump is int(L/clumpSize-1):
                m += mL
            E += np.dot(self.lpsi,np.dot(m,self.rpsi))
        # Inter Clump
        if clumpSize is not L:
            mi_x = np.kron(np.eye(2**(clumpSize-1)),mi)
            mi_x = np.kron(mi_x,np.eye(2**(clumpSize-1)))
            for clump in range(int(L/clumpSize-1)):
                self.lpsi = np.kron(isproj[clump,:],isproj[clump+1,:])
                self.rpsi = np.kron(sproj[clump,:],sproj[clump+1,:]).transpose()
                E += np.dot(self.lpsi,np.dot(mi_x,self.rpsi))
        return E


if __name__ == "__main__":
    x = exactDiag(L=10,clumpSize=2,s=0)
    x = exactDiag(L=10,clumpSize=10,s=0)
