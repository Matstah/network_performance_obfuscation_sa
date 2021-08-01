import sys
from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI
import ipaddress as ipAddr
from Graph_algo import Graph
import pandas as pd


class Parser(object):

    def __init__(self):
        self.topo = Topology(db="../topology.db")
        self.topo.network_graph.remove_node('sw-cpu') #used to set up switch routing, as we don't want to route over sw-cpu
        self.real_topo = Topology(db="../topology.db")
        self.existing_flows = pd.DataFrame()
        self.controllers = {}
        self.newEntry = {}
        self.df = pd.DataFrame()
        self.init()

    def init(self):
        self.connect_to_switches()

    def connect_to_switches(self):
        for p4switch in self.topo.get_p4switches():
            thrift_port = self.topo.get_thrift_port(p4switch)
            self.controllers[p4switch] = SimpleSwitchAPI(thrift_port)


#handle inputs
    def get_new_rule(self, df):
        print("\n--------A D D  N E W  R U L E--------")
        newEntry = {}
        self.df = df
        while self.get_flow_type():
            pass
        self.get_srcIp()
        self.get_dstIp()
        #self.get_current_flow_rules(df)
        if self.newEntry['flow_type'] == 'traceroute':
            return self.set_traceroute_hops()
        else:
            self.get_flow_parameters()
            print("NewEntry: {}".format(self.newEntry))
            return [self.newEntry]

    def get_srcIp(self):
        again = True
        while again:
            print("Enter srcIP range to consider, must be hosts to same switch:  <'ip1->ip2'>")
            ip_range = sys.stdin.readline().replace('\n', '')
            if '->' not in ip_range:
                print("ERROR: enter ip range: <'ip1->ip2'> ")
                continue
            splitted = ip_range.split('->')
            ip = splitted[0]
            ip_upper = splitted[1]
            if (not self.validate_ip(ip)) or (not self.validate_ip(ip_upper)):
                print("ERROR: type not valid, enter IPv4 addr with NO prefix")
                continue
            #accept range connected to one switch
            if not self.ip_range_in_subnet(splitted):
                print("ERROR: ip addrs is in not connected to same switch: ")
                continue
            again = False

        self.newEntry['srcIp'] = str(ip) #then i dont need to change everything..
        self.newEntry['srcIp_range'] = ip_range

    def get_dstIp(self):
        again = True
        while again:
            print("Enter dstIP range to consider, mus be hosts to same switch: <'ip1->ip2'>")
            ip_range = sys.stdin.readline().replace('\n', '')
            if '->' not in ip_range:
                print("ERROR: enter ip range: <'ip1->ip2'> ")
                continue
            splitted = ip_range.split('->')
            ip = splitted[0]
            ip_upper = splitted[1]
            if (not self.validate_ip(ip)) or (not self.validate_ip(ip_upper)):
                print("ERROR: type not valid, enter IPv4 addr with NO prefix")
                continue
            #accept range connected to one switch
            if not self.ip_range_in_subnet(splitted):
                print("ERROR: ip addrs is in not connected to same switch: ")
                continue
            again = False

        self.newEntry['dstIp'] = str(ip)
        self.newEntry['dstIp_range'] = ip_range

    def validate_ip(self, ip):
        a = ip.replace('/', '.').split('.')
        if len(a) == 5:
            #if int(a[4]) not in range(0,33):
            return False
        if len(a) == 4:# or len(a) == 5:
            for x in range(0,4):
                try:
                    i = int(a[x])
                    if i < 0 or i > 255:
                        return False
                except ValueError:
                    return False
            return True
        return False

    def ip_range_in_subnet(self, ip_range):
        ip_low = ip_range[0]
        ip_up = ip_range[1]
        test_ip_low = ipAddr.ip_network((ip_low+'/32').decode('utf-8'))
        test_ip_up  = ipAddr.ip_network((ip_up+'/32').decode('utf-8'))
        #get subnet of each switch
        #sw_subnet = ipAddr.ip_network('20.')
        #if ip_low == ip_up && ip_low
        for sw_name, controller in self.controllers.items():
            ip_low_bool = False
            ip_up_bool = False
            #check if they belong to same sw subnet if hosts
            for host in self.topo.get_hosts_connected_to(sw_name):
                #passed if no hosts connected to switch
                subnet = ipAddr.ip_network(self.topo.get_host_ip(host))
                if test_ip_low.overlaps(subnet):
                    ip_low_bool = True
                if test_ip_up.overlaps(subnet):
                    ip_up_bool = True
            if ip_low_bool and ip_up_bool:
                return True
            #check if its switch ip
            ip = '20.{}.1.1'.format(sw_name.replace('s',''))
            if ip_low == ip_up and ip_low == ip:
                return True
        print("Error: No such subnet exists")
        return False

