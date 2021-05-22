import numpy as np

from IBitstream import IBitstream
from arithBase import ProbModel
from arithDecoder import ArithDecoder


def sign(b):
    if b:
        return 1
    else:
        return -1


# class for all the entropy decoding
class EntropyDecoder:
    def __init__(self, bitstream: IBitstream):
        self.arith_dec = ArithDecoder(bitstream)
        self.prob_sig_flag = ProbModel()
        self.prob_cbf = ProbModel()
        self.prob_golomb_suffix = ProbModel()

    def readQIndexBlock(self, blockSize: int):
        # loop over all positions inside NxN block
        #  --> call readQIndex for all quantization index

        out_integer_array = np.zero(blockSize*blockSize, dtype=np.uint8)

        coded_block_flag = self.self.arith_enc.decodeBin(self.prob_cbf)
        if not coded_block_flag:
            return out_integer_array.reshape([blockSize, blockSize])

        last_scan_index = self.expGolombProbAdapted()
        out_integer_array[last_scan_index] = self.readQIndex(isLast=True)

        for k in range(last_scan_index-1, -1, -1):
            out_integer_array[k] = self.readQIndex()

        return out_integer_array.reshape([blockSize, blockSize])

    def readQIndex(self, isLast=False):
        if not isLast:
            sig_flag = self.arith_dec.decodeBin(self.prob_sig_flag)
            if sig_flag == 0:
                return 0

        gt1_flag = self.arith_dec.decodeBinEP()
        if gt1_flag == 0:
            sign_flag = self.arith_dec.decodeBinEP()
            return sign(sign_flag)

        # (1) read expGolomb for absolute value
        value = self.expGolomb() + 2
        value *= sign(self.arith_dec.decodeBinEP())

        # (3) return value
        return value

    def expGolomb(self):
        # (1) read class index k using unary code (read all bits until next '1'; classIdx = num zeros)
        # (2) read position inside class as fixed-length code of k bits [red bits]
        # (3) return value

        length = 0
        while not self.arith_dec.decodeBinEP():
            length += 1

        value = 1
        if length > 0:
            value = value << length
            value += self.arith_dec.decodeBinsEP(length)

        value -= 1

        return value

    def expGolombProbAdapted(self):
        # (1) read class index k using unary code (read all bits until next '1'; classIdx = num zeros)
        # (2) read position inside class as fixed-length code of k bits [red bits]
        # (3) return value

        length = 0
        while not self.arith_dec.decodeBin(self.prob_cbf):
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
