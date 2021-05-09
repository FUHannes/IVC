# class for all the entropy decoding
import IBitstream


class EntropyDecoder:

    def __init__(self, bitstream: IBitstream):
        self.bitstream = bitstream

    def readQIndexBlock(self, blockSize: int):
        # loop over all positions inside NxN block
        #  --> call readQIndex for all quantization index
        out_integer_array = []
        for _ in range(blockSize ** 2):
            out_integer_array.append(self.readQIndex())
        return out_integer_array

    def readQIndex(self):
        # (1) read expGolomb for absolute value
        value = self.expGolomb()

        # (2) read sign bit for absolutes values > 0
        if value:
            value *= -1 if self.bitstream.get_bit() else 1

        # (3) return value
        return value

    def expGolomb(self):
        # (1) read class index k using unary code (read all bits until next '1'; classIdx = num zeros)
        # (2) read position inside class as fixed-length code of k bits [red bits]
        # (3) return value
        current_red_code = 1
        reading_blue_part = True
        red_length = 0
        while True:
            bit = self.bitstream.get_bit()
            if reading_blue_part:
                red_length += 1
                reading_blue_part = not bit
            else:
                current_red_code = current_red_code * 2 + bit
                red_length -= 1
                if red_length == 0:
                    return current_red_code - 1
