class EntropyDecoder:
    def __init__ ( self , bitstream ):
        self.bitstream = bitstream
        
    def readLevel ( self ):

        out_integer_array=[]

        current_red_code=1
        reading_blue_part = True
        red_length = 0
        for bit in self.bitstream:
            if reading_blue_part:
                red_length+=1
                reading_blue_part = not bit
            else:
                current_red_code * 2 + int(bit) #ok der teil wäre wohl in c wesentlich schneller (current_red_code << 1 + bit)
                red_length-=1
                if red_length == 0:
                    out_integer_array.append(current_red_code-1)
                    current_red_code=1
                    reading_blue_part = True

        return out_integer_array #maybe as bytes or idk

