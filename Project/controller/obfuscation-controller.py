# -*- coding: utf-8 -*-
from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI
from Input_parser import Parser
from iperf_detector import Iperf
import ipaddress as ipAddr
import sys
import pandas as pd
import json

class ObfuscationController(object):

    def __init__(self):
        self.topo = Topology(db="../topology.db")
        self.topo.network_graph.remove_node('sw-cpu') #used to set up switch routing, as we don't want to route over sw-cpu
        self.real_topo = Topology(db="../topology.db")
        self.controllers = {}
        self.path_id_counter = 0
        self.df = pd.DataFrame()
        self.COLUMN_NAMES = ['srcIp','dstIp','route_type','flow_type','latency','loss_rate','bandwidth']
        self.init()

    def init(self):
        #self.read_df()
        self.connect_to_switches()
        self.clear_obfuscation_tables()
        self.set_table_defaults()
        self.set_everything_for_meters()
        self.set_iperf_classification()

    def read_df(self):
        try:
            data = {}
            with open("obf_entries.json") as file:
                data = json.load(file)
                self.df = pd.read_json(data, orient='index')
                self.df = self.df[self.COLUMN_NAMES]
            #df.set_index('handle') #for every handle, we have a dictionary containing the entry..
            print("read_df function: {}".format(self.df))
        except:
            print("exception")
            self.df = pd.DataFrame(columns=self.COLUMN_NAMES)
            data = self.df.to_json(orient='index')
            with open('obf_entries.json', 'w') as f:
                json.dump(data, f)

    def save_obf_entries(self):
        self.df = self.df[self.COLUMN_NAMES]
        data = self.df.to_json(orient='index')
        with open('obf_entries.json', 'w') as f:
            json.dump(data, f)

    def connect_to_switches(self):
        for p4switch in self.topo.get_p4switches():
            thrift_port = self.topo.get_thrift_port(p4switch)
            self.controllers[p4switch] = SimpleSwitchAPI(thrift_port)

    def clear_obfuscation_tables(self):
        [controller.table_clear("meter_id_to_meter_read") for controller in self.controllers.values()]
        [controller.table_clear("m_filter") for controller in self.controllers.values()]
        [controller.table_clear("consider_flow") for controller in self.controllers.values()]
        [controller.table_clear("path_id_to_path") for controller in self.controllers.values()]
        #[controller.table_clear("meter_id_to_meter_read") for controller in self.controllers.values()]

    def set_table_defaults(self):
        for controller in self.controllers.values():
            pass
            # set all table defaults..
            #controller.table_set_default("consider_srcAddr", "NoAction", [])
            #controller.table_set_default("consider_dstAddr", "NoAction", [])
            controller.table_add("path_id_to_path", "NoAction", [str(0)]) #hit on path_id 0 means no src routing


    ########
    # Set Meter for rate liming
    ########
    def set_everything_for_meters(self):
        self.set_meter_rates()
        self.set_meter_id_to_meter_read_table()
        self.set_m_filter_table()

    def set_meter_rates(self):
        #Peak Information Rate (PIR) with PBS(peak burst size) and
        #Committed Information Rate (CIR) with CBS(comitted burst size)
        #botw values depend on link bandwidth: here assumed as 20Mbps
        l_bw = 10.0 #Mbitsps *8 = MBps
        MTU = 1500 #bytes
        for sw_name, controller in self.controllers.items():
            #set meter_id_to_meter_read
            for m_id in range(1,11): #[1,10]
                m_name = "meter"+str(m_id)

                #yellow #burst periode of 1000ms = 1s
                cir = l_bw/10 *float(m_id)/8 # bytes/microsec
                cbs = l_bw*1*1000000.0/8 #one second= 1.25MB =833MTU
                #red #measure rate of first 44 packets
                pir = l_bw/10 *float(m_id)/8 # bytes/microsec
                pbs = 44*MTU # this is 66k, meaning one tcp window without scaling

                yellow = str(cir) + ':' + str(int(cbs))
                red = str(pir) + ':' + str(int(pbs))
                print("--->m_name:{}, rates: [{},{}]".format(m_name, yellow,red))
                controller.meter_array_set_rates(m_name, [yellow, red])

    def set_meter_id_to_meter_read_table(self):
        for sw_name, controller in self.controllers.items():
            #set meter_id_to_meter_read
            for m_id in range(1,11): #[1,10]
                controller.table_add("meter_id_to_meter_read", "meter"+str(m_id)+"_action", [str(m_id)])

    def set_m_filter_table(self):
        for sw_name, controller in self.controllers.items():
            #Green = 0
            controller.table_add("m_filter", "NoAction", ["0"])
            #Yellow = 1
            controller.table_add("m_filter", "drop", ["1"])
            #red = 2
            controller.table_add("m_filter", "drop", ["2"])


    ########
    # Iperf detecion, use helper
    ########
    def set_iperf_classification(self):
        iperf_controller = Iperf()
        iperf_controller.main()

    ########
    # Add obfuscation rules and parameters
    ########
    def add_obf_rule(self, new_rule):
        #Precondition: srcIp, dstIp exist in network, srcIp range contains only hosts connected to one switch..

        srcIp = new_rule['srcIp']
        srcIp_range = new_rule['srcIp_range']
        dstIp = new_rule['dstIp']
        dstIp_range = new_rule['dstIp_range']
        flow_type_id, ternary = self.get_flow_type_id(new_rule['flow_type']) #types = ['traceroute', 'iperf', 'ping', 'udp', 'tcp', 'ipv4'] #id == priority!
        ttl = new_rule['ttl']
        if flow_type_id == 1:
            ternary[-1] = "{} &&& 0xff".format(ttl)
        loss_rate = new_rule['loss_rate'] # permille of loss like 1%
        bw = new_rule['bandwidth']

        #find responsible src switch
        src_range = srcIp.split('->')
        for sw_name, controller in self.controllers.items():
            #get source
            for host in self.topo.get_hosts_connected_to(sw_name):
                #passed if no hosts connected to switch
                srcip = ipAddr.ip_network(srcIp.decode('utf-8'),False)
                subnet = ipAddr.ip_network(self.topo.get_host_ip(host))
                if srcip.overlaps(subnet):
                    #set src routing path
                    path_id = self.set_path_and_return_path_id(new_rule['path'],ttl, controller)
                    #ip is included in host subnet
                    print("---Add rule to Switch:{}, srcIP:{}, dstIp:{}".format(sw_name, srcIp_range, dstIp_range))
                    print("prio:{}: path_id:{}, loss_meter:{}, bw:{}, meta_matches:{}".format(flow_type_id, path_id, loss_rate, bw, ternary[0]))
                    handle = controller.table_add("consider_flow", "set_parameters", [srcIp_range, dstIp_range, ternary[1],
                            ternary[2], ternary[3], ternary[4], ternary[5], ternary[6]], [str(flow_type_id), str(path_id), str(ttl), str(loss_rate), str(bw)], str(flow_type_id))
                    print("answer_from_table_add: handle{}".format(handle))

    def get_flow_type_id(self,flow_type):
        # ternary fo say what we care about..["1 &&& 0x1"] last bit must be one,
        # ["1 &&& 0x0"] dont care if bit is 1 or zero
        output = ["1 &&& 0x0","1 &&& 0x0", "1 &&& 0x0", "1 &&& 0x0", "1 &&& 0x0", "1 &&& 0x0", "1 &&& 0x00"]
        activate = "1 &&& 0x1"
        id = 6
        #precondition: will receive one of those values
        if flow_type == 'traceroute':
            output[0] = activate
            id = 1
        elif flow_type == 'ping':
            output[1] = activate
            id = 2
        elif flow_type == 'iperf':
            output[2] = activate
            id = 3
        elif flow_type == 'tcp':
            output[3] = activate
            id = 4
        elif flow_type == 'udp':
            output[4] = activate
            id = 5
        else: #ipv4
            output[5] = activate
            id = 6
        print("OUTPUT TERNARY: {}".format(output))
        return id, output

    def set_path_and_return_path_id(self, path, ttl, controller):
        print("Set src routing path: path:{}".format(path))
        if path == []:
            return 0 #will lead to miss in table, and therefore set NO src routing
        if len(path) == 2:
            if path[0] == path[1]:
                #path closest to target length is to stay on same switch.. do ipv4 routing
                return 0
        #set path and return path_id
        self.path_id_counter += 1
        path_id = self.path_id_counter

        src_header = [str(ttl)] # ( ttl, port0(egress_port), port1,...port9)
        for x, y in zip(path, path[1:]):
            src_header.append(str(self.topo.node_to_node_port_num(x,y)))

        nr_of_hops = len(src_header)-2

        #set path to switch
        print("here error")
        print(nr_of_hops)
        print(path_id)
        print(src_header)
        print("Set src routing path: hop{}, path_id:{}, src_header:{}".format(nr_of_hops, path_id, src_header))
        controller.table_add("path_id_to_path", "hop"+str(nr_of_hops), [str(path_id)], src_header)
        return path_id



if __name__ == "__main__":
    # Dieser block (__main__) nur ausgefuehrt, wenn Modul als eigenstaendiges Programm selbst gestartet wurde,
    #aber nicht, wenn es von einem anderen Modul importiert wurde

    controller = ObfuscationController()
    parser = Parser()

    # get values for obfuscation
    while True:
        new_obf_rule = parser.get_new_rule(controller.df)
        for new_rule in new_obf_rule:
            controller.add_obf_rule(new_rule)
