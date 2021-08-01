from iperflexer.iperfparser import IperfParser
from iperflexer.sumparser import SumParser, HumanExpression
from iperflexer.unitconverter import UnitConverter
from iperflexer.unitconverter import UnitNames as d_names
from iperflexer.unitconverter import BinaryUnitNames as b_names
from iperflexer.unitconverter import BinaryUnitconverter
import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

class Plot_bw_data(object):

    def __init__(self):
        pass

    def parse_txt(self, lines):
        client_sums = SumParser(units='bits')
        bw_array = []  # Mbits
        retr = []  # number
        wsize = []  # Kbytes


        for line in lines[3:-4]:
            #print(line)
            #extract bandwidth from line
            client_sums(line)

            values = re.findall("\d*\.*\d+", line)
            #print(values)

            # extract retr from line
            retr.append(int(values[-2]))

            #extact wsize from line
            w_value = values[-1]
            wsize.append(float(w_value))

        #print("bandwidth")
        for bw in client_sums.bandwidths:
            #print(bw)
            bw_array.append(float(bw) / 1000000)

        return bw_array, retr, wsize



    def parse_download_txt(self, lines):
        client_sums = SumParser(units='bits')
        bw_array = []  # Mbits

        for line in lines[3:-4]:
            # extract bandwidth from line
            client_sums(line)

        for bw in client_sums.bandwidths:
            bw_array.append(float(bw) / 1000000)
        print(bw_array)
        bw_array = bw_array[:20]
        print(bw_array)
        return bw_array


    def load_data(self, folder):
        bw_data_up = {}
        bw_data_down = {}
        retr = {}
        wsize = {}

        upload_file = "{}_{}".format('up',folder)
        download_file = "{}_{}".format('down', folder)
        print(upload_file, download_file)

        for i in range(1, 11):

            with open("data/{0}/{0}_{1}.txt".format(upload_file, i)) as reader:
                print("data/{0}/{0}_{1}.txt".format(upload_file, i))
                lines = reader.readlines()

                bw_data_up[i], retr[i], wsize[i] = self.parse_txt(lines)

            with open("data/{0}/{0}_{1}.txt".format(download_file, i)) as reader:
                print("data/{0}/{0}_{1}.txt".format(download_file, i))
                lines = reader.readlines()

                bw_data_down[i] = self.parse_download_txt(lines)

        return bw_data_up, bw_data_down, retr, wsize


    def create_plot(self, title,bw_data_up, bw_data_down, retr, wsize):
        x = range(0, 200)

        target = []
        mbps_up = []
        mbps_down = []
        t_retr = []
        t_wsize = []
        for i in range(10,0,-1):
            mbps_up.extend(bw_data_up[i])
            mbps_down.extend(bw_data_down[i])
            t_retr.extend(retr[i])
            t_wsize.extend(wsize[i])
            target.extend(np.full(20, int(i)))
        retr = t_retr
        wsize = t_wsize

        if len(mbps_down) >200: #little hack to match size
           # length = len(mbps_down) - 200
            mbps_down = mbps_down[:200]

        print(mbps_down)
        print(len(target))
        print("title: {}\nbw_data_up: {}\nbw_data_down: {}\nretr: {}\nwsize: {}".format(title,len(mbps_up),len(mbps_down),len(retr),len(wsize)))
        df = pd.DataFrame({'x': x, 'target': target, 'mbps_up': mbps_up, 'mbps_down': mbps_down, 'wsize': wsize, 'retr': retr})

        fig = plt.figure()
        ax1 = fig.add_subplot(411)  # The big subplot
        ax2 = fig.add_subplot(412)
        ax3 = fig.add_subplot(413)
        ax4 = fig.add_subplot(414)
        # multiple line plot
        #plt.plot('x', 'y1', data=df, marker='o', markerfacecolor='blue', markersize=12, color='skyblue', linewidth=4)
        #plt.plot('x', 'y2', data=df, marker='', color='olive', linewidth=2)

        color = 'black'
        fontsize = 7
        #ax1.set_xlabel('Time (s)', fontsize=fontsize)
        ax1.set_ylabel('Sender (Mbps)', color=color, fontsize=fontsize)
        ax1.plot('x', 'mbps_up', data=df,linewidth=1.0, color=color)
        ax1.step('x', 'target', data=df, where='post', linewidth=1.0, color='tab:red')
        ax1.set_xticks(np.arange(0, 201, 20))
        ax1.set_xticklabels([])
        #ax1.tick_params(axis='y', labelcolor=color)
        ax1.grid(True)
        #ax1.set_title(title)

        #ax1.set_xlabel('Time (s)', fontsize=fontsize)
        ax2.set_ylabel('Receiver (Mbps)', color=color, fontsize=fontsize)
        ax2.plot('x', 'mbps_down', data=df, linewidth=1.0, color=color)
        ax2.step('x', 'target', data=df, where='post', linewidth=1.0, color='tab:red')
        #ax2.yaxis.set_label_position("right")
        ax2.set_xticks(np.arange(0, 201, 20))
        ax2.set_xticklabels([])
        ax2.grid(True)

        # second plot
        #ax2.set_xlabel('Time (s)', fontsize=fontsize)
        ax3.set_ylabel('TCP Window(KB)', color=color, fontsize=fontsize)
        ax3.plot('x', 'wsize', data=df, linewidth=1.0, color=color)
        ax3.set_xticks(np.arange(0, 201, 20))
        ax3.set_xticklabels([])
        #ax2.tick_params(axis='y', labelcolor=color)
        ax3.grid(True)

        #plt.subplot(313)
        ax4.set_xlabel('Time (s)', fontsize=fontsize)
        ax4.set_ylabel('Retransmit(#/s)', color=color, fontsize=fontsize)
        ax4.bar('x', 'retr', data=df, linewidth=1.0, color='tab:blue')
        ax4.set_xticks(np.arange(0, 201, 20))
        ax4.grid(True)


        ax1.set_title(title)
        plt.savefig('plots/{}.png'.format(title), dpi=400)
        print("image saved")
        #plt.show()


    def plot(self, folder_name):

        bw_data_up, bw_data_down, retr, wsize = self.load_data(folder_name)
        self.create_plot(folder_name, bw_data_up, bw_data_down, retr, wsize)




if __name__ == "__main__":
    data_plotter = Plot_bw_data()

    plots = ['combined_20ms', 'combined_200ms', 'red_20ms', 'red_200ms', 'yellow_20ms', 'yellow_200ms']
    for plot in plots:
        data_plotter.plot(plot)



    # combined_20ms
    # combined_200ms
    # red_20ms
    # red_200ms
    # yellow_20ms
    # yellow_200ms
    # simple_path_200ms
