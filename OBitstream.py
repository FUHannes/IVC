# authors: Giovanni Sorice, Manuel Welte

class OBitstream:
    # constructor: open specified output file and initialize members
    def __init__(self, filename):
        self.file = open(filename, 'wb')
        self.buffer = 0
        self.bit_counter = 0

    # add bit to bitstream
    def addBit(self, bit: int):  # only 0 or 1
        self.buffer = ( self.buffer << 1 ) | int(bool(bit))
        self.bit_counter += 1
        if self.bit_counter == 8:
            if not self.file:
                raise Exception('OBitstream: File not open')
            self.file.write(self.buffer.to_bytes(1, byteorder='big'))
            self.buffer = 0
            self.bit_counter = 0

    # write numBits from bitPattern (most significant bit first)
    def addBits(self, bitPattern: int, numBits: int):
        for i in range(numBits, 0, -1):
            # Take the single interesting bit
            bit = (bitPattern >> (i - 1)) & int(1)
            self.addBit(bit)

    # write zeros to fill last byte
    def byteAlign(self):
        if self.bit_counter != 0:
            for i in range(self.bit_counter, 8):
                # Take the single interesting bit
                self.addBit(0)

    # terminate bitstream (and close file)
    def terminate(self):
        self.byteAlign()
        self.file.close()
        self.file = None

