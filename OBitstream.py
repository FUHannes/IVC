# authors: Giovanni Sorice, Manuel Welte

class OBitstream:
    def __init__(self, byteArray: []):
        self.byteArray = byteArray
        self.buffer = 0
        self.bit_counter = 0

    # add bit to bitstream
    def addBit(self, bit: int):  # only 0 or 1
        self.buffer = self.buffer << 1
        self.buffer += bit
        self.bit_counter += 1
        if self.bit_counter == 8:
            self.byteArray.append(self.buffer.to_bytes(1, byteorder='big'))
            print(self.buffer)
            self.buffer = 0
            self.bit_counter = 0

    # write numBits from bitPattern (most significant bit first)
    def addBits(self, bitPattern: int, numBits: int):
        for i in range(numBits, 0, -1):
            # Take the single interesting bit
            bit = (bitPattern >> (i - 1)) & int(1)
            self.addBit(bit)

    # write zeros to fill last byte
    def byteAlign(self) -> list:
        for i in range(self.bit_counter, 8):
            # Take the single interesting bit
            self.addBit(0)
        return self.byteArray


def test_OBitstream():
    OB = OBitstream([])
    OB.addBit(1)
    OB.addBits(9, 5)
    OB.addBits(5, 3)
    OB.addBits(28, 6)
    OB.addBit(0)
    OB.addBits(2, 2)
    l = [(166).to_bytes(1, byteorder='big'), (184).to_bytes(1, byteorder='big'), (128).to_bytes(1, byteorder='big')]
    assert OB.byteAlign() == l
