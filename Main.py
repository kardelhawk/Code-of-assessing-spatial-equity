import argparse
import math

import numpy
from PIL import Image
import numpy
import os

from skimage.metrics import structural_similarity
import xlsxwriter as xw


parser = argparse.ArgumentParser(description='Assess Spatial Equity')
parser.add_argument('--img1', default="D:\\Assess Spatial Equity\\supply map.jpg", type=str, help='image file5')
parser.add_argument('--img2', default="D:\\Assess Spatial Equity\\demand map.jpg", type=str, help='image file6')

# The window of dpi is depend on the spatial scale needed 
parser.add_argument('--WIN_X', default=80, type=int, help='length of dpi')
parser.add_argument('--WIN_Y', default=80, type=int, help='width of dpi')

parser.add_argument('--T_SSIM', default=0.8, type=float, help='predefined threshold')


def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)


def xw_to_excel(xlsfile, data):  # record similarity results
    workbook = xw.Workbook(xlsfile) 
    sheet1 = workbook.add_worksheet("sheet1")  

    for i in range(len(data)):
        row = 'A' + str(i+1)
        sheet1.write_row(row, data[i])
    workbook.close() 


def compute_region_ssim(gray1, gray2, WIN_X, WIN_Y):
    width = min(gray1.width, gray2.width)
    height = min(gray1.height, gray2.height)
    num_x = math.floor(width / WIN_X)
    num_y = math.floor(height / WIN_Y)
    if num_x == 0 or num_y == 0:
        print("error: the width/height of defined window is less than or equal to that of images")
        num_x = 1
        num_y = 1
        WIN_X = width
        WIN_Y = height

    ssim = [[0] * num_x for _ in range(num_y)]
    for i in range(num_x):
        for j in range(num_y):
            clip1 = gray1.crop((i * WIN_X, j * WIN_Y, (i + 1) * WIN_X, (j + 1) * WIN_Y))
            clip2 = gray2.crop((i * WIN_X, j * WIN_Y, (i + 1) * WIN_X, (j + 1) * WIN_Y))            
            np_clip1 = numpy.array(clip1)
            np_clip2 = numpy.array(clip2)
            np_clip1[np_clip1 == 255] = 0
            np_clip2[np_clip2 == 255] = 0
            sum1 = numpy.sum(numpy.sum(np_clip1))
            sum2 = numpy.sum(numpy.sum(np_clip2))
            
            # no map information
            if sum1 == 0 and sum2 == 0:
                ssim[j][i] = None
                continue

            np_clip1 = numpy.array(clip1)
            np_clip2 = numpy.array(clip2)
            ssim[j][i] = structural_similarity(np_clip1, np_clip2)

    return ssim


def colored_region(gray1, gray2, WIN_X, WIN_Y, ssim, T_SSIM):

    #Calculate mean average (overall spatial equity)
    ssim_array = numpy.array(ssim)
    ssim_float = ssim_array.astype(float)   
    masked_array = numpy.ma.array(ssim_float, mask=numpy.isnan(ssim_float))  
    average = masked_array.mean()
    var=masked_array.var()
    MAX = numpy.nanpercentile(ssim_float, 100)
    MIN = numpy.nanpercentile(ssim_float, 0)

    width = min(gray1.width, gray2.width)
    height = min(gray1.height, gray2.height)
    num_x = math.floor(width / WIN_X)
    num_y = math.floor(height / WIN_Y)
    if num_x == 0 or num_y == 0:
        print("error: the width/height of defined window is less than or equal to that of images")
        num_x = 1
        num_y = 1
        WIN_X = width
        WIN_Y = height
    
    # Grey map
    count_one=0
    count_grey=0
    res = numpy.full((3, gray1.height, gray1.width), 255, dtype=numpy.uint8)
    
    for i in range(num_x):
        for j in range(num_y):
            # areas with nothing or without exceeding the threshold
            if ssim[j][i] == None:
                res[0, j * WIN_Y:(j + 1) * WIN_Y, i * WIN_X:(i + 1) * WIN_X] = 255
                res[1, j * WIN_Y:(j + 1) * WIN_Y, i * WIN_X:(i + 1) * WIN_X] = 255
                res[2, j * WIN_Y:(j + 1) * WIN_Y, i * WIN_X:(i + 1) * WIN_X] = 255
                continue
            
            if ssim[j][i] >= T_SSIM:
                res[0, j * WIN_Y:(j + 1) * WIN_Y, i * WIN_X:(i + 1) * WIN_X] =205
                res[1, j * WIN_Y:(j + 1) * WIN_Y, i * WIN_X:(i + 1) * WIN_X] =205
                res[2, j * WIN_Y:(j + 1) * WIN_Y, i * WIN_X:(i + 1) * WIN_X] =205
                count_one += 1
            
            else:    
                # considerable areas
                res[0, j * WIN_Y:(j + 1) * WIN_Y, i * WIN_X:(i + 1) * WIN_X] =int(205*(ssim[j][i]-MIN)/(MAX-MIN))
                res[1, j * WIN_Y:(j + 1) * WIN_Y, i * WIN_X:(i + 1) * WIN_X] =int(205*(ssim[j][i]-MIN)/(MAX-MIN))
                res[2, j * WIN_Y:(j + 1) * WIN_Y, i * WIN_X:(i + 1) * WIN_X] =int(205*(ssim[j][i]-MIN)/(MAX-MIN))
                count_grey += 1
                

    count_all = count_one + count_grey
    print("ratio of consider areas：", count_grey / count_all)    
    print("=====================================")

    return res.swapaxes(0, 1).swapaxes(1, 2)


if __name__ == '__main__':
    opt = parser.parse_args()

    pos1 = opt.img1.rfind("\\")
    outdir = opt.img1[0:pos1 + 1] + "result\\"
    mkdir(outdir)
    print("Result save path：" + outdir)

    pos2 = opt.img1.rfind(".")
    img1_name = opt.img1[pos1 + 1:pos2]

    pos1 = opt.img2.rfind("\\")
    pos2 = opt.img2.rfind(".")
    img2_name = opt.img2[pos1 + 1:pos2]

    img1 = Image.open(opt.img1)
    img2 = Image.open(opt.img2)

    print("Grey map recording")
    gray1 = img1.convert("L")
    gray2 = img2.convert("L")
    # gray2.show()
    gray1.save(outdir + img1_name + "_gray.jpg")
    gray2.save(outdir + img2_name + "_gray.jpg")

    print("Evaluate map similarity")
    ssim = compute_region_ssim(gray1, gray2, opt.WIN_X, opt.WIN_Y)
    xlsfile = outdir + img1_name + "_" + img2_name + ".xlsx"
    xw_to_excel(xlsfile, ssim)

    print("Assess overall spatial equity")
    sum_ssim = 0
    count = 0
    for j in range(ssim.__len__()):
        for i in range(ssim[0].__len__()):
            if ssim[j][i] != None:
                sum_ssim += ssim[j][i]
                count += 1
    ave_ssim = sum_ssim / count
    print("overall spatial equity = ", ave_ssim)

    print("Map similarity")
    res1 = colored_region(gray1, gray2,
                          opt.WIN_X, opt.WIN_Y,
                          ssim, opt.T_SSIM)

    pil_res1 = Image.fromarray(res1)
    pil_res1.save(outdir + "considerable areas.jpg")


