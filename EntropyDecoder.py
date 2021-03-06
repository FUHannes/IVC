import numpy as np

from IBitstream import IBitstream
from arithBase import ProbModel
from arithDecoder import ArithDecoder
from PredictionCalculator import PredictionMode
from ContextModeler import ContextModeler


def sign(b):
    if b:
        return 1
    else:
        return -1


# class for all the entropy decoding
class EntropyDecoder:
    def __init__(self, bitstream: IBitstream, block_size: int):
        self.arith_dec = ArithDecoder(bitstream)
        self.cm = ContextModeler(block_size)
        self.block_size = block_size

    def read_block_intra_pic(self):
        # read side information
        if self.arith_dec.decodeBin(self.cm.prediction_mode_bin1) == 0:
            prediction_mode = PredictionMode.PLANAR_PREDICTION
        elif self.arith_dec.decodeBin(self.cm.prediction_mode_bin2) == 0:
            prediction_mode = PredictionMode.DC_PREDICTION
        elif self.arith_dec.decodeBin(self.cm.prediction_mode_bin3) == 0:
            prediction_mode = PredictionMode.HORIZONTAL_PREDICTION
        else:
            prediction_mode = PredictionMode.VERTICAL_PREDICTION

        # read quantization indexes
        qidx_block = self.read_qindexes_block()

        return qidx_block, prediction_mode

    def read_block_inter_pic(self):
        # read intra/inter mode
        inter_flag = self.arith_dec.decodeBin(self.cm.prediction_inter_flag)

        # read side information
        mx, my = 0, 0
        if inter_flag:
            mx_abs_greater0_flag = self.arith_dec.decodeBin(self.cm.prob_mx_abs_greater0_flag)
            if mx_abs_greater0_flag:
                mx_abs = self.expGolombProbAdapted(self.cm.prob_mx)
                mx_sign = self.arith_dec.decodeBinEP()
                mx = mx_abs * sign(mx_sign)

            my_abs_greater0_flag = self.arith_dec.decodeBin(self.cm.prob_my_abs_greater0_flag)
            if my_abs_greater0_flag:
                my_abs = self.expGolombProbAdapted(self.cm.prob_my)
                my_sign = self.arith_dec.decodeBinEP()
                my = my_abs * sign(my_sign)

        # read quantization indexes
        qidx_block = self.read_qindexes_block()

        return qidx_block, inter_flag, mx, my

    def read_qindexes_block(self):
        # loop over all positions inside NxN block
        #  --> call readQIndex for all quantization index

        out_integer_array = np.zeros(self.block_size*self.block_size, dtype=np.int32)

        coded_block_flag = self.arith_dec.decodeBin(self.cm.prob_cbf)
        if not coded_block_flag:
            return out_integer_array.reshape([self.block_size, self.block_size])

        last_scan_index = self.expGolombProbAdapted(self.cm.prob_last_prefix)
        out_integer_array[last_scan_index] = self.readQIndex(last_scan_index, isLast=True)

        for k in range(last_scan_index-1, -1, -1):
            out_integer_array[k] = self.readQIndex(k)

        return out_integer_array.reshape([self.block_size, self.block_size])

    def readQIndex(self, pos, isLast=False):
        self.cm.switchContext(pos)

        if not isLast:
            sig_flag = self.arith_dec.decodeBin(self.cm.prob_sig_flag)
            if sig_flag == 0:
                return 0

        gt1_flag = self.arith_dec.decodeBin(self.cm.prob_gt1_flag)
        if gt1_flag == 0:
            sign_flag = self.arith_dec.decodeBinEP()
            return sign(sign_flag)

        # (1) read expGolomb for absolute value
        value = self.expGolombProbAdapted(self.cm.prob_level_prefix) + 2
        value *= sign(self.arith_dec.decodeBinEP())

        # (3) return value
        return value


    def expGolombProbAdapted(self, prob):
        # (1) read class index k using unary code (read all bits until next '1'; classIdx = num zeros)
        # (2) read position inside class as fixed-length code of k bits [red bits]
        # (3) return value

        length = 0
        while not self.arith_dec.decodeBin(prob):
            length += 1

        value = 1
        if length > 0:
            value = value << length
            value += self.arith_dec.decodeBinsEP(length)

        value -= 1

        return value


    # placeholder: will make sense with arithmetic coding
    def terminate(self):
        return self.arith_dec.finish()
