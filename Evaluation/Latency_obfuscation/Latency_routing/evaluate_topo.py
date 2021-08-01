import geopy.distance
import networkx as nx
import matplotlib
import numpy as np

from matplotlib.ticker import MaxNLocator
from random import choice
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import os
from Best_path_finder import Graph


class Set_up_network(object):

    def __init__(self):
        self.pos = {}
        self.edge_labels = {}
        pass

    def print_network(self, net, net_name, show_node_names, show_edge_weigths):
        print("plot")
        switch_delay = 0#2.0 / 3 * 300000 * 0.001
        edge_delay = {}
        pos = {}
        f100 = plt.figure(100)
        for city, node in net.nodes.items():
            #print(city)
            pos[city] = (float(node['Longitude']), float(node['Latitude']))
            #print(pos[city])
            for n_city in net.neighbors(city):
                edge_delay[(city, n_city)] = net[city][n_city]['delay'] - switch_delay #subtract time given by switch delay
                if edge_delay[(city, n_city)] <0:
                    edge_delay[(city, n_city)] = 0
        labels = None#{node: node[:3] for node in net.nodes()}

        plt.title(net_name)
        nx.draw(net, pos, weight='delay', edge_color='black', width=1, linewidths=1, \
                node_size=100, node_color='pink', alpha=0.9, labels=labels, with_labels=show_node_names)  # ,labels={node:node[:3] for node in G.nodes()}
        #nx.draw(G, with_labels = True, weight='delay')

        if show_edge_weigths:
            nx.draw_networkx_edge_labels(net, pos, edge_labels=edge_delay)
        plt.title(net_name)
        plt.savefig('plots/{}.png'.format(net_name), dpi=400)
        plt.clf()
        #plt.show()

        #print("experiment:")
        #print(net.nodes.data())
        #print(net.number_of_nodes())
        #print(net.nodes)
        #print(net.number_of_edges())
        #print(net.edges)

    def calc_distance(self, start,target):
        switch_delay = 0#2.0 / 3 * 300000 * 0.001  # 1ms on 2/3 of speed of light(e-signal speed) gives 200km
        #lat,long
        coords_1 = (start['Latitude'], start['Longitude'])
        #print(coords_1)
        coords_2 = (target['Latitude'], target['Longitude'])
        #print(coords_2)
        km = geopy.distance.vincenty(coords_1, coords_2).km
        if int(round(km)) == 0:
            #to separate points
            km = 1.0
        km += switch_delay
        return round(km)

        # light_speed = 300  # km/s
        # link_lenght = geopy.distance.vincenty(coords_1, coords_2).km
        # sw_delay = 0
        # link_delay = link_lenght / light_speed + sw_delay  # would be a constant added everywhere..might be empty, then king of link latency..
        # therefore we could actually just use distance km..

    def set_edge_delay(self, net):
        for city, node in net.nodes.items():
            #print(city)
            #print(node)
            #print("neighbours:")
            #print(node['Latitude'])
            for n in net.neighbors(city):
             #   print("from {} to {} in: km:".format(city,n))
                dist = self.calc_distance(node, net.nodes[n])
                self.edge_labels[(city, n)] = str(dist)#+'km'
                net[city][n]['delay'] = dist
             #   print(net.get_edge_data(city, n))

    def remove_all_nodes_with_no_coordinates(self,net):
        r_graph = net.copy()
        for city, node in net.nodes.items():
            if 'Latitude' in node and 'Longitude' in node:
                pass
            else:
                r_graph.remove_node(city)
        return r_graph

    def remove_parallel_egdes(self,net):
        r_graph = net.copy()
        visited_nodes = []
        for city, node in net.nodes.items():
            for n_city in net.neighbors(city):
                if n_city not in visited_nodes:
                    nr_edges =net.number_of_edges(city, n_city)
                    for i in range(0, nr_edges-1):
                        r_graph.remove_edge(city, n_city)
            visited_nodes.append(city)

        return r_graph

    def remove_nodes_with_no_edges(self, net):
        r_graph = net.copy()
        for city, node in net.nodes.items():
            if net.degree(city) == 0:
                r_graph.remove_node(city)
        return r_graph

    def load_topos_into_nx_graph(self):
        graphs = []
        graphs_name = []
        files = os.listdir("topos/")  # array with file names
        print("Number of topologies: {}".format(len(files)))
        for file in files:
            graphs_name.append(str(file)[:-4])
            print(file)
            graphs.append(nx.read_gml("topos/{}".format(file)))
            if 'ATT' in  file:
                #gra = self.remove_all_nodes_with_no_coordinates(graphs[-1])
                #self.set_edge_delay(gra)
                #self.print_network(gra)
                pass
        return graphs, graphs_name

    def plot_hops_vs_delay(self, G, src, dst):
        # for one graph, pick a source and destination, and run on different delay values
        data = {'hops': [], 'delay': [], 'delay_real': []}

        for delay in range(1, 801, 10):
            # max_min_search(self, sw_s, sw_t, target_length, max_hops):
            best_path, path_length, target_length, best_cost = G.max_min_search(src, dst, delay, 10)
            print(best_path, path_length, target_length, best_cost)
            nr_hops = len(best_path)-1
            data['hops'].append(nr_hops)
            # convert KM into ms, by applying:
            # smallest path = 17 km. Define this to be 1ms.. (includes switch and so on..)
            data['delay'].append(float(delay)/17)
            data['delay_real'].append(float(path_length)/17)

        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()

        color = 'black'
        ax1.set_xlabel("target delay (ms)")
        ax1.set_xticks(range(0, 50, 5))
        ax1.set_ylabel("# hops")
        ax2.set_ylabel("path delay (ms)", color='blue')
        ax1.plot(data['delay'], data['hops'], '-o', markersize=4.0, linewidth=1.0, color=color)
        #plt.xticks(range(0, len(data), 5))
        ax2.plot(data['delay'], data['delay_real'], '-o', markersize=4.0, linewidth=1.0, color='blue')

        ax1.grid(True, axis='x')
        ax2.grid(True, axis='y')
        plt.title("Network Overhead between {}-{}".format(src,dst))
        plt.savefig('plots/{}.png'.format("1_hop_difference_denmark"), dpi=400)
        plt.show()

    def plot_hops_vs_delay_multiple(self, Gnx):
        G = Graph(Gnx)
        n = 1
        delays = range(1, 1000, 50)
        colors = plt.cm.rainbow(np.linspace(0, 1, n))
        all_nodes = list(Gnx.nodes())
        evaluated = set()
        df = {}
        max_link = max(dict(Gnx.edges).items(), key=lambda x: x[1]['delay'])[1]['delay']
        max_delay = max_link * n
        delays = range(1, max_delay, int(max_delay/100.0))
        print(max_link)

        for i in range(1, n+1):
            #print(all_nodes)
            src = choice(all_nodes)
            dst = choice(all_nodes)
            while (src, dst) in evaluated or (dst, src) in evaluated:
                src = choice(all_nodes)
                dst = choice(all_nodes)
            evaluated.add((src, dst))
            evaluated.add((dst, src))
            print("----->random src: {}, dst: {}".format(src, dst))

            data = {'hops': [], 'delay': [], 'delay_real': []}

            for delay in delays:
                # max_min_search(self, sw_s, sw_t, target_length, max_hops):
                best_path, path_length, target_length, best_cost = G.max_min_search(src, dst, delay, 10)
                print(best_path, path_length, target_length, best_cost)
                nr_hops = len(best_path)-1
                data['hops'].append(nr_hops)
                data['delay'].append(delay)
                data['delay_real'].append(path_length)
                data['src'] = str(src)
                data['dst'] = str(dst)

            df[str(i)] = data
            min_hops = data['hops'][0]
            if min_hops == 0:
                min_hops = "no path"
            label = "{} -> {}; min_hops:{}".format(src, dst, min_hops)
            color = colors[i-1]
            plt.plot(delays, data['hops'], markersize=1.0, linewidth=1.0, color=color, label=label)
        plt.title("10 combis")
        plt.xlabel("target delay")
        plt.ylabel("# hops")
        plt.legend(loc='lower right')
        plt.grid(True)
        plt.show()

    def shortest_simple_path_with_n_hops(self,n,src,dst,Gnx):
        all_paths = list(nx.all_simple_paths(Gnx, src, dst, n))
        #print("all_simple_paths: {}".format(all_paths))
        best_path = []
        smallest_latency = 0
        for path in all_paths:
            #only look at path with correct length
            if len(path)-1 != n:
                continue

            delay = 0
            for x, y in zip(path, path[1:]):
                link_delay = Gnx.get_edge_data(x, y)['delay']
                delay += int(link_delay)
            if smallest_latency > delay:
                smallest_latency = delay
                best_path = path
            elif smallest_latency==0 and best_path==[]:
                smallest_latency = delay
                best_path = path


        #print("********** all_valid_paths: {}, delay = {}".format(best_path, smallest_latency))
        return best_path, smallest_latency

    def distanced_neighbours(self, src, Gnx, shortest_hop_count):
        all_nodes = list(Gnx.nodes())
        qualified_neighbours = []
        for node in all_nodes:
            #shortest_path, best_latency = self.shortest_simple_path_with_n_hops(shortest_hop_count, src, node, Gnx)
            shortest_path = nx.shortest_path(Gnx, source=src, target=node, weight='delay')
            #what if there is no shortest path to any other node of length hop_count.. look at simple paths!
            #print(shortest_path)
            hop_count = len(shortest_path) - 1
            if hop_count == shortest_hop_count:
                qualified_neighbours.append(node)
                #print("######## QUALIFIED: {} ######".format(node))
        #print("######## ALL QUALIFIED: {} ######".format(qualified_neighbours))
        return qualified_neighbours


    def latency_increase_vs_hop_count(self, Gnx, shortest_hop_count, num_of_samples):
        if not nx.is_connected(Gnx):
            print("Graph not fully connected")
            return 0

        evaluated = set()
        all_nodes = list(Gnx.nodes())
        y = []
        max_increase = 2001
        x = range(0, max_increase, 20)

        for i in range(num_of_samples):
            # Pick a random node
            #print("sample_{}---->evaluated set : {}".format(i, evaluated))
            src = choice(all_nodes)
            all_nodes_of_distance = self.distanced_neighbours(src, Gnx, shortest_hop_count)
            #print("########## all nodes at distance: {} ##########".format(all_nodes_of_distance))
            while all_nodes_of_distance == []:
                # todo infinity loop
                print("No other node has shortest path of n hops, pick other source")
                src = choice(all_nodes)
                all_nodes_of_distance = self.distanced_neighbours(src, Gnx, shortest_hop_count)

            dst = choice(all_nodes_of_distance)
            #while src == dst: # should actually never happen.. savety first
            #    dst = choice(all_nodes_of_distance)

            # if node combination already used, pick an other one
            while (src, dst) in evaluated or (dst, src) in evaluated:
                src = choice(all_nodes)
                all_nodes_of_distance = self.distanced_neighbours(src, Gnx, shortest_hop_count)

                #if no shortest path to any node at this distance, pick other src.
                while all_nodes_of_distance == []:
                    #todo infinity loop
                    print("No other node has shortest path of n hops, pick other source")
                    src = choice(all_nodes)
                    all_nodes_of_distance = self.distanced_neighbours(src, Gnx, shortest_hop_count)

                dst = choice(all_nodes_of_distance)
            evaluated.add((src, dst))
            evaluated.add((dst, src))

            shortest_path = nx.shortest_path(Gnx, source=src, target=dst, weight='delay')
            min_hops = len(shortest_path) - 1
            min_dist = nx.shortest_path_length(Gnx, source=src, target=dst, weight='delay')

            x_i = range(0, max_increase, 20)
            y_i = [min_hops]
            #y_actual_latency = [min_dist]
            #y_target_latency = [min_dist]

            for j in x[1:]:
                increase = (j+100)*0.01
                target_latency = increase * min_dist
                G = Graph(Gnx)

                print(j, target_latency)
                best_path, path_length, target_length, best_cost = G.max_min_search(src, dst, target_latency, 10)
                #print("src:{}, dst:{}".format(src, dst))
                #print("##best_path: {}, path_length: {}, target: {}, best_cost: {}".format(best_path, path_length, target_length, best_cost))

                y_i.append(len(best_path)-1)
                #y_actual_latency.append(path_length)
                #y_target_latency.append(target_latency)
            if i == 0:
                y = [y_i]
                print("y in if: {}".format(y_i))
            else:
                print("y_i in else: {}".format(y_i))
                y = np.vstack([y, y_i])
                print("y in else: {}".format(y))
        print("y before mean: {}".format(y))
        y_mean = np.mean(y, axis=0)
        print("y_mean: {}".format(y_mean))
        label = "Minimum {} hops".format(shortest_hop_count)
        #plt.step(x, y_mean, where='post', color='black',  linewidth=1.0, label=label)
        #plt.ylabel("Number of hops")
        #plt.xlabel("Latency increase from shortest path (%)")
        #plt.yticks(range(1,11))
        #plt.grid()

        #print("latency_increase_vs_hop_count plot shown")
        #plt.show()

        return x, y_mean


    def compare_networks(self,Gnx,net_name , shortest_hop_count, num_of_samples):
        colors = ['black', 'tab:red', 'blue', 'green']
        colors = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33', '#a65628', '#f781bf']
        for i, hops in enumerate(shortest_hop_count):
            x, y_mean = self.latency_increase_vs_hop_count(Gnx, hops, num_of_samples)
            #print(y_mean)
            label = "Shortest path of {} hops".format(hops)
            plt.step(x, y_mean, where='post', color=colors[i], linewidth=1.5, label=label, alpha=0.75)

        plt.ylabel("Number of hops")
        plt.xlabel("Latency increase from shortest path (%)")
        plt.yticks(range(1, 11))
        plt.grid()
        plt.legend()
        plt.title("{} randomly picked nodes per line".format(num_of_samples))

        print("compare_networks plot shown")

        plt.savefig('plots/{}.png'.format(net_name+'_hops'), dpi=400)
        plt.clf()

        #plt.show()



    def print_topology_features(self, Gnx, name):

        text = "name of network: {}".format(name)
        print("name of network: {}".format(name))
        nodes = list(Gnx.nodes())
        edges = list(Gnx.edges()) # pairs of src, dst of each edge
        number_of_nodes = len(nodes)
        number_of_edges = len(edges)
        print("number of nodes: {}".format(number_of_nodes))
        text += '\n' + "number of nodes: {}".format(number_of_nodes)
        print("number of edges: {}".format(number_of_edges))
        text += '\n' + "number of edges: {}".format(number_of_edges)

        average_degree = float(number_of_edges)/float(number_of_nodes)
        print("average degree per node: {}".format(average_degree))
        text += '\n' + "average degree per node: {}".format(average_degree)

        switch_delay = 0 #2.0 / 3 * 300000 * 0.001
        all_edge_weights = np.array([Gnx.get_edge_data(src, dst)['delay'] - switch_delay for src, dst in edges])
        all_edge_weights[ np.where(all_edge_weights<0) ] = 0 #remove latency added by switch

        print("network size: {}".format(sum(all_edge_weights)))
        text += '\n' + "network size: {}".format(sum(all_edge_weights))
        print("max link size: {}".format(np.max(all_edge_weights)))
        text += '\n' + "max link size: {}".format(np.max(all_edge_weights))
        print("min link size: {}".format(np.min(all_edge_weights)))
        text += '\n' + "min link size: {}".format(np.min(all_edge_weights))
        print("median link size: {}".format(np.median(all_edge_weights)))
        text += '\n' + "median link size: {}".format(np.median(all_edge_weights))
        print("average link site: {}".format(np.mean(all_edge_weights)))
        text += '\n' + "average link site: {}".format(np.mean(all_edge_weights))

        file = open("plots/{}_data.txt".format(name), "w")
        file.write(text)
        file.close()


    def main(self):

        # initiate graphs from topology data
        graphs, graphs_name = self.load_topos_into_nx_graph()
        for i, G in enumerate(graphs):
            G = self.remove_all_nodes_with_no_coordinates(G)
            G = self.remove_parallel_egdes(G)
            G = nx.Graph(G)
            G = self.remove_nodes_with_no_edges(G)
            self.set_edge_delay(G)
            graphs[i] = G
            #self.print_network(G)




        ######## print network ########
        #self.print_network(graphs[0])


        ######## Plot hops vs delay target vs actual delay ########
        # close by: 'Lyngby', 'Orestad',
        # far away: 'Lyngby', 'Arthus',
        G = Graph(graphs[0])
        show_node_names = True
        show_edge_weigths = False
        src = 'Lyngby' #'Lyngby'
        dst = 'Orestad' #'Orestad'
        #self.print_network(graphs[0], graphs_name[0], show_node_names, show_edge_weigths)
        self.plot_hops_vs_delay(G, src, dst)



        ######## compare networks ########

        # network for presentation: 0,1,14
        # 0: UniC
        # 1: Bandcon
        # 14: switchL3
        grapth_id = 0

        Gnx = graphs[grapth_id]

        #self.print_topology_features(Gnx, graphs_name[grapth_id])
        show_node_names = False
        show_edge_weigths = False
        #self.print_network(graphs[grapth_id], graphs_name[grapth_id], show_node_names, show_edge_weigths)
        num_of_samples = 5
        shortest_hop_count = [1, 3, 4]
        #self.compare_networks(Gnx, graphs_name[grapth_id], shortest_hop_count, num_of_samples)


    def test(self):
        pass



if __name__=='__main__':
    net = Set_up_network()
    net.main()
    #net.test()

