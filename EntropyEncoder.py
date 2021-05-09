import sys
from OBitstream import OBitstream
from typing import Callable, List

def bitsUsed(value: int) -> int:
    counter = 0

    while value != 0:    
        value = int(value // 2)
        counter += 1
        

    return counter

class EntropyEncoder:
    def __init__(self, bitstream: OBitstream):
        self.bitstream = bitstream

    def expGolomb( self, value: int ): 
        assert(value >= 0)

        classIndex = bitsUsed(value + 1) - 1 # class index

        self.bitstream.addBits(1, classIndex + 1)
        self.bitstream.addBits(value + 1, classIndex)


    def writeQIndex(self, level: int):
        """
        writes a positive or negative value with exp golomb coding and sign bit
        """

        # bitsUsed is "real" bits used - 1
        self.expGolomb(abs(level))
        
        if level > 0:
            self.bitstream.addBit(0)
        elif level < 0:
            self.bitstream.addBit(1)

    def writeQIndexBlock( self, values: List[int]):
        """
        writes all values sequential to the bitstream
        """
        for value in values:
            self.writeQIndex(value)

def runTest(name: str, testFunc: Callable):
    tName = f"{name} > {testFunc.__name__}"
    print(f"{tName} | Running")
    try:
        testFunc()
    except Exception as e:
        print(f"{tName} failed: {e}")
        raise e
    print(f"{tName} | Finished")

def test_EntropyEncoder():

    def test1():
        stream = OBitstream([])
        enc = EntropyEncoder(stream)
        enc.writeQIndex(0)
        enc.bitstream.byteAlign()
        # 1 [000 0000]
        assert(enc.bitstream.byteArray == [b'\x80'])

    def test2():
        stream = OBitstream([])
        enc = EntropyEncoder(stream)
        enc.writeQIndex(16)
        enc.bitstream.byteAlign()
        # 0000 1000 1 [000 0000]
        assert(enc.bitstream.byteArray == [b'\x08', b'\x80'])

    def test3():
        stream = OBitstream([])
        enc = EntropyEncoder(stream)
        enc.writeQIndex(-31)
        enc.bitstream.byteAlign()
        # 0000 0100 0001 [0000]
        assert(enc.bitstream.byteArray == [b'\x04', b'\x10'])

    runTest("EntropyEncoder", test1)
    runTest("EntropyEncoder", test2)
    runTest("EntropyEncoder", test3)
    

if __name__ == "__main__":
    test_EntropyEncoder()
