import os
import sys
import lzma
import shutil
import struct
import platform

sys.path.append('./System')

from DataBase import Version
from PIL import Image


folder = "./In-Compressed-SC/"
folder_export = "./Out-Decompressed-SC/"
SystemName = platform.system()
sys.stdout.write('\x1b]2;XCoder | Version: ' + Version + ' | Developer: MasterDevX\x07')

if SystemName == 'Windows':

    def Clear():

        os.system('cls')

else:

    def Clear():

        os.system('clear')


def GameSelect():

    global Game

    print('1 - Brawl Stars')
    print('2 - Clash Royale')
    Game = input('Select Target Game: ')

    if Game != '1' and Game != '2':

        Clear()
        GameSelect()


Clear()
GameSelect()
Clear()


def _(message):
    print("[INFO] " + message)


def convert_pixel(pixel, type):
    if type == 0:  # RGB8888
        return struct.unpack('4B', pixel)
    elif type == 2:  # RGB4444
        pixel, = struct.unpack('<H', pixel)
        return (rgb4split(pixel, 0), rgb4split(pixel, 1), rgb4split(pixel, 2), rgb4split(pixel, 3))
    elif type == 4:  # RGB565
        pixel, = struct.unpack("<H", pixel)
        return (((pixel >> 11) & 0x1F) << 3, ((pixel >> 5) & 0x3F) << 2, (pixel & 0x1F) << 3)
    elif type == 6:  # LA88
        pixel, = struct.unpack("<H", pixel)
        return ((pixel >> 8), (pixel >> 8), (pixel >> 8), (pixel & 0xFF))
    elif type == 10:  # L8
        pixel, = struct.unpack("<B", pixel)
        return (pixel, pixel, pixel)
    else:
        raise Exception("Unknown pixel type: " + type)


def rgb4split(pixel, position):
    return (((pixel >> 12 - 4 * position) & 0xF) << 4) + ((pixel >> 12 - 4 * position) & 0xF)


