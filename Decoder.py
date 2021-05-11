import numpy as np
from entropy_decoder import EntropyDecoder
from IBitstream import IBitstream


class Decoder:

    def __init__(self, input_path, output_path):
        self.output_path = output_path
        self.bitstream = IBitstream(input_path)
        self.image_width = self.bitstream.get_bits(16)
        self.image_height = self.bitstream.get_bits(16)
        self.block_size = self.bitstream.get_bits(16)
        self.qp = self.bitstream.get_bits(8)
        self.qs = 2**(self.qp/4)
        self.blocks_width = self.image_width // self.block_size
        self.blocks_height = self.image_height // self.block_size
        self.image = np.zeros([self.image_width, self.image_height, self.block_size, self.block_size], dtype=np.int8)
        self.ent_dec = EntropyDecoder(self.bitstream)

    def decode_block(self, x: int, y: int):
        # entropy decoding (EntropyDecoder)
        # de-quantization
        # adding prediction (128)
        # clipping (0,255)
        ent_dec_block = self.ent_dec.readQIndexBlock(self.block_size)
        ent_dec_block = np.array(ent_dec_block).reshape([self.block_size, self.block_size])
        dequantized_block = ent_dec_block * self.qs
        self.image[y][x] = np.clip(dequantized_block + 128, 0, 255).astype('uint8')

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
        for yi in range(int(self.blocks_height)):
            for xi in range(int(self.blocks_width)):
                self.decode_block(xi, yi)
        self.write_out()
