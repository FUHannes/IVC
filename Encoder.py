import numpy as np

from EntropyEncoder import EntropyEncoder
from OBitstream import OBitstream


# read PGM image
def _read_image(input_path):
    file = open(input_path, 'rb')
    if not file:
        raise Exception('Encoder: Could not open image file')
    # read meta data
    header = file.readline()
    if header != b'P5\n':
        raise Exception('Encoder: No PGM image')
    imgSize = file.readline()
    maxVal = file.readline()
    if maxVal != b'255\n':
        raise Exception('Encoder: PGM image has unexpected bit depth')
    width, height = str(imgSize).split(' ')
    width = int(width[2:])
    height = int(height[:len(height) - 3])
    # create image and read data
    image = np.zeros([height, width])
    for h in range(0, height):
        for w in range(0, width):
            byte = file.read(1)
            if not byte:
                raise Exception('Encoder: PGM image is corrupted')
            image[h, w] = byte[0]
    return image


class Encoder:

    def __init__(self, input_path, output_path, block_size, QP, reconstruction_path=None):
        self.input_path = input_path
        self.output_path = output_path
        self.block_size = block_size
        self.qp = QP
        self.qs = 2 ** (self.qp / 4)
        self.image = None
        self.image_reconstructed = None
        self.image_width = 0
        self.image_height = 0
        self.entropyEncoder = None
        self.reconstruction_path = reconstruction_path

    def init_obitstream(self, img_height, img_width, path):
        outputBitstream = OBitstream(path)
        outputBitstream.addBits(img_width, 16)
        outputBitstream.addBits(img_height, 16)
        outputBitstream.addBits(self.block_size, 16)
        outputBitstream.addBits(self.qp, 8)
        return outputBitstream

    # Gets an image and return an encoded bitstream. 
    def encode_image(self):
        # read image
        self.image = _read_image(self.input_path)
        self.image_height = self.image.shape[0]
        self.image_width = self.image.shape[1]
        self.image_reconstructed = np.zeros([self.image_height, self.image_width], dtype=np.uint8)
        # open bitstream and write header
        outputBitstream = self.init_obitstream(self.image_height, self.image_width, self.output_path)
        # open reconstructed bitstream and write header
        # initialize entropy encoder
        self.entropyEncoder = EntropyEncoder(outputBitstream)
        # process image
        for yi in range(0, self.image_height, self.block_size):
            for xi in range(0, self.image_width, self.block_size):
                self.encode_block(xi, yi)
        # terminate bitstream
        self.entropyEncoder.terminate()
        outputBitstream.terminate()
        if self.reconstruction_path:
            self.write_out()

    def reconstruct_trans_coef(self, q_idx_block, x, y):
        # TODO: reconstruct transform coefficients from quantization indexes (invoke 2D Transform inverse)
        # prediction
        # TODO: invoke prediction function (see 4.3 DC prediction)
        q_idx_block += 128
        self.image_reconstructed[y:y + self.block_size, x:x + self.block_size] = np.clip(q_idx_block, 0, 255).astype('uint8')

    # encode block of current picture
    def encode_block(self, x: int, y: int):
        # accessor for current block
        currBlock = self.image[y:y + self.block_size, x:x + self.block_size]
        # prediction
        currBlock -= 128
        # TODO: invoke 2D Transform (see 4.1)
        # quantization
        qIdxBlock = np.round(currBlock / self.qs, decimals=0).astype('int')
        self.reconstruct_trans_coef(currBlock, x, y)
        # entropy coding
        self.entropyEncoder.writeQIndexBlock(qIdxBlock)

    # opening and writing a binary file
    def write_out(self):
        out_file = open(self.reconstruction_path, "wb")
        out_file.write(f'P5\n{self.image_width} {self.image_height}\n255\n'.encode())
        out_file.write(self.image_reconstructed.ravel().tobytes())
        out_file.close()
        return True
