# Simple example task for the process queue.
import time

def add(x, y):
    time.sleep(2)
    return x + y

import matplotlib.pyplot as plt

def GenerateGraph(self, column, shape, np1, x, filename):
        #generate y axis
        plt.cla()
        print(column)
        for j in range(shape[1]):
            y = []
            for i in range(shape[0]):
                y.append(np1[i][j][column])
            plt.plot(x, y)
            plt.xlabel("Voltage")
            plt.ylabel("ADC Value")
            #plt.ylim(0,40) # use this when coarse only shifted down by 6-bits
            plt.ylim(0,40) # use this one when plotting both coarse and fine on the same graph
            plt.title("Sensor 2, ADC column %04d" %column)
            plt.savefig(filename + "ADC_COLUMN_%04d.png" %column, dpi = 100)