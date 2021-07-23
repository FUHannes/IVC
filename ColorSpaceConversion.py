import numpy as np

# "inspired by" https://stackoverflow.com/a/34913974/15289577

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

def rgb2ycocg(im):
    xform = np.array([[1, 2, 1], [-1, 2, -1], [2, 0, -2]])
    ycocg = im.dot(xform.T)/4
    ycocg[:,:,[1,2]] += 128
    return np.uint8(ycocg)

def ycocg2rgb(im):
    xform = np.array([[1, -1, 1], [1, 1, 0], [1, -1, -1]])
    rgb = im.astype(np.float)
    rgb[:,:,[1,2]] -= 128
    rgb = rgb.dot(xform.T)
    np.putmask(rgb, rgb > 255, 255)
    np.putmask(rgb, rgb < 0, 0)
    return np.uint8(rgb)