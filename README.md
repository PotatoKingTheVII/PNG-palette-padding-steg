## File usage
User inputs can be found at the top of each file, paddingDecoder prints the resulting padding bits of the chosen file while paddingEncoder inserts the payload and creates a new Output.png containing it.


## Brief technical overview
In the PNG palette mode each pixel can have a defined bit depth of 1,2,4 or 8 allowing up to 256 palette colours to be used. However, in all modes other than 8 there are scenarios where there are unused bits at the end of each horizontal row of the image. So the following can happen:
Where | is a pixel separator, # a byte separator, pn the pixel bits and un the undefined free bits

#|p1,p2,p3,p4|u1,u2,u3,u4|#

This happens with all depths 1,2 and 4 and can give up to 7 free bits per row in the extreme 1 bit depth case with 7 unused bits at the end of each row.

Only certain width and bit depth values actually allow this to happen though and changing the width by only 1 or 2 pixels can be the difference in an extra 6 bits or no bits available at all for a payload in the 1-bit depth case.

To actually use these free undefined bits we first gather all the IDAT chunks and extract the zlib pixel stream from them. Then work out which byte the free bits are in and change each individual bit to our payload from LSB to MSB as in: 1011free{3,2,1,0}. Once we've done that for however many rows that are needed we zlib deflate the altered pixel stream and add it back into the PNG then calculate the new lengths and CRC values.


## Dependancies

 - numpy
 - pillow
