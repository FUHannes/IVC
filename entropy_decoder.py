from IBitstream import IBitstream

# class for all the entropy decoding
class EntropyDecoder:
    def __init__(self, bitstream: IBitstream):
        self.bitstream = bitstream
        self.weird_flags_aber_ok = weird_flags_aber_ok

    def readQIndexBlock( self, blockSize: int ):
        # loop over all positions inside NxN block
        #  --> call readQIndex for all quantization index
        out_integer_array = []
        for _ in range(blockSize**2):
            out_integer_array.append(self.readQIndex())
        return out_integer_array

    def readQIndex( self ):
        
        # (1) read expGolomb for absolute value
        value = self.expGolomb()

        # (2) read sign bit for absolutes values > 0
        if value:
            value *= -1 if self.bitstream.getBit() else 1
            
        # (3) return value
        return value

        
    def expGolomb( self ):
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