def decompileSC(fileName):
    baseName = os.path.splitext(os.path.basename(fileName))[0]

    with open(fileName, "rb") as fh:
        data = fh.read()

        if data[0] != 93:
            data = data[26:]

        xbytes = b'\xff' * 8
        ybytes = b'\x00' * 4

        if Game == '1':
            data = data[0:5] + xbytes + data[9:]
        if Game == '2':
            data = data[0:9] + ybytes + data[9:]
        decompressed = lzma.LZMADecompressor().decompress(data)

        i = 0
        picCount = 0

        _("Collecting information...")

        while len(decompressed[i:]) > 5:
            fileType = decompressed[i]
            fileSize, = struct.unpack("<I", decompressed[i + 1:i + 5])
            subType = decompressed[i + 5]
            width, = struct.unpack("<H", decompressed[i + 6:i + 8])
            height, = struct.unpack("<H", decompressed[i + 8:i + 10])

            i += 10

            d = open("debug", "w")
            d.write(decompressed.hex())
            d.close()

            if subType == 0:
                pixelSize = 4
            elif subType == 2 or subType == 4 or subType == 6:
                pixelSize = 2
            elif subType == 10:
                pixelSize = 1
            else:
                raise Exception("Unknown pixel type: " + subType)

            xfilename = fileName[::-1]
            xfilename = xfilename[:xfilename.index('/')]
            xfilename = xfilename[::-1]

            _("About: FileName: %s, FileType: %s, FileSize: %s, SubType: %s, Width: %s, Height: %s" % (xfilename, fileType, fileSize, subType, width, height))
            _("Creating picture...")

            img = Image.new("RGBA", (width, height))

            pixels = []

            for y in range(height):
                for x in range(width):
                    pixels.append(convert_pixel(decompressed[i:i + pixelSize], subType))
                    i += pixelSize

            Asset = 0
            usedPixels = []
            for y in range(height):
                for x in range(width):
                    # print(f"x{x} y{y}")
                    if pixels[x + y * width][3] != 0 and (x, y) not in usedPixels:
                        Current = 0
                        slicedPixels = [(x, y, pixels[x + y * width])]
                        checkedPixels = []
                        furthestPoints = [y, x, x, y]
                        while True:
                            if len(slicedPixels) == Current:
                                break
                            currentPixel = slicedPixels[Current]
                            # print(f"current {currentPixel}")
                            # print(pixelChecker(pixels, currentPixel, checkedPixels, width, height, "t"))
                            # print(pixelChecker(pixels, currentPixel, checkedPixels, width, height, "tr"))
                            # print(pixelChecker(pixels, currentPixel, checkedPixels, width, height, "r"))
                            # print(pixelChecker(pixels, currentPixel, checkedPixels, width, height, "br"))
                            # print(pixelChecker(pixels, currentPixel, checkedPixels, width, height, "b"))
                            # print(pixelChecker(pixels, currentPixel, checkedPixels, width, height, "bl"))
                            # print(pixelChecker(pixels, currentPixel, checkedPixels, width, height, "l"))
                            # print(pixelChecker(pixels, currentPixel, checkedPixels, width, height, "tl"))
                            # print("")
                            if pixelChecker(pixels, currentPixel, checkedPixels, width, height, "t"):
                                sp, cp, up, furthestPoints = pixelCalculator(pixels, currentPixel, furthestPoints, width, height, 0, -1)
                                slicedPixels.append(sp)
                                checkedPixels.append(cp)
                                usedPixels.append(up)
                            if pixelChecker(pixels, currentPixel, checkedPixels, width, height, "tr"):
                                sp, cp, up, furthestPoints = pixelCalculator(pixels, currentPixel, furthestPoints, width, height, 1, -1)
                                slicedPixels.append(sp)
                                checkedPixels.append(cp)
                                usedPixels.append(up)
                            if pixelChecker(pixels, currentPixel, checkedPixels, width, height, "r"):
                                sp, cp, up, furthestPoints = pixelCalculator(pixels, currentPixel, furthestPoints, width, height, 1, 0)
                                slicedPixels.append(sp)
                                checkedPixels.append(cp)
                                usedPixels.append(up)
                            if pixelChecker(pixels, currentPixel, checkedPixels, width, height, "br"):
                                sp, cp, up, furthestPoints = pixelCalculator(pixels, currentPixel, furthestPoints, width, height, 1, 1)
                                slicedPixels.append(sp)
                                checkedPixels.append(cp)
                                usedPixels.append(up)
                            if pixelChecker(pixels, currentPixel, checkedPixels, width, height, "b"):
                                sp, cp, up, furthestPoints = pixelCalculator(pixels, currentPixel, furthestPoints, width, height, 0, 1)
                                slicedPixels.append(sp)
                                checkedPixels.append(cp)
                                usedPixels.append(up)
                            if pixelChecker(pixels, currentPixel, checkedPixels, width, height, "bl"):
                                sp, cp, up, furthestPoints = pixelCalculator(pixels, currentPixel, furthestPoints, width, height, -1, 1)
                                slicedPixels.append(sp)
                                checkedPixels.append(cp)
                                usedPixels.append(up)
                            if pixelChecker(pixels, currentPixel, checkedPixels, width, height, "l"):
                                sp, cp, up, furthestPoints = pixelCalculator(pixels, currentPixel, furthestPoints, width, height, -1, 0)
                                slicedPixels.append(sp)
                                checkedPixels.append(cp)
                                usedPixels.append(up)
                            if pixelChecker(pixels, currentPixel, checkedPixels, width, height, "tl"):
                                sp, cp, up, furthestPoints = pixelCalculator(pixels, currentPixel, furthestPoints, width, height, -1, -1)
                                slicedPixels.append(sp)
                                checkedPixels.append(cp)
                                usedPixels.append(up)
                            Current += 1
                        # print(slicedPixels)
                        sWidth = furthestPoints[2] - furthestPoints[1] + 1
                        sHeight = furthestPoints[3] - furthestPoints[0] + 1
                        imgData = [(0, 0, 0, 0) for x in range(sWidth * sHeight)]
                        for pixel in slicedPixels:
                            imgData[pixel[0] - furthestPoints[1] + (pixel[1] - furthestPoints[0]) * sWidth] = pixel[2]
                        slicedImg = Image.new("RGBA", (sWidth, sHeight))
                        slicedImg.putdata(imgData)
                        slicedImg.save(folder_export + CurrentSubPath + str(Asset) + "part.png")
                        Asset += 1

            img.putdata(pixels)

            if fileType == 28 or fileType == 27:
                imgl = img.load()
                iSrcPix = 0
                for l in range(int(height / 32)):
                    for k in range(int(width / 32)):
                        for j in range(32):
                            for h in range(32):
                                imgl[h + (k * 32), j + (l * 32)] = pixels[iSrcPix]
                                iSrcPix += 1
                    for j in range(32):
                        for h in range(width % 32):
                            imgl[h + (width - (width % 32)), j + (l * 32)] = pixels[iSrcPix]
                            iSrcPix += 1

                for k in range(int(width / 32)):
                    for j in range(int(height % 32)):
                        for h in range(32):
                            imgl[h + (k * 32), j + (height - (height % 32))] = pixels[iSrcPix]
                            iSrcPix += 1

                for j in range(height % 32):
                    for h in range(width % 32):
                        imgl[h + (width - (width % 32)), j + (height - (height % 32))] = pixels[iSrcPix]
                        iSrcPix += 1

            fullname = baseName + ('_' * picCount)

            _("Saving as png...")
            img.save(folder_export + CurrentSubPath + fullname + ".png", "PNG")
            picCount += 1
            _("Saving completed" + "\n")


