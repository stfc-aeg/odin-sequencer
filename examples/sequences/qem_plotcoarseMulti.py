import numpy as np
import h5py
import sys
import cv2
import socket
import glob
import time


class PlotCourse:

    def __init__(self):

        self.fileroot = "/aeg_sw/work/projects/qem/data/"
        self.filename = "/aeg_sw/work/projects/qem/data/coarsesweepdata/combinedte7smithers.h5"

        self.np1 = []
        self.shape = []
        self.x = []
        self.img_array = []
    
    def setup(self):
        self.np1 = self.ReadFile()
        self.shape = self.GetShape()
        self.x = self.GenerateX()

    def GenerateX(self):
        x = []
        for i in range(self.shape[0]):
            x.append(0.213 + (i * 0.000375))
        return x

    def ReadFile(self):
        f=h5py.File(self.filename, 'r')       # open the file fn in Read mode
        a_group_key = list(f.keys())[0]     # extract keys from the h5 file 
        np1=np.array(f[a_group_key])
        f.close()
        return np1       # dataset_name is same as hdf5 object name

    def GetShape(self):
        return np.shape(self.np1)

    def GenerateVideo(self):
        filelist = glob.glob(self.fileroot + "*.png")
        filelist.sort()
        for filename in filelist:
            img = cv2.imread(filename)
            height, width, layers = img.shape
            size = (width,height)
            self.img_array.append(img)

        out = cv2.VideoWriter(self.fileroot + "coarsesweep" + 'adc_coarse_all.avi',cv2.VideoWriter_fourcc(*'DIVX'), 15, size)
    
        for i in range(len(self.img_array)):
            out.write(self.img_array[i])
        out.release()
