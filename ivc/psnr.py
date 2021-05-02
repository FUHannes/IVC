import math
import subprocess
import pandas as pd
import os
import matplotlib.pyplot as plt


from Encoder import Encoder as Encoder
from Decoder import Decoder as Decoder

PSNR_TOOL_PATH = 'tools/psnr-images/bin/psnrImg'

DATA_ROOT_PATH = 'dat'

IMAGES_ROOT_PATH = 'images'
PGM_ORIGINAL_PATH = os.path.join(IMAGES_ROOT_PATH, 'original')
BITSTREAM_PATH = os.path.join(IMAGES_ROOT_PATH, 'bitstream')
PGM_RECONSTRUCTION_PATH = os.path.join(IMAGES_ROOT_PATH, 'reconstruction')

PGM_SUFFIX = '.pgm'
BITSTREAM_SUFFIX = '.jpeg'  # todo: check suffix with other groups
DATA_SUFFIX = '.dat'


def generate_data(filename, version):
    input_path = os.path.join(PGM_ORIGINAL_PATH, filename + PGM_SUFFIX)

    if not os.path.exists(BITSTREAM_PATH):
        os.mkdir(BITSTREAM_PATH)
    bitstream_path = os.path.join(BITSTREAM_PATH, filename + BITSTREAM_SUFFIX)

    if not os.path.exists(PGM_RECONSTRUCTION_PATH):
        os.mkdir(PGM_RECONSTRUCTION_PATH)
    output_path = os.path.join(PGM_RECONSTRUCTION_PATH, filename + PGM_SUFFIX)

    df = pd.DataFrame(columns=['bpp', 'db'])

    for index, quality in enumerate([8, 12, 16, 20, 24]):
        Encoder(block_size=16, multithreaded=False)(input_path, bitstream_path)  # todo: check interface with other groups
        Decoder(multithreaded=False)(bitstream_path, output_path)  # todo: check interface with other groups

        process = subprocess.run(
            [PSNR_TOOL_PATH, input_path, output_path, bitstream_path],
            stdout=subprocess.PIPE,
        )

        stdout = process.stdout.decode("utf-8")
        bpp, db = stdout.split(' bpp ')
        bpp, db = float(bpp), float(db.replace(' dB', ''))
        db = 0.0 if math.isinf(db) else db
        df.loc[index] = [bpp, db]

    version_path = os.path.join(DATA_ROOT_PATH, version)
    if not os.path.exists(version_path):
        os.mkdir(version_path)
    df.to_pickle(os.path.join(version_path, filename + DATA_SUFFIX))


def plot_data(filename, version, versions):
    versions = versions.split(',') + [version] if versions else version

    fig = plt.figure(figsize=(10, 5))
    for version in versions:
        ver = pd.DataFrame(pd.read_pickle(os.path.join(DATA_ROOT_PATH, version, filename + DATA_SUFFIX)))
        plt.plot(ver['bpp'], ver['db'], label=version)
        print(ver)
    jpeg_data = None  # todo: implement
    # jpeg = pd.DataFrame(jpeg_data)
    # plt.plot(jpeg['bpp'], jpeg['db'], label='jpeg', color='red')

    plt.xlabel('X: Bits (bpp)')
    plt.ylabel('Y: PSNR (db)')
    plt.legend()
    fig.savefig("PSNR_test_curves.png")
    plt.show()
