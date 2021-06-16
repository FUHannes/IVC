import random
from enum import IntEnum

import numpy as np


class PredictionMode(IntEnum):
    DC_PREDICTION = 0
    VERTICAL_PREDICTION = 1
    HORIZONTAL_PREDICTION = 2
    PLANAR_PREDICTION = 3


def random_prediction_mode():
    # TODO: set to [0,3] when PLANAR_PREDICTION is implemented
    return random.randint(0, 3)


class PredictionCalculator:
    def __init__(self, image: np.ndarray, blocksize: int, ref_image: np.array = None):
        self.image = image
        self.ref_image = ref_image
        self.coded_width = self.image.shape[1]
        self.coded_height = self.image.shape[0]
        self.blocksize = blocksize

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
        mx = max(-x, min(mx, self.coded_width - (x + self.blocksize)))
        my = max(-y, min(my, self.coded_height - (y + self.blocksize)))
        xref = x + mx
        yref = y + my
        return self.ref_image[yref:yref + self.blocksize, xref:xref + self.blocksize]
