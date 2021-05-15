import numpy as np
from enum import IntEnum

class PredictionMode(IntEnum):
    DC_PREDICTION = 0


class IntraPredictionCalculator:
    def __init__(self, image: np.ndarray, blocksize: int):
        self.image = image
        self.blocksize = blocksize

    def get_prediction(self, x: int, y: int, prediction_mode: PredictionMode) -> int:
        if prediction_mode == PredictionMode.DC_PREDICTION:
            return self.get_dc_prediction(x, y)
        else:
            raise Exception('Unsupported prediction mode')

    def get_dc_predictionV1(self, x: int, y: int) -> int:
        if x > 0 and y > 0:
            left_mean = self.image[y:y+self.blocksize, x-1:x].mean()
            top_mean  = self.image[y-1:y, x:x+self.blocksize].mean()
            return round((left_mean + top_mean) / 2)
        elif x > 0:
            left_mean = self.image[y:y+self.blocksize, x-1:x].mean()
            return round(left_mean)
        elif y > 0:
            top_mean  = self.image[y-1:y, x:x+self.blocksize].mean()
            return round(top_mean)
        else:
            return 128

    def get_dc_predictionV2(self, x: int, y: int) -> int:
        left_border = self.image[y:y+self.blocksize, x-1:x].ravel() if x > 0 else []
        top_border = self.image[y-1:y, x:x+self.blocksize].ravel() if y > 0 else []
        border = np.concatenate([left_border, top_border])
        prediction = round(border.mean()) if border.size > 0 else 128
        return prediction

    def get_dc_predictionV3(self, x: int, y: int) -> int:
        left_border = []
        if x > 0:
            left_border = self.image[y:y+self.blocksize, x-1:x].ravel()
        
        top_border = []
        if y > 0:
            top_border = self.image[y-1:y, x:x+self.blocksize].ravel()
        
        border = np.concatenate([left_border, top_border])

        prediction = 128
        if border.size > 0:
            prediction = round(border.mean())
        
        return prediction

if __name__ == '__main__':
    import time
    import random

    width = 1600
    height = 1200
    blocksize = 8
    runden = 10

    arr = np.random.uniform(0,256,(height,width)).astype('uint8')
    tests = [(x, y) for y in range(0, height, blocksize) for x in range(0, width, blocksize)]
    ipc = IntraPredictionCalculator(arr, blocksize)

    def testFunction(name, func):
        t0 = time.process_time()
        for x, y in tests:
            func(ipc, x, y)
        td = time.process_time() - t0
        return td

    def measureFunction(name, func):
        tda = [testFunction(name, func) for i in range(runden)]
        tmean = np.mean(tda)
        tstd = np.std(tda)
        print(f'{name:2s}: mean={tmean:5f} std={tstd:5f}')

    funcs = {
        'V1': IntraPredictionCalculator.get_dc_predictionV1,
        'V2': IntraPredictionCalculator.get_dc_predictionV2,
        'V3': IntraPredictionCalculator.get_dc_predictionV3,
    }

    for k in funcs:
        measureFunction(k, funcs[k])
