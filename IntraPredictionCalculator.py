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
    return random.randint(0,2)

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
        else:
            raise Exception('Unsupported prediction mode')

    def get_dc_prediction(self, x: int, y: int) -> np.ndarray:
        border = np.concatenate([self.left_border(x, y), self.top_border(x, y)])
        prediction = round(border.mean()) if x > 0 and y > 0 else 128
        return np.full([self.blocksize, self.blocksize], prediction)

    def get_vertical_prediction(self, x: int, y: int) -> np.ndarray:
        return np.full([self.blocksize, self.blocksize], self.top_border(x, y))

    def get_horizontal_prediction(self, x: int, y: int) -> np.ndarray:
        return np.full([self.blocksize, self.blocksize], self.left_border(x, y)).T
