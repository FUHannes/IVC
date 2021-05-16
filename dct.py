# %% 
from scipy.fftpack import dct, idct
import numpy as np
import matplotlib.pylab as plt 

# %% 
class Transformation:
    def forward_dct(self, block):
        return dct(dct(block, axis=0, norm='ortho'), axis=1, norm='ortho')

    def backward_dct(self, block):
        return idct(idct(block, axis=0, norm='ortho'), axis=1, norm='ortho')