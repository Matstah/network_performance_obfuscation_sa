
import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

class Plot_ping_data(object):

    def __init__(self):
        pass



    def parse_txt(self, lines):
        #only care about data line
        output = {}
        data = lines[2:]
        hop = 1
        for line in data:
            all_numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)[-5:]
            all_numbers = [float(x) for x in all_numbers]
            #print(hop)
            print(all_numbers)
            mean = np.mean(all_numbers)
            var = np.sqrt( np.var(all_numbers))
            output[str(hop)] = [mean, var]
            hop += 1
        print(output)

        return output




    def load_data(self, non_obf, obf):
        non_obf_values = {}
        obf_values = {}

        #load non obf
        with open(non_obf, 'r') as reader:
            lines = reader.readlines()
            non_obf_values = self.parse_txt(lines)

        # load non obf
        with open(obf, 'r') as reader:
            lines = reader.readlines()
            obf_values = self.parse_txt(lines)

        return non_obf_values, obf_values




    def create_plot(self, plot_name, non_obf, obf):

        x = range(1,6)
        y = []
        err = []
        y_obf = []
        err_obf = []

        for i in x:
            y.append(non_obf[str(i)][0]) #mean
            err.append(non_obf[str(i)][1]) #var

            y_obf.append(obf[str(i)][0])
            err_obf.append((obf[str(i)][1]))

        #plt.errorbar(x, y, err,  fmt='.k')
        #plt.errorbar(x, y_obf, err_obf, fmt='.k')

        plt.plot(x,y,'-',marker='o', label="Normal traceroute", color='black')
        plt.plot(x,y_obf,'-',marker='o', label="Obfuscated traceroute", color='tab:red')

        print("difference per hop: {}".format(np.round(abs(np.array(y) - np.array(y_obf)))))

        plt.xticks(x)

        plt.ylabel("Round Trip Time (ms)")
        plt.xlabel("Number of hops")

        plt.legend()
        plt.grid()
        #plt.title(plot_name)
        plt.savefig('plots/{}.png'.format(plot_name), dpi=400)
        print("image saved")
        plt.show()



    def plot(self):

        non_obf = "data/traceroute.txt"
        obf = "data/traceroute_obfuscated.txt"
        plot_name = "Traceroute Obfuscation"

        non_obf, obf = self.load_data(non_obf, obf)
        self.create_plot(plot_name, non_obf, obf)



if __name__ == "__main__":

    Plot_ping_data().plot()

