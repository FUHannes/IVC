# psnrRaw

**Simple tool for measuring PSNR and rate of raw video files**


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

For only measuring the PSNR between two raw video files:

`> ./psnrRaw (width) (height) (format) (orgVideo) (recVideo)`

where
  * **width** and **height** specify the width and height of the videos in luma samples.  
  * **format** specifies the chroma sampling format.  
     Valid values are **400** (luma only), **420** (4:2:0 chroma sampling),  
	 **422** (4:2:2 chroma sampling), and **444** (no chroma subsampling).
  * **orgVideo** is the file name of the original video file.
  * **recVideo** is the file name of the reconstructed video file.

For additionally measuring the bit rate:

`> ./psnrRaw (width) (height) (format) (orgVideo) (recVideo) (bitstream) (fps)`

where
  * **bitstream** is a compressed video file (for example, an HEVC file).
  * **fps** is the frame rate (in frames per second) of the videos.


