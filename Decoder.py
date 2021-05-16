import numpy as np
from EntropyDecoder import EntropyDecoder
from IBitstream import IBitstream
from dct import Transformation

class Decoder:

    def __init__(self, input_path, output_path):
        self.output_path = output_path
        self.bitstream = IBitstream(input_path)
        self.image_width = self.bitstream.get_bits(16)
        self.image_height = self.bitstream.get_bits(16)
        self.block_size = self.bitstream.get_bits(16)
        self.qp = self.bitstream.get_bits(8)
        self.qs = 2**(self.qp/4)
        self.image = np.zeros([self.image_height, self.image_width], dtype=np.uint8)
        self.ent_dec = EntropyDecoder(self.bitstream)

    def decode_block(self, x: int, y: int):
        # entropy decoding (EntropyDecoder)
        ent_dec_block = self.ent_dec.readQIndexBlock(self.block_size)
        # de-quantization
        recBlock = ent_dec_block * self.qs
        # idct
        recBlock = Transformation().backward_dct(recBlock)
        # adding prediction (128)
        recBlock += 128
        # clipping (0,255) and store to image
        self.image[y:y+self.block_size, x:x+self.block_size] = np.clip(recBlock, 0, 255).astype('uint8')

    # opening and writing a binary file
    def write_out(self):
        out_file = open(self.output_path, "wb")
        out_file.write( f'P5\n{self.image_width} {self.image_height}\n255\n'.encode() )
        out_file.write( self.image.ravel().tobytes() )
        out_file.close()
        return True

    def decode_image(self):
        for yi in range(0,self.image_height,self.block_size):
            for xi in range(0,self.image_width,self.block_size):
                self.decode_block(xi, yi)
        self.ent_dec.terminate()
        self.write_out()
