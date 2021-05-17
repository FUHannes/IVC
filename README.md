# ivc-ss21

image/video coding project (SS 2021)

## In Progress

Currently encoding and decoding only works for blocksizes bs for which:

**image_width % bs == 0** and **image_height % bs == 0**.

Note this when specifing the blocksize by your own.

## How to encode

Simply run

```
encode.py -bs[--blocksize] 8 -qp[--quantization-parameter] 8 -i[--input] exampleImage.pgm -b[--bitstream] myEncodedBinaryOutput.dat
```

See

```
encode.py -h[--help]
```

for further information.

## How to decode

Simply run

```
decode.py -b[--bitstrean] myEncodedBinaryOutput.dat -o[--output] myReconstructedImage.pgm
```

See

```
decode.py -h[--help]
```

for further information.

## How to test with psnr tool

To test for pgm 'Berlin.pgm' and compare with versions 1 and 2
Run

```
main.py -f Berlin -v 3 [-vs 1,2] [-bs]
```

use `-bs` to compute psnr curves for multiple block sizes [1,2,4,8,16,32]

See

```
main.py -h[--help]
```
