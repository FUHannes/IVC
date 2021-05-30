import numpy as np
from enum import IntEnum
import random

class PredictionMode(IntEnum):
    DC_PREDICTION = 0
    VERTICAL_PREDICTION = 1
    HORIZONTAL_PREDICTION = 2
    PLANAR_PREDICTION = 3

def random_prediction_mode():
    # TODO: set to [0,3] when PLANAR_PREDICTION is implemented
    return random.randint(0,3)

class IntraPredictionCalculator:
    def __init__(self, image: np.ndarray, blocksize: int):
        self.image = image
        self.blocksize = blocksize

    def left_border(self, x: int, y: int):
        return self.image[y:y+self.blocksize, x-1:x].ravel() if x > 0 else [128] * self.blocksize

    def top_border(self, x: int, y: int):
        return self.image[y-1:y, x:x+self.blocksize].ravel() if y > 0 else [128] * self.blocksize

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
        x_border_idx = (x // self.blocksize) - 1
        y_border_idx = (y // self.blocksize) - 1

        predicted_block = np.zeros([self.blocksize, self.blocksize])

        for local_x in range(0, self.blocksize):
            global_x = local_x + x


            for local_y in range(0, self.blocksize):
                global_y = local_y + y
                h = (self.blocksize - 1 - local_x) * self.image[global_y, x_border_idx] + (1 + local_x) * self.image[y_border_idx, x_border_idx + self.blocksize]
                v = (self.blocksize - 1 - local_y) * self.image[y_border_idx, global_x] + (1 + local_y) * self.image[y_border_idx + self.blocksize, x_border_idx]
                predicted_block[local_y, local_x] = (h + v) / (2 * self.blocksize)
         
        return predicted_block.astype('int')