# handle flow type
    def get_current_flow_rules(self,df):
        srcIp = self.newEntry['srcIp']
        dstIp = self.newEntry['dstIp']
        try:
            flow_rules = df.loc[(df['srcIp'] == srcIp) & (df['dstIp'] == dstIp)]
            print("\nExisting flow_rules:\n{}".format(flow_rules))
            print("\nWill eather overwrite(if same flow_type) or create new entry\n")
            self.existing_flows = flow_rules
        except:
            print("No existing entry for this (src,dst)")
            self.existing_flows = pd.DataFrame()

    def get_flow_type(self):
        types = ['traceroute', 'iperf', 'ping', 'udp', 'tcp', 'ipv4']
        print("What type of flow to consider?: \n{}?".format(types))
        flow = sys.stdin.readline().replace('\n', '')
        if flow in types:
            #overwrite = self.existing_flows.loc[self.existing_flows['flow_type'] == flow]
            #if not overwrite.empty:
            #    print("\n Following rules will be overwritten:\n{}\n".format(overwrite))
            self.newEntry['flow_type'] = flow
            return False
        else:
            print("ERROR: type not valid")
            return True

## handle traceroute
    def set_traceroute_hops(self):
        hosts = self.topo.get_hosts()
        output = []
        src_host = ''
        dst_host = ''
        for host in hosts:
            if self.newEntry['srcIp'] == self.topo.get_host_ip(host):
                src_host = host
            if self.newEntry['dstIp'] == self.topo.get_host_ip(host):
                dst_host = host
        routing_path = self.topo.get_shortest_paths_between_nodes(src_host , dst_host)[0]
        print("\nNormal routing path: {}".format(routing_path))
        print("For each switch in path, set parameters:")
        ttl = 1
        for sw in routing_path[1:-1]: #
            ip = "20.{}.1.1".format(sw.replace('s',''))
            dst_ip = self.newEntry['dstIp']
            self.newEntry['dstIp'] = ip
            self.newEntry['dstIp_range'] = ip+'->'+ip
            self.newEntry['ttl'] = str(ttl)
            print("\n####S-> {} with ttl:{} in path:{}####".format(sw,ttl,routing_path))
            self.get_flow_parameters() #self.newEntry should overwrite all importent values
            ttl += 1
            self.newEntry['dstIp'] = dst_ip
            self.newEntry['dstIp_range'] = dst_ip+'->'+dst_ip
            output.append(self.newEntry.copy())
        print("newEntry: traceroute on path from src:{} to dst:{}".format(src_host,dst_host))
        return output

## Handle Flow parameters..
    def get_flow_parameters(self):
        print("\nEnter parameters to manipulate flow type:")
        #'route_type'
        while self.get_route_type():
            pass
        #'latency'
        self.get_latency()
        #'loss_rate'
        while self.get_packet_loss_rate():
            pass
        #'bandwidth'
        while self.get_bandwidth():
            pass

# Route type
    def get_route_type(self):
        route_type = ['simple_path','same_path', 'any_path']
        print("What routing is allowed? Pick one:\n{}".format(route_type))
        route = sys.stdin.readline().replace('\n','')
        if route in route_type:
            self.newEntry['route_type'] = route
            if route in 'any_path':
                self.newEntry['route_type'] = 'loopy_path'
            return False
        else:
            print("ERROR: type not valid")
            return True

