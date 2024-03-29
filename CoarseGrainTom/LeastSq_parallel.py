import itertools
import numpy as np
import scipy.linalg as lin
import copy
import math as mt
import cmath as cp
import operator
import time
import datetime
import six
import pickle
import itertools
import timeit
from qutip import *
#from pylab import *
#from scipy import *
from scipy.optimize import least_squares

#import sys
#sys.path.append ('/libs')
from libs_rand import Funs as funs
from libs_rand import DataGen as datagen
from importlib import reload
reload (funs)
reload (datagen)
from joblib import Parallel, delayed
import multiprocessing

num_cores = -1

def save_dict(dictionary, filename):
	with open(filename, 'wb') as f:
		pickle.dump(dictionary, f)

def load_dict(filename):
	with open(filename, 'rb') as f:
		ret_di = pickle.load(f)
	return ret_di

print('P2',six.PY2)
print('P3',six.PY3)

i = complex(0,1)
Nq = 1
aver = 100
sorting = False
condno = True
multinomial = True
dist='uniform'

tom = funs.TomFuns()
tom.set_tomography(Nqubits=Nq)

NoClickArr = [100]
if dist=='exponential':
    Beta = [0,np.pi/16,np.pi/8,np.pi/4,np.pi/2,10000*np.pi]
else:
    Beta = [0]

if sorting:
    Segments = [4,8,16]
else:
    Segments = [0]

rho = [rand_dm_ginibre(2**Nq, None).full() for j in range(aver)]

def run_exp_cond(N,Inc,beta,Av):

    gendata = datagen.DataGen()
    gendata.set_experiment(NoClicks=N,Slices=Inc,Nqubits=Nq,Rho=rho[Av],dist_key=dist,scale_par=beta,sort=sorting)

    #initial (non-optimised) search array
    t0 = np.random.rand(1,(2**Nq)**2)
    t0 = [val for sublist in t0 for val in sublist]
    Mvr, Nvr= gendata.Mvr(), gendata.Nvr()

    condnoDict[(ang,N,Inc)].append(np.linalg.cond(np.array(Mvr).reshape((len(Mvr),4**Nq))))


def run_exp(N,Inc,beta,Av):

    gendata = datagen.DataGen()
    gendata.set_experiment(NoClicks=N,Slices=Inc,Nqubits=Nq,Rho=rho[Av],dist_key=dist,scale_par=beta,sort=sorting)

    #initial (non-optimised) search array
    t0 = np.random.rand(1,(2**Nq)**2)
    t0 = [val for sublist in t0 for val in sublist]
    #Mvr, Nvr= gendata.Mvr(), gendata.Nvr()
    Projs, Nvr = gendata.Mvr(), gendata.Nvr()
    Mvr = Projs[1]
    State = Projs[0]
    print(sum(Nvr))

    start = timeit.default_timer()
    if multinomial:
        res_2 = least_squares(tom.LikeFun, t0, args=(Mvr,Nvr))
    else:
        res_2 = least_squares(tom.LikeFun, t0, tom.fderiv, args=(Mvr,Nvr))
    stop = timeit.default_timer()
    print('time taken to find soln',stop - start)

    #output density matrix
    out_2 = np.dot(tom.Tmatconj(res_2.x),tom.Tmat(res_2.x))/np.trace(np.dot(tom.Tmatconj(res_2.x),tom.Tmat(res_2.x)))
    #calculate fidelity
    mat1_Jac = lin.sqrtm(rho[Av])
    mat2_Jac = np.dot(mat1_Jac,out_2)
    mat3_Jac = lin.sqrtm(np.dot(mat2_Jac,mat1_Jac))
    
    return [np.trace(mat3_Jac).real, stop - start]

Test={}

for N in NoClickArr:
    for Inc in Segments:
        for b in Beta:
            Test[(N,Inc,b)] = []

for N in NoClickArr:
    for Inc in Segments:
        for b in Beta:
            Test[(N,Inc,b)].append(Parallel(n_jobs=num_cores)(delayed(run_exp)(N,Inc,b,k) for k in range(aver)))
            save_dict(Test,'Leastsq_uniform')

