# psnrImg

**Simple tool for measuring PSNR and rate of PGM or PPM images**


***  
## Building the Code: ##

### Linux/Make: ###

Simply use **make** in the main folder:

`> make`

or

`> make cc=(path to c++ compiler)`

or 

`> make debug`

or

`> make cc=(path to c++ compiler) debug`


### Windows/Visual Studio: ###

First create a Visual Studio solution by:

`> mkdir build\msvc`

`> cd build\msvc`

`> cmake ..\..`

Then open the solution and build with Visual Studio.



***  
## Using the tool: ##

For only measuring the PSNR between two images:

`> ./psnrImg (image1) (image2)`

where *image1* and *image2* are two image files in PGM or PPM format.  
Both images must have the same format and the same size.

For additionally measuring the bit rate:

`> ./psnrImg (image1) (image2) (bitstream)`

where *bitstream* is a compressed image file (for example, a JPEG file).


