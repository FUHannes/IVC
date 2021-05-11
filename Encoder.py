import numpy as np

from EntropyEncoder import EntropyEncoder
from OBitstream import OBitstream


class PGM:
    def __init__(self, raw_bytes):
        self.raw_bytes = raw_bytes
        self._get_img_data_()

    def _get_img_data_(self):
        self.width = 0
        self.height = 0
        self.max_pixel_val = 0
        self.data_start = -1

        width_done = False
        line = 0
        for byte in self.raw_bytes:
            self.data_start += 1

            if chr(byte) == '\n':
                line += 1
                continue

            if line == 1:
                if chr(byte) == ' ':
                    width_done = True
                    continue
                if not width_done:
                    self.width = self.width * 10 + int(chr(byte))
                else:
                    self.height = self.height * 10 + int(chr(byte))

            if line == 2 and not chr(byte) == ' ':
                self.max_pixel_val = self.max_pixel_val * 10 + int(chr(byte))

            if line == 3:
                break

        self.data = self.raw_bytes[self.data_start:]


class Encoder:

    def __init__(self, block_size=100, QP=12):
        self.block_size = block_size
        self.QP = QP
        self.outputBitstream = OBitstream()
        self.entropyEncoder = EntropyEncoder(self.outputBitstream)

    # Gets an image and return an encoded bitstream. 
    def encode_image(self, input_path, output_path=None):
        self._read_image(input_path)
        self._encode()
        if output_path is not None:
            self._write_out(output_path)
        return self.encoded_stream

    def _read_image(self, input_path):
        in_file = open(input_path, 'rb')
        self.raw_bytes = in_file.read()
        in_file.close()
        return self.raw_bytes

    def _write_out(self, output_path):
        with open(output_path, 'wb') as out_file:
            out_file.write(self.encoded_stream)
        return True

    def _quantize(self, data_blocks: np.array):
        # Get amount of blocks in x, y direction.
        x_block_idx, y_block_idx, _, _ = data_blocks.shape
        # Cast to int8 for signed int.
        data_blocks = data_blocks.astype('int8')
        # quantization step size
        QS = 2 ** (self.QP / 4)
        # Quantize block-by-block.
        for i in range(x_block_idx):
            for j in range(y_block_idx):
                data_blocks[i, j] = (data_blocks[i, j] - 128).astype('int8')
                data_blocks[i, j] = (np.round((data_blocks[i, j] / QS), decimals=0)).astype('int8')
        return data_blocks

    def _encode(self, raw_bytes=None):
        if raw_bytes is not None:
            self.raw_bytes = raw_bytes

        # Parse all the pgm (meta-)data.
        self.pgm = PGM(self.raw_bytes)

        # Cut away additional data and convert to ndarray for performance improvements.
        data = np.array(bytearray(self.pgm.data)[:self.pgm.height * self.pgm.width])

        blocks_x = int(self.pgm.width / self.block_size)
        blocks_y = int(self.pgm.height / self.block_size)
        # Currently no img padding so the img size must be an exact multiple of the block size in both directions.
        assert self.pgm.width % self.block_size == 0 and self.pgm.height % self.block_size == 0

        # Restructure image into blocks.
        data_blocks = np.swapaxes(data.reshape([blocks_x, self.block_size, blocks_y, self.block_size]), 1, 2)

        # Quantize and entropy-_encode.
        data_blocks = self._quantize(data_blocks)
        self.entropyEncoder.writeQIndexBlock(data_blocks)

        # Construct output bitstream. 
        metadata = self.block_size.to_bytes(2, 'big') + blocks_x.to_bytes(2, 'big') + blocks_y.to_bytes(2, 'big') + self.QP.to_bytes(1, 'big')

        self.encoded_stream = metadata + self.entropyEncoder.bitstream
        return self.encoded_stream
