import os
import sys
import lzma
import shutil
import struct
import platform

sys.path.append('./System')

from DataBase import Version
from BytesWorker import *
from PIL import Image, ImageDraw, ImageChops


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

            if subType == 0:
                pixelSize = 4
            elif subType == 2 or subType == 4 or subType == 6:
                pixelSize = 2
            elif subType == 10:
                pixelSize = 1
            else:
                raise Exception("Unknown pixel type: " + str(subType))

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

            img.putdata(pixels)

            assetInt = 0

            checkArray = [
                ("t", 0, -1, 5),
                ("tl", -1, -1, 6),
                ("l", -1, 0, 7),
                ("bl", -1, 1, 0),
                ("b", 0, 1, 1),
                ("br", 1, 1, 2),
                ("r", 1, 0, 3),
                ("tr", 1, -1, 4),
                ]
            checkArray.extend(checkArray)

            for y in range(height):
                for x in range(width):

                    if pixels[x + y * width][3] != 0:
                        current = 0
                        slicedPixels = [(x, y)]
                        furthestPoints = [y, x, x, y]
                        lastPixelDirection = 0

                        startingPixel = (x, y)

                        while True:
                            if len(slicedPixels) == current:
                                break
                            currentPixel = slicedPixels[current]

                            for r in range(8):
                                if pixelChecker(pixels, currentPixel, width, height, checkArray[lastPixelDirection + r][0], 1):
                                    if (currentPixel[0] + checkArray[lastPixelDirection + r][1], currentPixel[1] + checkArray[lastPixelDirection + r][2]) == startingPixel:
                                        break
                                    sp, furthestPoints = pixelCalculator(pixels, currentPixel, furthestPoints, width, height, checkArray[lastPixelDirection + r][1], checkArray[lastPixelDirection + r][2])
                                    slicedPixels.append(sp)
                                    lastPixelDirection = checkArray[lastPixelDirection + r][3]
                                    break

                            current += 1

                        sWidth = furthestPoints[2] - furthestPoints[1] + 1
                        sHeight = furthestPoints[3] - furthestPoints[0] + 1
                        imgData = [0 for x in range(sWidth * sHeight)]
                        for pixel in slicedPixels:
                            imgData[pixel[0] - furthestPoints[1] + (pixel[1] - furthestPoints[0]) * sWidth] = 1

                        unmasked = Image.new("RGBA", (width, height))
                        unmasked.putdata(pixels)
                        unmasked = unmasked.crop((furthestPoints[1], furthestPoints[0], furthestPoints[2] + 1, furthestPoints[3] + 1))

                        maskOutline = Image.new("1", (sWidth, sHeight))
                        maskOutline.putdata(imgData)
                        maskOutline.save(folder_export + CurrentSubPath + str(assetInt) + "part2.png")

                        maskFill = Image.new("1", (sWidth, sHeight))
                        maskFill.putdata(imgData)

                        savedFills = Image.new("1", (sWidth, sHeight))

                        mask = Image.new("1", (sWidth, sHeight))

                        for h in range(sHeight):
                            for w in range(sWidth):
                                if pixels[furthestPoints[1] + w + width * (furthestPoints[0] + h)][3] > 0 and maskOutline.load()[w, h] == 0 and savedFills.load()[w, h] == 0:
                                    
                                    maskFill.putdata(imgData)
                                    maskFill = ImageChops.add(maskFill, savedFills)

                                    ImageDraw.floodfill(maskFill, xy=(w, h), value=1)

                                    savedFills = ImageChops.add(maskFill, savedFills)
                                    maskFill = ImageChops.subtract(maskFill, maskOutline)
                                    maskFill.save(folder_export + CurrentSubPath + str(assetInt) + "part5.png")
                                    mask = maskFill.copy()

                                    maskOutlineData = maskOutline.load()

                                    outlineCountTotal = 0
                                    outlineCount = 0
                                    outlineCountPrevious = -1

                                    for y1 in range(sHeight):
                                        for x1 in range(sWidth):
                                            if maskOutlineData[x1, y1] == 1:
                                                outlineCountTotal += 1

                                    while outlineCount != outlineCountTotal and outlineCount != outlineCountPrevious:
                                        outlineCountPrevious = outlineCount
                                        for y2 in range(sHeight):
                                            for x2 in range(sWidth):
                                                if maskOutlineData[x2, y2] == 1:
                                                    if imageCheckerOR(mask, (x2, y2), checkArray, sWidth, sHeight) and maskOutlineData[x2, y2] == 1 and mask.load()[x2, y2] == 0:
                                                        mask.putpixel((x2, y2), 1)
                                                        outlineCount += 1

                        filledImgData = mask.load()
                        mask.save(folder_export + CurrentSubPath + str(assetInt) + "part4.png")

                        slicedImg = Image.new("RGBA", (sWidth, sHeight))
                        slicedImg = Image.composite(unmasked, slicedImg, mask)
                        slicedImg.save(folder_export + CurrentSubPath + str(assetInt) + "part.png")

                        for sy in range(sHeight):
                            for sx in range(sWidth):
                                if filledImgData[sx, sy] == 1:
                                    pixels[furthestPoints[1] + sx + width * (furthestPoints[0] + sy)] = (0, 0, 0, 0)

                        debug = Image.new("RGBA", (width, height))
                        debug.putdata(pixels)
                        debug.save(folder_export + CurrentSubPath + str(assetInt) + "part3.png")

                        assetInt += 1

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
    return(
        (
            (currentPixel[0] + xSide, currentPixel[1] + ySide),
            [
                currentPixel[1] + ySide if currentPixel[1] + ySide < furthestPoints[0] and ySide < 0 else furthestPoints[0],
                currentPixel[0] + xSide if currentPixel[0] + xSide < furthestPoints[1] and xSide < 0 else furthestPoints[1],
                currentPixel[0] + xSide if currentPixel[0] + xSide > furthestPoints[2] and xSide > 0 else furthestPoints[2],
                currentPixel[1] + ySide if currentPixel[1] + ySide > furthestPoints[3] and ySide > 0 else furthestPoints[3]
            ]
        )
        )


def pixelChecker(i, c, w, h, s, d):
    a = {
        "t": (-1, 0, 0, -1),
        "tr": (w-1, 0, 1, -1),
        "r": (w-1, -1, 1, 0),
        "br": (w-1, h-1, 1, 1),
        "b": (-1, h-1, 0, 1),
        "bl": (0, h-1, -1, 1),
        "l": (0, -1, -1, 0),
        "tl": (0, 0, -1, -1)
    }
    b = a[s]
    if d == 1:
        return c[0] != b[0] and c[1] != b[1] and i[c[0] + b[2] + w * (c[1] + b[3])][0] != 0
    elif d == 2:
        return c[0] != b[0] and c[1] != b[1] and i[c[0] + b[2], c[1] + b[3]] != 0
    return False


def imageCheckerOR(image, currentPixel, checkArray, width, height):
    final = False
    for i in range(8):
        if pixelChecker(image.load(), currentPixel, width, height, checkArray[i][0], 2):
            final = True
    return final


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
