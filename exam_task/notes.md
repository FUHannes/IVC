## my task
- IC2
- Coding of Color Images
- Extend our codec for PGM images (gray) to a codec for PPM images (given in RGB)
- Compare two different versions:
    - Independent coding of R, G, and B color components
    - Color transform to YCbCr (or YCoCg), coding of these components (with or without chroma subsampling), reconstruction of R, G, and B after decoding and output as PPM image
- Compare both variants with JPEG (data available in git)

## psnr 
- called psnrImg

## PPM
- switch on header P5 = grey ; P6 = PPM/Color
- jedes pixel 3 bytes (aka R G B)
    - die 3 bilder bekommen wäre ungefähr data.reshape(breite,höhe,3).swapaxes(0,2)