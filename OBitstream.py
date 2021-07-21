# authors: Giovanni Sorice, Manuel Welte

class OBitstream:
    # constructor: open specified output file and initialize members
    def __init__(self, filename):
        self.file = open(filename, 'wb')
        self.buffer = 0
        self.bit_counter = 0

    # add bit to bitstream
    def addBit(self, bit: int):  # only 0 or 1
        self.buffer = (self.buffer << 1) | int(bool(bit))
        self.bit_counter += 1
        if self.bit_counter == 8:
            if not self.file:
                raise Exception('OBitstream: File not open')
            self.file.write(self.buffer.to_bytes(1, byteorder='big'))
            self.buffer = 0
            self.bit_counter = 0

    # write numBits from bitPattern (most significant bit first)
    def addBits(self, bitPattern: int, numBits: int):
        if self.bit_counter + numBits < 8:
            self.buffer = (self.buffer << numBits) | int(bitPattern & ((1 << numBits) - 1))
            self.bit_counter += numBits
            return
        if not self.file:
            raise Exception('OBitstream: File not open')
        if self.bit_counter:
            freeBits = 8 - self.bit_counter
            self.buffer = (self.buffer << freeBits) | int((bitPattern >> (numBits - freeBits)) & ((1 << freeBits) - 1))
            numBits -= freeBits
            self.file.write(self.buffer.to_bytes(1, byteorder='big'))
        while numBits >= 8:
            numBits -= 8
            self.buffer = int(bitPattern >> numBits) & 255
            self.file.write(self.buffer.to_bytes(1, byteorder='big'))
        self.buffer = int(bitPattern & ((1 << numBits) - 1))
        self.bit_counter = numBits

    # write zeros to fill last byte
    def byteAlign(self):
        if self.bit_counter != 0:
            self.addBits(0, 8 - self.bit_counter)

    # terminate bitstream (and close file)
    def terminate(self):
        self.byteAlign()
        self.file.close()
        self.file = None
