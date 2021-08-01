import argparse
import logging as log
import sys

from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI


class Iperf(object):

    #instanciate variables
    def __init__(self):
        self.topo = Topology(db="../topology.db")
        self.topo.network_graph.remove_node('sw-cpu') #used to set up switch routing, as we don't want to route over sw-cpu
        self.real_topo = Topology(db="../topology.db")
        self.controllers = {}
        self.init()

    #initialize class by doing certain standart actions
    def init(self):
        self.connect_to_switches()
        self.clear_tables()
        self.set_table_defaults()

    def connect_to_switches(self):
        for p4switch in self.topo.get_p4switches():
            thrift_port = self.topo.get_thrift_port(p4switch)
            self.controllers[p4switch] = SimpleSwitchAPI(thrift_port)

    def clear_tables(self):
        [controller.table_clear("iperf_payload") for controller in self.controllers.values()]

    def set_table_defaults(self):
        print("Table defaults: ")
        #If no match on iperf, do nothing
        [controller.table_set_default("iperf_payload", "NoAction", []) for controller in self.controllers.values()]



    def set_table_iperf_payload(self):
        print("set payload to matcht:")
        # hit on all ports... 0000 means it doesn't matter what the value is
        #self.controller.table_add("detect_iperf", "handle_iperf_flow", ["5001 &&& 0x0000"], [],"1" ) #not really usefull, as we only allow src to pass, so answer limited again..
        # hit only when value is exactly matched
        for controller in self.controllers.values():
            for i in range(10):
                ascii_array = []
                match_string = []
                for j in range(10):
                    ascii_array.append(str((i+j)%10)) # no 10..
                #print("ascii_array: {}".format(ascii_array))

                for idx in range(0,9,2):
                    #print("val{}: {},shifted:{} val{}: {}".format(idx,ord(ascii_array[idx]),ord(ascii_array[idx])<<8 ,idx+1,ord(ascii_array[idx+1]) ))

                    temp = (ord(ascii_array[idx]) << 8) + ord(ascii_array[idx+1])
                    match_string.append(str(temp))

                #add match rule
                #print("iperf_payload, NoAction, {}".format(match_string))
                controller.table_add("iperf_payload", "NoAction", match_string ) #not really usefull, as we only allow src to pass, so answer limited again..


    def main(self):
        self.set_table_iperf_payload()


if __name__ == "__main__":

    controller = Iperf().main()