## latency measurement
    def get_latency(self):
        max_lat = self.get_max_latency()
        min_lat = self.get_min_latency()
        while True:
            print("Enter prefered latency in miliseconds, as integer")
            try:
                latency = sys.stdin.readline().replace('\n','')
                value = int(latency)
                if value in range(min_lat[0], max_lat[0]+1):
                    self.newEntry['latency'] = str(int(value))
                    break
                else:
                    print("ERROR: Use latency that lies between {}ms and {}ms.".format(min_lat[0], max_lat[0]))
                    continue
            except ValueError:
                print("ERROR: type not valid, use integer.")
        print("Entered latency:"+latency)
        best_path_latency, best_path  = self.search_best_path(int(self.newEntry['latency']), 10)
        print("best_latency:{}ms \nbest path:{}".format(best_path_latency, best_path))
        self.newEntry['latency'] = best_path_latency
        self.newEntry['path'] = best_path

    def get_latency_of_path(self, path):
        delay = 0
        for x, y in zip(path, path[1:]):
            #print("\nDelay between x:{}, y:{} is {}\n".format(x,y,self.topo.node(x)[y]['delay'].replace('ms','')))
            delay += int(self.topo.node(x)[y]['delay'].replace('ms',''))
        return delay

    def get_slowest_simple_path(self, src, dst):
        delay = 0
        max_path = []
        paths = self.topo.network_graph.get_all_simple_paths_between_nodes(src,dst)
        for path in paths:
            path_delay = self.get_latency_of_path(path)
            if path_delay > delay:
                delay = path_delay
                max_path = path
        return (delay, max_path)

    def get_slowest_same_path(self,src,dst):
        delay = 0
        max_path = []
        max_links = 10 #defined by max src routing header(9) + first egress port
        largest_links = []
        path = self.topo.get_shortest_paths_between_nodes(src,dst)[0] #includes hosts..
        #print("\nShortest path found:".format(path))
        #first, get largest links
        best_link_delay = 0
        for x, y in zip(path, path[1:]):
            link_delay = int(self.topo.node(x)[y]['delay'].replace('ms',''))
            if best_link_delay > link_delay:
                continue
            elif best_link_delay == link_delay:
                largest_links.append((x,y))
            else: #link_delay > best_link_delay
                largest_links = [(x,y)]
                best_link_delay = link_delay
        #print("Largest_links:{}, best link delays: {}".format(largest_links, best_link_delay))
        max_links -= (len(path)-3) #-2 to remove hosts links, #switches-1 = number of links
        num_round_trips = max_links/2 #each link needs to be used odd times
        to_add_links = [0 for x in range(len(largest_links))] #counter of how often to use each longest link
        for i in range(0,num_round_trips):
            j = i % len(largest_links)
            to_add_links[j] += 1
        # make the long path
        #print("counts of where to add links: {}".format(to_add_links))
        j=0
        path = list(path)
        path_copy = path
        for x, y in zip(path_copy, path_copy[1:]):
            if not largest_links:
                #no links to add anymore
                continue
            j += 1
            #print("\nx:{}, y:{}, j:{}\n".format(x,y,j))
            if (x,y) == largest_links[0]:
                to_add = []
                for nr in range(to_add_links.pop(0)):
                    to_add.extend([y,x])

                path = path[:j] + to_add + path[j:]
                #print("updated path with added link:{}".format(path))
                j += len(to_add)
                largest_links.pop(0)
        delay = self.get_latency_of_path(tuple(path))
        #print("\nMaximum possible latency on same_path: {}ms\n".format(delay))
        #print("\nThe path with max latency: {}".format(path))
        return (delay,path)

    def get_slowest_loopy_path(self,src,dst):
        graph = Graph()
        #problem.. we src,dst include h1,h2.. but we want
        src_neighbors = self.topo.get_neighbors(src)
        dst_neighbors = self.topo.get_neighbors(dst)
        src_node = 0
        dst_node = 0
        for next in src_neighbors:
            if self.topo.get_node_type(next) == 'switch':
                src_node = next
                break
        for next in dst_neighbors:
            if self.topo.get_node_type(next) == 'switch':
                dst_node = next
                break
        #get longest path with 10 hops
        best_path, path_length, target_length, best_cost = graph.search_best_any_path(src_node, dst_node, graph.inf,10)
        return path_length, [src,best_path, dst]

    def get_max_latency(self):
        #Precondition src,dst ip exists and are hosts
        hosts = self.topo.get_hosts()
        max_path = ()
        src_host = ''
        dst_host = ''
        for host in hosts:
            if self.newEntry['srcIp'] == self.topo.get_host_ip(host):
                src_host = host
            if self.newEntry['dstIp'] == self.topo.get_host_ip(host):
                dst_host = host
        if dst_host == '':
            #dst ip is not a host, but a switch
            dst_host = 's' + self.newEntry['dstIp'].split('.')[1]
        if self.newEntry['route_type'] == 'simple_path':
            max_path = self.get_slowest_simple_path(src_host, dst_host)
        elif self.newEntry['route_type'] == 'same_path':
            max_path = self.get_slowest_same_path(src_host, dst_host)
        elif self.newEntry['route_type'] == 'loopy_path':
            max_path = self.get_slowest_loopy_path(src_host, dst_host)
        print("\nMaximum possible latency: {}ms".format(max_path[0]))
        return max_path

    def get_min_latency(self):
        #precondition: srcIp and dstIp exist. srcIp is a host, dstIp might be host or switch
        hosts = self.topo.get_hosts()
        min_path = []
        src_host = ''
        dst_host = ''
        for host in hosts:
            if self.newEntry['srcIp'] == self.topo.get_host_ip(host):
                src_host = host
            if self.newEntry['dstIp'] == self.topo.get_host_ip(host):
                dst_host = host
        if dst_host == '':
            #dst ip is not a host, but a switch
            dst_host = 's' + self.newEntry['dstIp'].split('.')[1]
        min_path = self.topo.get_shortest_paths_between_nodes(src_host , dst_host)[0]
        if self.newEntry['flow_type'] in ['iperf', 'udp', 'tcp', 'ipv4','ping']:
        #if not to ip within our network (our routers), shortest path = fastest
            ttl = len(min_path)-3 # -src_host -dst_host -last switch
            if ttl < 0:
                ttl = 0
            self.newEntry['ttl'] = str(ttl) # -src_host -dst_host -last switch
        elif self.newEntry['flow_type'] in ['traceroute']:
            ##traceroute traffic determined as traffic that stops inside our network
            #imediate response possible
            #min_path = []
            pass
        #calc latency
        delay = self.get_latency_of_path(min_path)
        print("Minimum possible latency: {}ms".format(delay))
        return (delay, min_path)

    def search_best_path(self, target_length, max_hops):
        graph = Graph()
        hosts = self.topo.get_hosts()
        src_host = ''
        dst_host = ''
        for host in hosts:
            if self.newEntry['srcIp'] == self.topo.get_host_ip(host):
                src_host = host
            if self.newEntry['dstIp'] == self.topo.get_host_ip(host):
                dst_host = host
        if dst_host == '':
            #dst ip is not a host, but a switch
            dst_host = 's' + self.newEntry['dstIp'].split('.')[1]
        src_neighbors = self.topo.get_neighbors(src_host)
        sw_s = ''
        sw_t = ''
        for next in src_neighbors:
            if self.topo.get_node_type(next) == 'switch':
                sw_s = next
                break
        if dst_host[0] != 's':
            dst_neighbors = self.topo.get_neighbors(dst_host)
            for next in dst_neighbors:
                if self.topo.get_node_type(next) == 'switch':
                    sw_t = next
                    break
        else:
            sw_t = dst_host
        #get longest path with 10 hops
        return graph.search_best_path(self.newEntry['route_type'], sw_s, sw_t, target_length, max_hops)

