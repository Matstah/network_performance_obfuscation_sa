
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

        line = lines[3]
        print(line)
        #print(re.findall(r"(\d+)%", line)[0])
        return int(re.findall(r"(\d+)%", line)[0])




    def load_data(self, folder):
        target_loss = []#[0]
        loss = []
        #files = os.listdir("{}".format(folder))
        for loss_rate in range(0, 11):
            for mesurement_nr in range(1, 11):
                print(loss_rate, mesurement_nr)
                target_loss.append(int(loss_rate))

                file_name = folder + '/' + 'ping_{}_{}.txt'.format(loss_rate, mesurement_nr)
                with open(file_name, 'r') as reader:
                    lines = reader.readlines()
                    real = self.parse_txt(lines)
                    loss.append(real)

        print(target_loss)
        print(loss)

        return target_loss, loss




    def create_plot(self, plot_name, target_loss, loss):
        #fig = plt.figure()
        df = pd.DataFrame({'x': range(len(loss)), 'target_loss': target_loss, 'loss': loss})

        color = 'black'
        fontsize = 8
        plt.step('x', 'target_loss', where='post', data=df, linewidth=2.0, color='tab:red')
        plt.plot('x', 'loss', data=df, linewidth=1.0, marker='.', color=color)
        plt.xticks(np.arange(0, 111, 10))
        plt.yticks(range(11))

        plt.ylabel("Packet Loss (%)")
        plt.xlabel("Unit (1000 Packets/Sample)")

        plt.grid()
        plt.title(plot_name)
        plt.savefig('plots/{}.png'.format(plot_name), dpi=400)
        print("image saved")
        plt.show()

    def create_average_plot(self, plot_name, target_loss, loss):
        # average the loss
        average_loss = []

        for i in range(0,11):
            start = i*10
            end = i*10 + 10
            mean = np.mean(loss[start:end])
            average_loss.extend(np.full(10, mean))

        df = pd.DataFrame({'x': range(len(loss)), 'target_loss': target_loss, 'average_loss': average_loss})

        color = 'black'
        fontsize = 8
        plt.step('x', 'target_loss', data=df, linewidth=1.5, color='tab:red')
        plt.plot('x', 'average_loss', '.', data=df, color=color)
        plt.xticks(np.arange(0, 111, 10))
        plt.yticks(range(11))

        plt.ylabel("Average packet Loss (%)")
        plt.xlabel("Unit (1000 Packets/Sample)")

        plt.grid()
        plt.title(plot_name)
        plt.savefig('plots/{}.png'.format('average_'+plot_name), dpi=400)
        print("image saved")
        plt.show()


    def plot(self):
        folder_name = "data"
        plot_name = "packet_loss_rate"

        target_loss, loss = self.load_data(folder_name)
        self.create_plot(plot_name, target_loss, loss)
        #self.create_average_plot(plot_name, target_loss, loss)



if __name__ == "__main__":
    Plot_ping_data().plot()


    # combined_20ms
    # combined_200ms
    # red_20ms
    # red_200ms
    # yellow_20ms
    # yellow_200ms
    # simple_path_200ms