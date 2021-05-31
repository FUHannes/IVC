import numpy as np

from EntropyEncoder import EntropyEncoder
from IntraPredictionCalculator import IntraPredictionCalculator
from IntraPredictionCalculator import PredictionMode
from IntraPredictionCalculator import random_prediction_mode
from OBitstream import OBitstream
from dct import Transformation


# import matplotlib.pyplot as plt


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
    image = np.zeros([height, width], dtype=np.uint8)
    for h in range(0, height):
        for w in range(0, width):
            byte = file.read(1)
            if not byte:
                raise Exception('Encoder: PGM image is corrupted')
            image[h, w] = byte[0]
    return image


def sort_diagonal(mat: np.ndarray) -> np.ndarray:
    res = []
    (rows, columns) = mat.shape
    for line in range(1, (rows + columns)):

        start_col = max(0, line - rows)
        count = min(line, (columns - start_col), rows)

        for j in range(0, count):
            res.append(mat[min(rows, line) - j - 1][start_col + j])
    return np.array(res)


class Encoder:

    def __init__(self, input_path, output_path, block_size, QP, reconstruction_path=None):
        self.input_path = input_path
        self.output_path = output_path
        self.block_size = block_size
        self.qp = QP
        self.qs = 2 ** (self.qp / 4)
        self.image_reconstructed = None
        self.entropyEncoder = None
        self.reconstruction_path = reconstruction_path
        self._read_image()
        self.pad_height = self.block_size - self.image_height % self.block_size if self.image_height % self.block_size != 0 else 0
        self.pad_width = self.block_size - self.image_width % self.block_size if self.image_width % self.block_size != 0 else 0
        self.est_bits = 0

    def init_obitstream(self, img_height, img_width, path):
        outputBitstream = OBitstream(path)
        outputBitstream.addBits(img_width, 16)
        outputBitstream.addBits(img_height, 16)
        outputBitstream.addBits(self.block_size, 16)
        outputBitstream.addBits(self.qp, 8)
        return outputBitstream

    # read image
    def _read_image(self):
        self.image = _read_image(self.input_path)
        self.image_height = self.image.shape[0]
        self.image_width = self.image.shape[1]

    def _add_padding(self):
        self.image = np.pad(self.image, ((0, self.pad_height), (0, self.pad_width)), "edge")

        # for testing (include matplotlib)    
        # plt.imshow(image)
        # plt.show()

    # Gets an image and return an encoded bitstream. 
    def encode_image(self):
        # add padding
        self._add_padding()
        self.image_reconstructed = np.zeros([self.image_height + self.pad_height, self.image_width + self.pad_width],
                                            dtype=np.uint8)
        # open bitstream and write header
        outputBitstream = self.init_obitstream(self.image_height, self.image_width, self.output_path)
        # initialize intra prediction calculator
        self.intra_pred_calc = IntraPredictionCalculator(self.image_reconstructed, self.block_size)
        # initialize entropy encoder
        self.entropyEncoder = EntropyEncoder(outputBitstream)
        # process image
        for yi in range(0, self.image_height + self.pad_height, self.block_size):
            for xi in range(0, self.image_width + self.pad_width, self.block_size):
                self.encode_block(xi, yi)
        # terminate bitstream
        self.entropyEncoder.terminate()
        outputBitstream.terminate()
        print(f'Estimated # of bits {self.est_bits}')
        print(f'# of bits in bitstream without header {outputBitstream.bits_written - 56}')
        if self.reconstruction_path:
            self.image_reconstructed = self.image_reconstructed[:self.image_height, :self.image_width]
            self.write_out()

    def reconstruct_block(self, pred_block, q_idx_block, x, y):
        # reconstruct transform coefficients from quantization indexes
        recBlock = q_idx_block * self.qs
        # invoke 2D Transform inverse
        recBlock = Transformation().backward_dct(recBlock)
        # invoke prediction function (see 4.3 DC prediction)
        recBlock += pred_block
        self.image_reconstructed[y:y + self.block_size, x:x + self.block_size] = np.clip(recBlock, 0, 255).astype(
            'uint8')

    # encode block of current picture
    def encode_block(self, x: int, y: int):
        # accessor for current block
        orgBlock = self.image[y:y + self.block_size, x:x + self.block_size]
        # prediction
        prediction_mode = random_prediction_mode()
        predBlock = self.intra_pred_calc.get_prediction(x, y, prediction_mode)
        predError = orgBlock.astype('int') - predBlock
        # dct
        transCoeff = Transformation().forward_dct(predError)
        # quantization
        qIdxBlock = (np.sign(transCoeff) * np.floor((np.abs(transCoeff)/self.qs) + 0.4)).astype('int')
        # reconstruction
        self.reconstruct_block(predBlock, qIdxBlock, x, y)
        # diagonal scan
        diagonal = sort_diagonal(qIdxBlock)
        # Sum estimated bits per block
        self.est_bits += self.entropyEncoder.estBits(prediction_mode, diagonal)
        # actual entropy encoding
        self.entropyEncoder.writeQIndexBlock(diagonal, prediction_mode)

    # opening and writing a binary file
    def write_out(self):
        out_file = open(self.reconstruction_path, "wb")
        out_file.write(f'P5\n{self.image_width} {self.image_height}\n255\n'.encode())
        out_file.write(self.image_reconstructed.ravel().tobytes())
        out_file.close()
        return True
