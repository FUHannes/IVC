#!/bin/bash


### PART 1

    IMG_NAME="Berlin"

    mkdir tmp

    for i in {1..100}
    do
        #encode
        convert pgm/${IMG_NAME}.pgm -quality ${i} tmp/${IMG_NAME}${i}.jpg

        #decode
        convert tmp/${IMG_NAME}${i}.jpg tmp/${IMG_NAME}${i}_rec.pgm

        #get PSNR
        ../tools/psnr-images/bin/GNU-9.3.0/psnrImg pgm/${IMG_NAME}.pgm tmp/${IMG_NAME}${i}_rec.pgm tmp/${IMG_NAME}${i}.jpg >> psnr/PSNR_${IMG_NAME}
    done

    rm -rf tmp

