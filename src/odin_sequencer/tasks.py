# Simple example task for the process queue.
import time

def add(x, y):
    time.sleep(2)
    return x + y

def dub(x):
    time.sleep(2)
    return 2 * x

import matplotlib.pyplot as plt
import os
import numpy as np
import h5py
import glob
import ffmpeg
import subprocess

def readFile(filename):
    with h5py.File(filename, 'r') as f: # open the file fn in Read mode
        a_group_key = list(f.keys())[0] # extract keys from the h5 file 
        np1 = np.array(f[a_group_key])
        return np1

def GenerateAverageADCFile(filepath):
    #generate y axis
    np1 = readFile(filepath) 
    shape = np.shape(np1)
    n1s = np.right_shift(np1, 6) # shift data down by 6 bits to get rid of fine bits

    # prepare a 3D array the correct size
    out = np.zeros([1, 9, shape[1]], np.uint16)
    
    for j in range(9):
        out[0, j, :] = np.mean(n1s[0, :, j::9], axis=1)

    #create h5 file for averages
    with h5py.File(filepath[:-3] + "_averages.h5", 'w') as h5f: # open file with this name in mode write
        h5f.create_dataset('dataset_1', data=out) # create the dataset with the name 'dataset_1'

def GenerateGraph(column, filepath):
    #generate y axis
    np1 = readFile(filepath)
    shape = np.shape(np1)
    x = [(0.213 + (i * 0.000375)) for i in range(shape[0])]

    plt.cla()
    for j in range(shape[1]):
        y = np1[:, j, column]
        plt.plot(x, y)
        plt.xlabel("Voltage")
        plt.ylabel("ADC Value")
        #plt.ylim(0,40) # use this when coarse only shifted down by 6-bits
        plt.ylim(0,40) # use this one when plotting both coarse and fine on the same graph
        plt.title("Sensor 2, ADC column %04d" %column)
        plt.savefig(os.path.dirname(filepath) + "/ADC_COLUMN_%04d.png" %column, dpi = 100)

def GenerateVideo(dirpath):
    out, err = (
        ffmpeg
        .input(dirpath + 'ADC_COLUMN_*.png', pattern_type='glob', framerate=24)
        .output(dirpath + 'adc_coarse_all.mp4')
        .run()
    )

def GenerateImage(filename, dirpath):
    n1 = readFile(dirpath + filename) 
    
    # for f in glob.glob(self.image_path + "frame_*.png"):
    #     os.remove(f)

    unique_filename = "frame_" + filename[:-3] + ".png"
    save_image(n1[0], dirpath + unique_filename)
    # save_image(n1[0], dirpath + "frame.png")

def save_image(data, filepath):
    sizes = np.shape(data)     
    fig = plt.figure()
    fig.set_size_inches(1. * sizes[1] / sizes[0], 1, forward = False)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    # ax.pcolor(data, vmax=2048, vmin=0, cmap='Greys')
    ax.imshow(data, cmap='gray')
    plt.savefig(filepath, dpi = sizes[1]) 
    #plt.savefig(filepath, dpi = 2000) 
    plt.close()

def CombineH5Files(dirpath):
    filelist= glob.glob(dirpath + '*averages.h5')
    filelist.sort()

    # open the first file to get size of image
    np1 = readFile(filelist[0])
    shape = np.shape(np1)

    #create an empty array based on shape and number of files
    combined = np.zeros((len(filelist), shape[1], shape[2]), dtype=np.uint16)
    combined[0] = np1

    # create new np array
    for i in range(1, len(filelist)):
        combined[i] = readFile(filelist[i])[0]

    # create new file for the combined data
    h5f = h5py.File(dirpath + "combined_histograms.h5", 'w')
    h5f.create_dataset('dataset_1', data=combined)
    h5f.close()
