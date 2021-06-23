from enum import IntEnum
from itertools import cycle
import numpy as np
from scipy import signal

class PredictionMode(IntEnum):
    DC_PREDICTION = 0
    VERTICAL_PREDICTION = 1
    HORIZONTAL_PREDICTION = 2
    PLANAR_PREDICTION = 3


class PredictionCalculator:
    def __init__(self, image: np.ndarray, blocksize: int, ref_image: np.array = None):
        self.image = image
        self.ref_image = ref_image
        self.interpolated_reconstructed_image = None if ref_image is None else self.half_sample_accurate_motion_compensation(ref_image)
        self.coded_width = self.image.shape[1]
        self.coded_height = self.image.shape[0]
        self.blocksize = blocksize
        self.mv = np.zeros([self.coded_height // self.blocksize + 1,
                            self.coded_width // self.blocksize + 2, 2], dtype=np.int)

    def half_sample_accurate_motion_compensation(self, image: np.ndarray) -> np.ndarray:

        # 1. Pad the (already padded) image with another 4 samples at each side (using sample repetition)
        image = np.pad(image, ((0, 4), (0, 4)), "edge")
        # 2. Create new image of size(2W+4B+8)×(2H+4B+8)that is filled with zeros andcopy the samples at integer positions from padded image (use NumPy slicing)
        image = np.repeat(np.repeat(image, 2, axis=0), 2, axis=1)
        values = cycle([1, 0])
        spreaded_image = np.array([[next(values) for i in range(image.shape[1])] if (j % 2) == 0 else [0 for i in range(image.shape[1])]  for j in range(image.shape[0])])
        spreaded_image = spreaded_image * image
        # 3 - 4 Vertical and Horizontal interpolation
        kernel = np.array([[-1, 0, 4, 0, -11, 0, 40, 64, 40, 0, -11, 0, 4, 0, -1]]) / 64
        kernel2D = kernel.T @ kernel
        spreaded_image = signal.convolve2d(spreaded_image, kernel2D, mode="same")
        # 5 Round the result to integers
        spreaded_image = spreaded_image[:spreaded_image.shape[0]-8, : spreaded_image.shape[1]-8]
        spreaded_image = np.rint(spreaded_image).astype(int)
        return spreaded_image

    def store_mv(self, x: int, y: int, mx: int, my: int):
        yb = y // self.blocksize + 1
        xb = x // self.blocksize + 1
        self.mv[yb, xb] = mx, my

    def get_mv_pred(self, x: int, y: int):
        yb = y // self.blocksize + 1
        xb = x // self.blocksize + 1
        mxa, mya = self.mv[yb, xb - 1]  # left block
        mxb, myb = self.mv[yb - 1, xb]  # block above
        mxc, myc = self.mv[yb - 1, xb + 1]  # block above-right
        mxp = (mxa + mxb + mxc) - min(mxa, mxb, mxc) - max(mxa, mxb, mxc)  # median: center of sorted list
        myp = (mya + myb + myc) - min(mya, myb, myc) - max(mya, myb, myc)  # median: center of sorted list
        return mxp, myp

    def left_border(self, x: int, y: int):
        return self.image[y:y + self.blocksize, x - 1:x].ravel() if x > 0 else np.full([self.blocksize], 128)

    def top_border(self, x: int, y: int):
        return self.image[y - 1:y, x:x + self.blocksize].ravel() if y > 0 else np.full([self.blocksize], 128)

    def get_prediction(self, x: int, y: int, prediction_mode: PredictionMode) -> np.ndarray:
        if prediction_mode == PredictionMode.DC_PREDICTION:
            return self.get_dc_prediction(x, y)
        elif prediction_mode == PredictionMode.VERTICAL_PREDICTION:
            return self.get_vertical_prediction(x, y)
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            return self.get_horizontal_prediction(x, y)
        elif prediction_mode == PredictionMode.PLANAR_PREDICTION:
            return self.get_planar_prediction(x, y)
        else:
            raise Exception('Unsupported prediction mode')

    def get_dc_prediction(self, x: int, y: int) -> np.ndarray:
        dc = 128
        if x > 0 and y > 0:
            dc = round(0.5 * (self.left_border(x, y).mean() + self.top_border(x, y).mean()))
        elif x > 0:
            dc = round(self.left_border(x, y).mean())
        elif y > 0:
            dc = round(self.top_border(x, y).mean())
        return np.full([self.blocksize, self.blocksize], dc)

    def get_vertical_prediction(self, x: int, y: int) -> np.ndarray:
        return np.full([self.blocksize, self.blocksize], self.top_border(x, y))

    def get_horizontal_prediction(self, x: int, y: int) -> np.ndarray:
        return np.full([self.blocksize, self.blocksize], self.left_border(x, y)).T

    def get_planar_prediction(self, x: int, y: int) -> np.ndarray:
        # speed-up (tried to use numpy as much as possible for making things faster)
        top_samples = self.top_border(x, y).astype('int')
        left_samples = self.left_border(x, y).astype('int')
        virtual_bottom_samples = np.full([self.blocksize], left_samples[self.blocksize - 1])
        virtual_right_samples = np.full([self.blocksize], top_samples[self.blocksize - 1])

        pred_block = np.full([self.blocksize, self.blocksize], self.blocksize,
                             dtype='int32')  # initialize with rounding offset

        # horizontal part
        for local_x in range(0, self.blocksize):
            pred_block[:, local_x] += (self.blocksize - 1 - local_x) * left_samples + (
                    1 + local_x) * virtual_right_samples

        # vertical part
        for local_y in range(0, self.blocksize):
            pred_block[local_y, :] += (self.blocksize - 1 - local_y) * top_samples + (
                    1 + local_y) * virtual_bottom_samples

        # final division (with rounding)
        pred_block //= (2 * self.blocksize)
        return pred_block

    def get_inter_prediction(self, x: int, y: int, mx: int, my: int):
        xref = max(0,
                   min(x + mx + self.blocksize, self.ref_image.shape[1] - self.blocksize))  # clip to padded image size
        yref = max(0,
                   min(y + my + self.blocksize, self.ref_image.shape[0] - self.blocksize))  # clip to padded image size
        return self.ref_image[yref:yref + self.blocksize, xref:xref + self.blocksize]