#Loss rate
    def get_packet_loss_rate(self):
        print("Enter packet loss in permille (x/1000), type integer:")
        lr = sys.stdin.readline().replace('\n','')
        if lr == '':
            print("No packet loss, value = 0 permille")
            self.newEntry['loss_rate'] = '0'
            return False
        try:
            value = int(lr)
            if value in range(0,1001):
                self.newEntry['loss_rate'] = str(value)
                print("Packet loss: {}permille".format(value))
                return False
            else:
                print("ERROR: value must be between 0 and 1000")
                return True
        except ValueError:
            print("ERROR: type not valid, use int")
            return True
        return False

#bandwith/ throughput
    def get_bandwidth(self):

        #smallest link capacity is upper bound
        bw_limit = 10
        print("\nMaximum possible bandwidth: {}bytes/microsec".format(bw_limit))
        print("Possible meter_id with values:")
        print("meter_id 1 =  1Mbps,\nmeter_id 2 =  2Mbps,\nmeter_id 3 =  3Mbps,\nmeter_id 4 =  4Mbps,\nmeter_id 5 = 5Mbps,")
        print("meter_id 6 = 6Mbps,\nmeter_id 7 = 7Mbps,\nmeter_id 8 = 8Mbps,\nmeter_id 9 = 9Mbps,\nmeter_id 10= 10Mbps")
        print("Select meter id:")
        bw = sys.stdin.readline().replace('\n','')
        if bw == '':
            print("No bandwidth limit set")
            self.newEntry['bandwidth'] = str(0)
            return False
        try:
            value = int(bw)
            if value in range(1,11):
                self.newEntry['bandwidth'] = str(value)
                return False
            else:
                print("given id is no meter id.")
                return True
        except ValueError:
            print("ERROR: type not valid, use int for meter id")
            return True
