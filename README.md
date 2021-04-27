# ivc-ss21

image/video coding project (SS 2021)

## Deprecated
The file main.py is deprecated and will be removed, but is still great for testing.

## In Progress

Currently encoding and decoding only works for blocksizes bs for which:

**image_width % bs == 0** and **image_height % bs == 0**.

Note this when specifing the blocksize by your own.

## How to encode
Simply run 
```
encode.py -i[--input] exampleImage.pgm -o[--output] myEncodedBinaryOutput.dat
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
