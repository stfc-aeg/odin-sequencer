import os
import glob
import numpy as np
import h5py

def averageADCValues(dirpath = "{ DIR PATH }"):
    queue = get_context('process_writer')
    path_list = glob.glob(dirpath + '*.h5')
    queue.group('GenerateAverageADCFile', True, path_list)

def generateImages(dirpath = "{ DIR PATH }"):
    queue = get_context('process_writer')
    queue.group('GenerateImage', True, [filename for filename in os.listdir(dirpath) if filename.endswith('.h5') and '_average' not in filename and 'combine' not in filename], dirpath)

def CombineH5Files(dirpath = "{ DIR PATH }"):
    queue = get_context('process_writer')
    queue.run('CombineH5Files', True, dirpath)

def plotcoarseMulti(filepath="{ DIR PATH }/combined_histograms.h5"):
    f = h5py.File(filepath, 'r')       # open the file fn in Read mode
    a_group_key = list(f.keys())[0]     # extract keys from the h5 file 
    np1 = np.array(f[a_group_key])
    f.close()
    shape = np.shape(np1)
    queue = get_context('process_writer')
    queue.group('GenerateGraph', True, range(0, shape[2]), filepath)

def GenerateVideo(dirpath="{ DIR PATH }"):
    queue = get_context('process_writer')
    queue.run('GenerateVideo', True, dirpath)
