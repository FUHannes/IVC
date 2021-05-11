import numpy as np
from entropy_decoder import EntropyDecoder
import IBitstream


class Decoder:

    def __init__(self, input_path, output_path):
        self.output_path = output_path
        self.bitstream = IBitstream(input_path)
        self.image_width = int(self.bitstream.getBits(16))
        self.image_height = int(self.bitstream.getBits(16))
        self.block_size = int(self.bitstream.getBits(16))
        self.qp = int(self.bitstream.getBits(8))
        self.qs = 2**(self.qp/4)
        self.blocks_width = self.image_width / self.block_size
        self.blocks_height = self.image_height / self.block_size
        self.image = np.zeros([self.image_width, self.image_height, self.block_size, self.block_size], dtype=np.int8)
        self.ent_dec = EntropyDecoder(self.bitstream)

    def decode_block(self, x: int, y: int):
        ent_dec_block = self.ent_dec.readQIndexBlock(self.block_size)
        ent_dec_block = ent_dec_block.reshape([self.block_size, self.block_size])
        dequantized_block = ent_dec_block * self.qs
        self.image[x][y] = np.clip(dequantized_block + 128, 0, 255).astype('uint8')
        # entropy decoding (EntropyDecoder)
        # de-quantization
        # adding prediction (128)
        # clipping (0,255)

    # opening and writing a binary file
    def write_out(self):
        out_file = open(self.output_path, "wb")
        pgm_metadata = f'P5\n{self.image_width} {self.image_height}\n255\n'.encode()
        pgm_image_data = np.swapaxes(self.image, 1, 2).ravel().tobytes()
        decoded_stream = pgm_metadata + pgm_image_data
        out_file.write(decoded_stream)
        out_file.close()
        return True

    def decode_image(self):
        for xi in range(self.blocks_width):
            for yi in range(self.blocks_height):
                self.decode_block_(xi, yi)
