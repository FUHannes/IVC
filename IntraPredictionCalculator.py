import numpy as np
from enum import IntEnum

class PredictionMode(IntEnum):
    DC_PREDICTION = 0


class IntraPredictionCalculator:
    def __init__(self, image: np.ndarray, blocksize: int):
        self.image = image
        self.blocksize = blocksize

    def get_prediction(self, x: int, y: int, prediction_mode: PredictionMode) -> np.ndarray:
        if prediction_mode == PredictionMode.DC_PREDICTION:
            return self.get_dc_prediction(x, y)
        else:
            raise Exception('Unsupported prediction mode')

    def get_dc_prediction(self, x: int, y: int) -> np.ndarray:
        left_border = self.image[y:y+self.blocksize, x-1:x].ravel() if x > 0 else []
        top_border  = self.image[y-1:y, x:x+self.blocksize].ravel() if y > 0 else []
        border = np.concatenate([left_border, top_border])
        prediction = round(border.mean()) if border.size > 0 else 128
        return np.full([self.blocksize, self.blocksize], prediction)
