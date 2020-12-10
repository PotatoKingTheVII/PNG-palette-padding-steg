from PIL import Image
import binascii
import numpy
import zlib
import math

#User inputs:
###################################
filename = "Output.png"




#Bitwise functions to address invidual bits later
def set_bit(value, bit):
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)



#Open image file and get some info
###################################
with open(filename,"rb") as fin:
    data=fin.read() 
    img = Image.open(fin)
    pixels = img.load()
    
width, height = img.size



#Type and sanity checking
###################################
paletteNumberIndex = data.find(bytes("PLTE","utf-8"))-1
if(paletteNumberIndex<0):
    print("Can't find PLTE chunk, likely not a palette image")
    quit()

paletteNumber = int(data[paletteNumberIndex]/3)  #To account for 1 sample colour = R,G,B bytes

if(paletteNumber == 8):  #Only bit depths of 1,4,8 are defined so 3 is treated like 4
    print("3 bit palette detected, treating as 4 bit as par the spec")
    paletteNumber = 16


paletteBitDepth = int(math.log(paletteNumber,2))
bitsAvailablePerLine = (8-((paletteBitDepth*width)%8))%8

if(bitsAvailablePerLine==0):
    print("Not a valid width with this bit-depth(",paletteBitDepth,") (8-((paletteBitDepth*width)%8))%8 must not equal 0")
    quit()


MaxLength = math.floor(height/(8/bitsAvailablePerLine))
print("Palette bit depth:", paletteBitDepth, "\nMaximum payload length:", MaxLength, "\nBits per height line:",bitsAvailablePerLine)



#Gather all IDAT chunks and extract zlib stream from them
###################################
DatLocation = data.find(bytes("IDAT","utf-8"))
CompressedZlibRaw = bytearray(data[DatLocation+4:len(data)])

while(CompressedZlibRaw.find(bytes("IDAT","utf-8")) != -1):
    DatLocationPlural = CompressedZlibRaw.find(bytes("IDAT","utf-8"))
    CurrentCRCChunk = CompressedZlibRaw[DatLocationPlural-4:DatLocationPlural]
    del CompressedZlibRaw[DatLocationPlural-8:DatLocationPlural+4]

CompressedZlib  = CompressedZlibRaw[0:len(CompressedZlibRaw)-4]
Decompressed = bytearray(zlib.decompress(CompressedZlib))



#Gather the payload bits
###################################
print("\nPayload bits:\n")
outputPayload = ""
for i in range(0,height):
    previousBytes = (i+1) + math.ceil(width/(8/paletteBitDepth))*i
    targetByteIndex = previousBytes+math.floor(width/(8/paletteBitDepth))
    targetByte = Decompressed[targetByteIndex]
    outputPayload+=(format(targetByte, '08b')[-bitsAvailablePerLine:])[::-1]
    

print(outputPayload)
print("\nFinished")
