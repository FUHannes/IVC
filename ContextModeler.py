from arithBase import ProbModel
import numpy as np

class ContextModeler:
    
    def __init__(self, block_size: int):
        self.prob_sig_flag = None
        self.prob_gt1_flag = None
        self.prob_level_prefix = None
        self.prob_cbf = ProbModel()
        self.prob_last_prefix = ProbModel()
        self.prediction_mode_bin1 = ProbModel()
        self.prediction_mode_bin2 = ProbModel()
        self.prediction_mode_bin3 = ProbModel()

        self.diag_map = self.genDiagMap(block_size)
        self.models_sig_flag = self.initProbModels(3)
        self.models_gt1_flag = self.initProbModels(3)
        self.models_level_prefix = self.initProbModels(3)

        self.prob_mx_abs_greater0_flag = ProbModel()
        self.prob_mx = ProbModel()
        self.prob_my_abs_greater0_flag = ProbModel()
        self.prob_my = ProbModel()

    def initProbModels(self, num):
        models = []
        for _ in range(num):
            models.append(ProbModel())
        return models

    def genDiagMap(self, block_size):
        diags = []
        (rows, columns) = (block_size, block_size)
        for line in range(1, (rows + columns)):

            start_col = max(0, line - rows)
            count = min(line, (columns - start_col), rows)

            for j in range(0, count):
                l = min(rows, line) - j - 1
                r = start_col + j
                diags.append(l + r)

        return np.array(diags)
    
    def switchContext(self, pos):
        # more or less arbitrary choice of diagonal classes
        if self.diag_map[pos] < 4:
            cl = 0
        elif self.diag_map[pos] < 7:
            cl = 1
        else:
            cl = 2

        self.prob_sig_flag = self.models_sig_flag[cl]
        self.prob_gt1_flag = self.models_gt1_flag[cl]
        self.prob_level_prefix = self.models_level_prefix[cl]

