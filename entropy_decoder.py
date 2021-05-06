# class for all the entropy decoding
class EntropyDecoder:

    def __init__( self, bitstream: IBitstream ):
        self.bitstream = bitstream

    def readQIndexBlock( self, blockSize: int ):
        # loop over all positions inside NxN block
        #  --> call readQIndex for all quantization index
        out_integer_array = []
        for _ in range(blockSize**2):
            out_integer_array.append(self.readQIndex())
        return out_integer_array

    def readQIndex( self ):
        # (1) read expGolomb for absolute value
        # (2) read sign bit for absolutes values > 0
        # (3) return value
        value = self.expGolomb()
        return value * (-1 if self.bitstream.getBit() else 1)

        
    def expGolomb( self ):
        # (1) read class index k using unary code (read all bits until next '1'; classIdx = num zeros)
        # (2) read position inside class as fixed-length code of k bits [red bits]
        # (3) return value
        current_red_code=1
        reading_blue_part = True
        red_length = 0
        while True:
            bit = int(self.bitstream.getBit())
            if reading_blue_part:
                red_length+=1
                reading_blue_part = (bit == 0)
            else:
                current_red_code = current_red_code * 2 + int(bit) #ok der teil wäre wohl in c wesentlich schneller (current_red_code << 1 + bit)
                red_length-=1
                if red_length == 0:
                    return current_red_code-1