def pixelCalculator(pixels, currentPixel, furthestPoints, width, height, xSide, ySide):
    return(((currentPixel[0] + xSide, currentPixel[1] + ySide, pixels[currentPixel[0] + xSide + width * (currentPixel[1] + ySide)]),
        (currentPixel[0] + xSide, currentPixel[1] + ySide),
        (currentPixel[0] + xSide, currentPixel[1] + ySide),
        [currentPixel[1] + ySide if currentPixel[1] + ySide < furthestPoints[0] and ySide < 0 else furthestPoints[0],
        currentPixel[0] + xSide if currentPixel[0] + xSide < furthestPoints[1] and xSide < 0 else furthestPoints[1],
        currentPixel[0] + xSide if currentPixel[0] + xSide > furthestPoints[2] and xSide > 0 else furthestPoints[2],
        currentPixel[1] + ySide if currentPixel[1] + ySide > furthestPoints[3] and ySide > 0 else furthestPoints[3]]))


def pixelChecker(pixels, currentPixel, checkedPixels, width, height, side):
    if side == "t":
        return(currentPixel[1] != 0 and pixels[currentPixel[0] + width * (currentPixel[1] - 1)][3] != 0 and (currentPixel[0], currentPixel[1] - 1) not in checkedPixels)
    elif side == "tr":
        return(currentPixel[1] != 0 and currentPixel[0] != width - 1 and pixels[currentPixel[0] + 1 + width * (currentPixel[1] - 1)][3] != 0 and (currentPixel[0] + 1, currentPixel[1] - 1) not in checkedPixels)
    if side == "r":
        return(currentPixel[0] != width - 1 and pixels[currentPixel[0] + 1 + width * currentPixel[1]][3] != 0 and (currentPixel[0] + 1, currentPixel[1]) not in checkedPixels)
    elif side == "br":
        return(currentPixel[1] != height - 1 and currentPixel[0] != width - 1 and pixels[currentPixel[0] + 1 + width * (currentPixel[1] + 1)][3] != 0 and (currentPixel[0] + 1, currentPixel[1] + 1) not in checkedPixels)
    if side == "b":
        return(currentPixel[1] != height - 1 and pixels[currentPixel[0] + width * (currentPixel[1] + 1)][3] != 0 and (currentPixel[0], currentPixel[1] + 1) not in checkedPixels)
    elif side == "bl":
        return(currentPixel[1] != height - 1 and currentPixel[0] != 0 and pixels[currentPixel[0] - 1 + width * (currentPixel[1] + 1)][3] != 0 and (currentPixel[0] - 1, currentPixel[1] + 1) not in checkedPixels)
    if side == "l":
        return(currentPixel[0] != 0 and pixels[currentPixel[0] - 1 + width * currentPixel[1]][3] != 0 and (currentPixel[0] - 1, currentPixel[1]) not in checkedPixels)
    elif side == "tl":
        return(currentPixel[1] != 0 and currentPixel[0] != 0 and pixels[currentPixel[0] - 1 + width * (currentPixel[1] - 1)][3] != 0 and (currentPixel[0] - 1, currentPixel[1] - 1) not in checkedPixels)
    else:
        return False


files = os.listdir(folder)
for file in files:
    if file.endswith("_tex.sc"):

        global CurrentSubPath

        ScNameList = []
        for i in file:
            ScNameList.append(i)
        DotIndex = ScNameList.index('.')
        CurrentSubPath = ''.join(ScNameList[:DotIndex]) + '/'
        if os.path.isdir(folder_export + CurrentSubPath) is True:
            shutil.rmtree(folder_export + CurrentSubPath)
        os.mkdir(folder_export + CurrentSubPath)
        decompileSC(folder + file)
