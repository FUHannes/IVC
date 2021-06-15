import numpy as np
from tqdm import tqdm
import random

from EntropyEncoder import EntropyEncoder
from IntraPredictionCalculator import IntraPredictionCalculator
from IntraPredictionCalculator import PredictionMode
from OBitstream import OBitstream
from dct import Transformation


# read PGM image
def read_image(input_path):
    with open(input_path, 'rb') as file:
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


def read_video(input_path, width, height, n_frames):
    with open(input_path, 'rb') as file:
        n_bytes = width * height * n_frames
        frames = file.read(n_bytes)
    _frames = np.frombuffer(frames, dtype='uint8')
    _frames = _frames.reshape(n_frames, height, width)

    return _frames


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
        self.image_reconstructed_array = []
        self.entropyEncoder = None
        self.reconstruction_path = reconstruction_path
        self.raw_video = False
        self.est_bits = 0
        self.transformation = Transformation(block_size)

    def init_obitstream(self, img_height, img_width, path):
        outputBitstream = OBitstream(path)
        outputBitstream.addBits(img_width, 16)
        outputBitstream.addBits(img_height, 16)
        outputBitstream.addBits(self.block_size, 16)
        outputBitstream.addBits(self.qp, 8)
        return outputBitstream

    def set_image_size(self, width, height):
        self.image_height = height
        self.image_width = width
        self.pad_height = self.block_size - self.image_height % self.block_size if self.image_height % self.block_size != 0 else 0
        self.pad_width = self.block_size - self.image_width % self.block_size if self.image_width % self.block_size != 0 else 0

    def _add_padding(self):
        self.image = np.pad(self.image, ((0, self.pad_height), (0, self.pad_width)), "edge")

    # motion-compensated prediction (at the moment, only frame difference prediction)
    def _inter_prediction(self, x, y):
        return self.image_reconstructed_array[-1][y:y + self.block_size, x:x + self.block_size]

    # Gets an image and return an encoded bitstream.
    def encode_image(self):
        self.image = read_image(self.input_path)
        self.set_image_size(width=self.image.shape[1], height=self.image.shape[0])

        # open bitstream and write header
        self.outputBitstream = self.init_obitstream(self.image_height, self.image_width, self.output_path)

        self.encode_frame_intra(show_frame_progress=True)

        # terminate bitstream
        self.outputBitstream.terminate()
        print(f'Estimated # of bits {self.est_bits}')
        print(f'# of bits in bitstream without header {self.outputBitstream.bits_written - 56}')
        if self.reconstruction_path:
            self.image_reconstructed_array.append(self.image_reconstructed)
            self.write_out()

    def encode_video(self, width, height, n_frames):
        self.raw_video = True
        video = read_video(self.input_path, width, height, n_frames)
        self.set_image_size(width, height)

        # open bitstream and write header
        self.outputBitstream = self.init_obitstream(height, width, self.output_path)

        is_first_frame = True
        for frame in tqdm(video):
            self.image=frame
            if not is_first_frame:
                self.encode_frame_inter()
            else:
                self.encode_frame_intra()
                is_first_frame = False
            self.image_reconstructed_array.append(self.image_reconstructed)

        # terminate bitstream
        self.outputBitstream.terminate()
        print(f'Estimated # of bits {self.est_bits}')
        print(f'# of bits in bitstream without header {self.outputBitstream.bits_written - 56}')
        if self.reconstruction_path:
            self.write_out()

    # If you change this methods pay attention because is used in both encode_image and encode_video() methods
    # This method should be called for the first frame only
    def encode_frame_intra(self, show_frame_progress=False):
        # add padding
        self._add_padding()
        self.image_reconstructed = np.zeros([self.image_height + self.pad_height, self.image_width + self.pad_width],
                                            dtype=np.uint8)

        # start new arithmetic codeword for each frame
        self.entropyEncoder = EntropyEncoder(self.outputBitstream, self.block_size)

        # initialize intra prediction calculator
        self.intra_pred_calc = IntraPredictionCalculator(self.image_reconstructed, self.block_size)

        if show_frame_progress:
            total_blocks = ((self.image_height + self.pad_height) // self.block_size) * ((self.image_width + self.pad_width) // self.block_size)
            progress_bar = tqdm(total=total_blocks)

        # process image
        lagrange_multiplier = 0.1 * self.qs * self.qs
        for yi in range(0, self.image_height + self.pad_height, self.block_size):
            for xi in range(0, self.image_width + self.pad_width, self.block_size):
                if show_frame_progress:
                    progress_bar.update()

                # mode decision
                cost_mode_tuples = []
                for pred_mode in PredictionMode:
                    cost_mode_tuples.append((self.test_encode_block_intra_pic(xi, yi, pred_mode, lagrange_multiplier), pred_mode))
                min_cost_mode = min(cost_mode_tuples, key = lambda t: t[0])
                optimal_pred_mode = min_cost_mode[1]

                # encoding using selected mode
                self.encode_block_intra_pic(xi, yi, optimal_pred_mode)

        if show_frame_progress:
            progress_bar.close()

        # terminate arithmetic codeword (but keep output bitstream alive)
        self.entropyEncoder.terminate()

    # This method should be called for all frames except the first one
    def encode_frame_inter(self):
        # add padding
        self._add_padding()
        self.image_reconstructed = np.zeros([self.image_height + self.pad_height, self.image_width + self.pad_width],
                                            dtype=np.uint8)

        # start new arithmetic codeword for each frame
        self.entropyEncoder = EntropyEncoder(self.outputBitstream, self.block_size)

        # initialize intra prediction calculator
        self.intra_pred_calc = IntraPredictionCalculator(self.image_reconstructed, self.block_size)

        # process image
        lagrange_multiplier = 0.1 * self.qs * self.qs
        for yi in range(0, self.image_height + self.pad_height, self.block_size):
            for xi in range(0, self.image_width + self.pad_width, self.block_size):
                # choose random motion vector: Replace later with motion estimation
                max_motion = 0 #self.block_size
                mx = random.randint(-max_motion, max_motion)
                my = random.randint(-max_motion, max_motion)

                # mode decision between inter and dc mode
                inter_mode_cost = self.test_encode_block_inter_pic(xi, yi, 1, mx, my, lagrange_multiplier)
                dc_mode_cost = self.test_encode_block_inter_pic(xi, yi, 0, 0, 0, lagrange_multiplier)
                if inter_mode_cost < dc_mode_cost:
                    self.encode_block_inter_pic(xi, yi, 1, mx, my)
                else:
                    self.encode_block_inter_pic(xi, yi, 0, 0, 0)

        # terminate arithmetic codeword (but keep output bitstream alive)
        self.entropyEncoder.terminate()

    def reconstruct_block(self, pred_block, q_idx_block, x, y, prediction_mode, update_rec_image=True):
        # reconstruct transform coefficients from quantization indexes
        recBlock = q_idx_block * self.qs
        # invoke 2D Transform inverse
        recBlock = self.transformation.backward_transform(recBlock, prediction_mode)
        # invoke prediction function (see 4.3 DC prediction)
        recBlock += pred_block

        recBlock = np.clip(recBlock, 0, 255).astype('uint8')

        if update_rec_image:
            self.image_reconstructed[y:y + self.block_size, x:x + self.block_size] = recBlock

        return recBlock

    # encode block of current picture
    def encode_block_intra_pic(self, x: int, y: int, pred_mode: PredictionMode):
        # accessor for current block
        orgBlock = self.image[y:y + self.block_size, x:x + self.block_size]
        # prediction
        predBlock = self.intra_pred_calc.get_prediction(x, y, pred_mode)
        predError = orgBlock.astype('int') - predBlock
        # dct
        transCoeff = self.transformation.forward_transform(predError, pred_mode)
        # quantization
        qIdxBlock: np.ndarray = (np.sign(transCoeff) * np.floor((np.abs(transCoeff) / self.qs) + 0.4)).astype('int')
        # reconstruction
        self.reconstruct_block(predBlock, qIdxBlock, x, y, pred_mode)

        if pred_mode == PredictionMode.PLANAR_PREDICTION or pred_mode == PredictionMode.DC_PREDICTION:
            # diagonal scan
            scanned_block = sort_diagonal(qIdxBlock)
        elif pred_mode == PredictionMode.HORIZONTAL_PREDICTION:
            # vertical scan: Transposed block
            scanned_block = qIdxBlock.T
        elif pred_mode == PredictionMode.VERTICAL_PREDICTION:
            # horizontal scan: unchanged block
            scanned_block = qIdxBlock

        # Sum estimated bits per block
        self.est_bits += self.entropyEncoder.est_block_bits_intra_pic(pred_mode, scanned_block)
        # actual entropy encoding
        self.entropyEncoder.write_block_intra_pic(scanned_block, pred_mode)

    # encode block of current picture
    def encode_block_inter_pic(self, x: int, y: int, inter_flag: int, mx: int, my: int):
        # accessor for current block
        orgBlock = self.image[y:y + self.block_size, x:x + self.block_size]

        if inter_flag:
            # clipping mvec into image dimensions (+ padding border)
            mx = max(-x, min(mx, self.image_width + self.pad_width - (x + self.block_size)))
            my = max(-y, min(my, self.image_height + self.pad_height - (y + self.block_size)))

            # Inter prediction
            predBlock = self._inter_prediction(x + mx, y + my)
        else:
            predBlock = self.intra_pred_calc.get_prediction(x, y, PredictionMode.DC_PREDICTION)

        predError = orgBlock.astype('int') - predBlock
        # dct
        transCoeff = self.transformation.forward_transform(predError, PredictionMode.DC_PREDICTION) # set predMode=DC for using correct transform
        # quantization
        qIdxBlock: np.ndarray = (np.sign(transCoeff) * np.floor((np.abs(transCoeff) / self.qs) + 0.4)).astype('int')
        # reconstruction
        self.reconstruct_block(predBlock, qIdxBlock, x, y, PredictionMode.DC_PREDICTION) # set predMode=DC for using correct transform
        # diagonal scanning
        scanned_block = sort_diagonal(qIdxBlock)
        # Sum estimated bits per block
        self.est_bits += self.entropyEncoder.est_block_bits_inter_pic(scanned_block, inter_flag, mx, my)
        # actual entropy encoding
        self.entropyEncoder.write_block_inter_pic(scanned_block, inter_flag, mx, my)

    # Calculate lagrangian cost for given block and prediction mode.
    def test_encode_block_intra_pic(self, x: int, y: int, pred_mode: PredictionMode, lagrange_multiplier):
        # Accessor for current block.
        org_block = self.image[y:y + self.block_size, x:x + self.block_size]

        # Prediction, Transform, Quantization.
        pred_block = self.intra_pred_calc.get_prediction(x, y, pred_mode)
        pred_error = org_block.astype('int') - pred_block

        trans_coeff = self.transformation.forward_transform(pred_error,pred_mode)

        q_idx_block = (np.sign(trans_coeff) * np.floor((np.abs(trans_coeff) / self.qs) + 0.4)).astype('int')

        rec_block = self.reconstruct_block(pred_block, q_idx_block, x, y, pred_mode, update_rec_image=False)

        # Distortion calculation using SSD.
        distortion = np.sum(np.square(org_block - rec_block))

        if pred_mode == PredictionMode.PLANAR_PREDICTION or pred_mode == PredictionMode.DC_PREDICTION:
            # diagonal scan
            scanned_block = sort_diagonal(q_idx_block)
        elif pred_mode == PredictionMode.HORIZONTAL_PREDICTION:
            # vertical scan: Transposed block
            scanned_block = q_idx_block.T
        elif pred_mode == PredictionMode.VERTICAL_PREDICTION:
            # horizontal scan: unchanged block
            scanned_block = q_idx_block

        bitrate_estimation = self.entropyEncoder.est_block_bits_intra_pic(pred_mode, scanned_block)

        # Return Lagrangian cost.
        return distortion + lagrange_multiplier * bitrate_estimation

    # Calculate lagrangian cost for given block: Extent and use later
    def test_encode_block_inter_pic(self, x: int, y: int, inter_flag: int, mx: int, my: int, lagrange_multiplier):
        # Accessor for current block.
        org_block = self.image[y:y + self.block_size, x:x + self.block_size]

        # Prediction
        if inter_flag:
            # clipping mvec into image dimensions (+ padding border)
            mx = max(-x, min(mx, self.image_width + self.pad_width - (x + self.block_size)))
            my = max(-y, min(my, self.image_height + self.pad_height - (y + self.block_size)))

            # Inter prediction
            pred_block = self._inter_prediction(x + mx, y + my)
        else:
            pred_block = self.intra_pred_calc.get_prediction(x, y, PredictionMode.DC_PREDICTION)

        # Prediction, Transform, Quantization.
        pred_error = org_block.astype('int') - pred_block

        trans_coeff = self.transformation.forward_transform(pred_error, PredictionMode.DC_PREDICTION) # set predMode=DC for using correct transform

        q_idx_block = (np.sign(trans_coeff) * np.floor((np.abs(trans_coeff) / self.qs) + 0.4)).astype('int')

        rec_block = self.reconstruct_block(pred_block, q_idx_block, x, y, PredictionMode.DC_PREDICTION, update_rec_image=False) # set predMode=DC for using correct transform

        # Distortion calculation using SSD.
        distortion = np.sum(np.square(org_block - rec_block))

        # diagonal scan
        scanned_block = sort_diagonal(q_idx_block)

        bitrate_estimation = self.entropyEncoder.est_block_bits_inter_pic(scanned_block, inter_flag, mx, my)

        # Return Lagrangian cost.
        return distortion + lagrange_multiplier * bitrate_estimation

    # opening and writing a binary file
    def write_out(self):
        out_file = open(self.reconstruction_path, "wb")
        # write PGM header only if input was PGM image
        if not self.raw_video:
            out_file.write(f'P5\n{self.image_width} {self.image_height}\n255\n'.encode())
        # output all reconstructed frames (remove padding just before output)
        for image_reconstructed in self.image_reconstructed_array:
            # remove padding
            image_reconstructed = image_reconstructed[:self.image_height, :self.image_width]
            out_file.write(image_reconstructed.ravel().tobytes())
        out_file.close()
        return True
