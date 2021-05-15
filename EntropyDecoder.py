import numpy as np

from IBitstream import IBitstream

def sign(b):
    if b:
        return 1
    else:
        return -1

# class for all the entropy decoding
class EntropyDecoder:
    def __init__(self, bitstream: IBitstream):
        self.bitstream = bitstream

    def readQIndexBlock(self, blockSize: int):
        # loop over all positions inside NxN block
        #  --> call readQIndex for all quantization index
        out_integer_array = []
        for _ in range(blockSize ** 2):
            out_integer_array.append(self.readQIndex())
        return np.array(out_integer_array).reshape([blockSize, blockSize])

    def readQIndex(self):
        sig_flag = self.bitstream.get_bit()
        if sig_flag == 0:
            return 0

        gt1_flag = self.bitstream.get_bit()
        if gt1_flag == 0:
            sign_flag = self.bitstream.get_bit()
            return sign(sign_flag)

        # (1) read expGolomb for absolute value
        value = self.expGolomb()+2
        value *= sign(self.bitstream.get_bit())

        # (3) return value
        return value

    def expGolomb(self):
        # (1) read class index k using unary code (read all bits until next '1'; classIdx = num zeros)
        # (2) read position inside class as fixed-length code of k bits [red bits]
        # (3) return value

        length = 0
        while not self.bitstream.get_bit():
            length += 1

        value = 1
        if length > 0:
            value = value << length
            value += self.bitstream.get_bits(length)

        value -= 1

        return value

    # placeholder: will make sense with arithmetic coding
    def terminate(self):
        return True
