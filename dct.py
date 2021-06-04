# %% 
from scipy.fftpack import dct, idct
import numpy as np
import matplotlib.pylab as plt 
from IntraPredictionCalculator import PredictionMode
import math

# %% 
class Transformation:
    def __init__(self, blocksize):
        self.dst_matrix = self.get_dst_vii_matrix(blocksize)
        self.dst_matrix_inverse = self.dst_matrix.T

    def get_dst_vii_matrix(self,size_N):
        matrix = []
        beta = math.sqrt(2/(2*size_N+1))
        for k in range(size_N):
            b_k = []
            for n in range(size_N):
                b_k.append(beta* math.sin(math.pi* ((2*k + 1)/(2*size_N+1)) *(n+1)))
            matrix.append(b_k)
        return np.asarray(matrix)

    def forward_transform(self, block, prediction_mode):
        if prediction_mode == PredictionMode.PLANAR_PREDICTION:
            return np.matmul(np.matmul(self.dst_matrix,block),self.dst_matrix_inverse)
        elif prediction_mode == PredictionMode.DC_PREDICTION:
            return dct(dct(block, axis=0, norm='ortho'), axis=1, norm='ortho')
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            return np.matmul(dct(block, axis=0, norm='ortho'),self.dst_matrix_inverse)
        elif prediction_mode == PredictionMode.VERTICAL_PREDICTION:
            return dct(np.matmul(self.dst_matrix,block), axis=1, norm='ortho')


    def backward_transform(self, block, prediction_mode):
        if prediction_mode == PredictionMode.PLANAR_PREDICTION:
            return np.matmul(np.matmul(self.dst_matrix_inverse,block),self.dst_matrix) *4
        elif prediction_mode == PredictionMode.DC_PREDICTION:
            return idct(idct(block, axis=0, norm='ortho'), axis=1, norm='ortho')
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            return np.matmul(idct(block, axis=0, norm='ortho'),self.dst_matrix)*2
        elif prediction_mode == PredictionMode.VERTICAL_PREDICTION:
            return idct(np.matmul(self.dst_matrix_inverse,block), axis=1, norm='ortho')*2


