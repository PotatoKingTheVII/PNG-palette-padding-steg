from PIL import Image
import binascii
import numpy
import zlib
import math

#User inputs:
###################################
TextIn = "Hello World! This is a test to check how the script works"
filename = "test.png"




#Bitwise functions to address invidual bits later
def set_bit(value, bit):
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)



#Convert payload text to binary string
###################################
TextList = ""
for i in range(0,len(TextIn)):
    Temp = str(numpy.base_repr(ord(TextIn[i]), base = 2, padding = 0).rjust(8,"0"))
    TextList += Temp


#Open image file and get some info
###################################
with open(filename,"rb") as fin:
    data=fin.read() 
    img = Image.open(fin)
    
width, height = img.size



#Type and sanity checking
###################################
paletteNumberIndex = data.find(bytes("PLTE","utf-8"))-1 #Check palette number before PLTE chunk
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


MaxLength = math.floor(height/(8/bitsAvailablePerLine)) #Max payload length for this setup
print("Palette bit depth:", paletteBitDepth, "\nMaximum payload length:", MaxLength, "chars\nBits per horizontal line:",bitsAvailablePerLine)

if(len(TextIn)>MaxLength):  #Input is too long, alert that excess is ignored
    print("Payload length",len(TextIn),"longer than maximum for carrier, ignoring excess message")




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




#Encode our payload into the free bits
###################################
payloadLength = math.ceil(len(TextList)/bitsAvailablePerLine) # i.e how many rows do we need for our payload
for i in range(0,height):   #For each row
    if(i > payloadLength):
        break   #Our payload has been set, just leave the rest untouched

    #Work out where the free bits we can change are:
    previousBytes = (i+1) + (math.ceil((width*paletteBitDepth)/8)*i)
    targetByteIndex = previousBytes+math.floor((width*paletteBitDepth)/8)
    targetByte = Decompressed[targetByteIndex]

    #Change each bit, one at a time of the available byte on the current line
    for j in range(0,bitsAvailablePerLine):
        currentPayloadIndex = (i*bitsAvailablePerLine) + j
        if((currentPayloadIndex)>=len(TextList)):
            break   #Our payload has been set, just leave the rest untouched

        #Change the byte value depending on our payload's bits
        if(TextList[currentPayloadIndex]=="1"):
            targetByte = set_bit(targetByte, j)
        else:
            targetByte = clear_bit(targetByte, j)
        
    Decompressed[targetByteIndex] = targetByte #Actually change the byte to our payload modified one



#Calculate new length and CRC of edited chunks and combine them
###################################
IENDChunk = bytearray(b"\00\x00\x00\x00\x49\x45\x4E\x44\xAE\x42\x60\x82")
EditCompressed = zlib.compress(Decompressed)
FinalData = bytearray(data[0:DatLocation+4] + EditCompressed)
IDatChunkActualLength = hex(len(EditCompressed))
IDatChunkActualLengthSizeFix = IDatChunkActualLength[2:len(IDatChunkActualLength)].rjust(8,"0") #Make sure it's always a 4-byte value

FinalData[(DatLocation - 4):DatLocation] = bytes.fromhex(IDatChunkActualLengthSizeFix)
DatLocation = FinalData.find(bytes("IDAT","utf-8"))
IDatCRC  = hex(binascii.crc32(FinalData[DatLocation:len(FinalData)]))



#Save final png to file
###################################
with open("Output.png", "wb") as fout:
    WriteData = FinalData + bytes.fromhex((IDatCRC[2:len(IDatCRC)]).rjust(8,"0")) + IENDChunk
    fout.write(WriteData)

print("Finished")
