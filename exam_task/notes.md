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

## Y'CbCr
conversion as of https://stackoverflow.com/a/34913974/15289577
```python
    def rgb2ycbcr(im):
        xform = np.array([[.299, .587, .114], [-.1687, -.3313, .5], [.5, -.4187, -.0813]])
        ycbcr = im.dot(xform.T)
        ycbcr[:,:,[1,2]] += 128
        return np.uint8(ycbcr)

    def ycbcr2rgb(im):
        xform = np.array([[1, 0, 1.402], [1, -0.34414, -.71414], [1, 1.772, 0]])
        rgb = im.astype(np.float)
        rgb[:,:,[1,2]] -= 128
        rgb = rgb.dot(xform.T)
        np.putmask(rgb, rgb > 255, 255)
        np.putmask(rgb, rgb < 0, 0)
        return np.uint8(rgb)
```
- schneller mit YCoCg
```python
    def rgb2ycocg(im):
        xform = np.array([[1, 2, 1], [-1, 2, -1], [2, 0, -2]])
        ycocg = im.dot(xform.T)/4
        ycocg[:,:,[1,2]] += 128
        return np.uint8(yobgr)

    def ycocg2rgb(im):
        xform = np.array([[1, -1, 1], [1, 1, 0], [1, -1, -1]])
        rgb = im.astype(np.float)
        rgb[:,:,[1,2]] -= 128
        rgb = rgb.dot(xform.T)
        np.putmask(rgb, rgb > 255, 255)
        np.putmask(rgb, rgb < 0, 0)
        return np.uint8(rgb)
```

### sub-sampling
new parameter (4:x:y) (wahrscheinlich hab ich width und height / x und y bissl vertauscht)
- :4:4 no subs 
    - `newdata=data`
- :2:2 skip every second horizontal pixel
    - `newdata=data[::2][:]`
- :1:1 skip 3 out of 4 horizontal pixel (take every fourths)
    - `newdata=data[::4][:]`
- :2:0 Durchschnitt (oder iwie) 4(2*2) pixel Gruppe
    - `newdata=data[::2][::2]` (samplen statt durchschnitt) `newdata=np.mean(np.swapaxes(data.reshape([width/2,2,height/2,2]),1,2),2,3)` (durschnitt wie in jpeg)