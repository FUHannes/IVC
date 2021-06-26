import math
import subprocess
import pandas as pd
import os
import matplotlib.pyplot as plt


from Encoder import Encoder as Encoder
from Decoder import Decoder as Decoder

# todo: adapt source of tool to your file structure
PSNR_TOOL_PATH = 'tools/psnr-images/bin/GNU-9.3.0/psnrImg'

DATA_ROOT_PATH = 'dat'

IMAGES_ROOT_PATH = 'images'
PGM_ORIGINAL_PATH = os.path.join(IMAGES_ROOT_PATH, 'original')
BITSTREAM_PATH = os.path.join(IMAGES_ROOT_PATH, 'bitstream')
PGM_RECONSTRUCTION_PATH = os.path.join(IMAGES_ROOT_PATH, 'reconstruction')

PGM_SUFFIX = '.pgm'
BITSTREAM_SUFFIX = '.txt'
DATA_SUFFIX = '.dat'


def generate_data(filename, version, block_size=16):
    input_path = os.path.join(PGM_ORIGINAL_PATH, filename + PGM_SUFFIX)

    if not os.path.exists(BITSTREAM_PATH):
        os.mkdir(BITSTREAM_PATH)
    bitstream_path = os.path.join(BITSTREAM_PATH, filename + BITSTREAM_SUFFIX)

    if not os.path.exists(PGM_RECONSTRUCTION_PATH):
        os.mkdir(PGM_RECONSTRUCTION_PATH)
    output_path = os.path.join(PGM_RECONSTRUCTION_PATH, filename + PGM_SUFFIX)

    df = pd.DataFrame(columns=['bpp', 'db'])

    for index, quality in enumerate([8, 12, 16, 20, 24]):
        enc = Encoder(input_path, bitstream_path, block_size, quality)
        enc.encode_image()
        dec = Decoder(bitstream_path, output_path, pgm=True)
        dec.decode_all_frames()

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
    print(version)
    if not os.path.exists(version_path):
        os.mkdir(version_path)
    df.to_pickle(os.path.join(version_path, filename + DATA_SUFFIX))


def parse_jpeg_data():
    jpeg_pgm_path = os.path.join(DATA_ROOT_PATH, 'JPEG_PGM' + DATA_SUFFIX)

    version_path = os.path.join(DATA_ROOT_PATH, 'jpeg')
    if not os.path.exists(version_path):
        os.mkdir(version_path)

    with open(jpeg_pgm_path) as jpeg_pgm_file:
        filecontent = jpeg_pgm_file.read()

    # data for different files is separated by two blank lines
    all_data = filecontent.split('\n\n\n')

    for i in range(1, len(all_data)):
        file_data = all_data[i].split('\n')

        # the first line is a comment, the second line is the filename surrounded by quotation marks
        filename = file_data[1].strip('"')

        df = pd.DataFrame(columns=['bpp', 'db'])

        for j in range(0, 100):
            line_data = file_data[j+2].split()

            bpp = float(line_data[1])
            db = float(line_data[3])
            df.loc[j] = [bpp, db]

        df.to_pickle(os.path.join(version_path, filename + DATA_SUFFIX))


def plot_data(filename, version, versions):
    versions = versions.split(',') + [version] if versions else [version]

    fig = plt.figure(figsize=(20, 12))
    for version in versions:
        ver = pd.DataFrame(pd.read_pickle(os.path.join(
            DATA_ROOT_PATH, version, filename + DATA_SUFFIX)))
        plt.plot(ver['bpp'], ver['db'], label=version)

    jpeg_path = os.path.join(DATA_ROOT_PATH, 'jpeg', filename + DATA_SUFFIX)
    if not os.path.exists(jpeg_path):
        parse_jpeg_data()
    jpeg = pd.DataFrame(pd.read_pickle(jpeg_path))
    plt.plot(jpeg['bpp'], jpeg['db'], label='jpeg', color='red')

    plt.xlabel('X: Bits (bpp)')
    plt.ylabel('Y: PSNR (db)')
    plt.legend()
    #plt.xlim(0.0,2.0)
    #plt.ylim(20.0,50.0)
    plt.title(filename)
    plt.savefig("PSNR_" + filename + ".pdf")
    plt.show()
