
import typing

from arithBase  import LPSTable
from arithBase  import RenormTable
from arithBase  import ProbModel
from IBitstream import IBitstream


#----- arithmetic decoder  -----
class ArithDecoder:
    
    # constructor:
    #    - bitstream = IBitstream  object
    #    - initialize  class  members  
    def __init__(self, bitstream):
        self.bitstream      = bitstream
        self.bitstream.byteAlign()
        self.range:int      = 510
        self.value:int      = self.bitstream.get_bits( 16 )
        self.bitsNeeded:int = -8
    
    
    # adaptive coding:
    #  - decodes binary decision (bin) using specified probability model
    #  - updates probability model based on value of bin
    def decodeBin( self, probModel ) -> int:
        bin:int         = probModel.mps()
        LPS:int         = LPSTable[ probModel.state() ][ ( self.range >> 6 ) - 4 ]
        self.range     -= LPS
        scaledRange:int = self.range << 7
        if self.value < scaledRange:
            if scaledRange < (256 << 7):
                self.range       = scaledRange >> 6
                self.value      += self.value
                self.bitsNeeded += 1
                if self.bitsNeeded == 0:
                    self.bitsNeeded = -8
                    self.value += self.bitstream.get_bits(8)
            probModel.updateMPS()
        else:
            bin              = 1 - bin
            numBits:int      = RenormTable[ LPS >> 3 ]
            self.value       = ( self.value - scaledRange ) << numBits
            self.range       = LPS << numBits
            self.bitsNeeded += numBits
            if self.bitsNeeded >= 0:
                self.value += ( self.bitstream.get_bits(8) << self.bitsNeeded )
                self.bitsNeeded -= 8
            probModel.updateLPS()
        return bin


    # wrapper for decode() to get multiple bins
    def decodeBins( self, numBins:int, probModel ) -> int:
        value:int = 0
        while numBins:
            numBins -= 1
            value = ( value << 1 ) | self.decodeBin(probModel)
        return value


    # bypass coding of a single bin
    def decodeBinEP( self ) -> int:
        self.value      += self.value
        self.bitsNeeded += 1
        if  self.bitsNeeded >= 0:
            self.bitsNeeded  = -8
            self.value  += self.bitstream.get_bits(8)
        scaledRange:int = self.range << 7
        if  self.value >= scaledRange:
            self.value -= scaledRange
            return 1
        return 0

    
    # bypass coding of multiple bins
    def decodeBinsEP( self, numBins: int ) -> int:
        value:int = 0
        while numBins > 8:
            self.value <<= 8
            self.value += int( self.bitstream.get_bits(8) << ( 8 + self.bitsNeeded ) )
            scaledRange:int = self.range << 15
            for i in range(8):
                value += value
                scaledRange >>= 1
                if self.value >= scaledRange:
                    value += 1
                    self.value -= scaledRange
            numBins -= 8
        self.bitsNeeded += numBins
        self.value <<= numBins
        if self.bitsNeeded >= 0:
            self.value += int( self.bitstream.get_bits(8) << self.bitsNeeded )
            self.bitsNeeded -= 8
        scaledRange:int = self.range << (numBins + 7)
        for i in range(numBins):
            value += value
            scaledRange >>= 1
            if self.value >= scaledRange:
                value += 1
                self.value -= scaledRange
        return value


    # finish (return value "true" indicates success)
    def finish( self ) -> bool:
        self.range -= 2
        scaledRange:int = self.range << 7
        if self.value >= scaledRange:
            return 1
        if scaledRange < ( 256 << 7 ):
            self.range  = scaledRange >> 6
            self.value += self.value
            self.bitsNeeded += 1
            if self.bitsNeeded == 0:
                self.bitsNeeded = -8
                self.value  += self.bitstream.get_bits( 8 )
        return 0


