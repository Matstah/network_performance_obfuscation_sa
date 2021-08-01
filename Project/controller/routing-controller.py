from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI

class RoutingController(object):

    def __init__(self):
        self.topo = Topology(db="topology.db")
        self.topo.network_graph.remove_node('sw-cpu') #used to set up switch routing, as we don't want to route over sw-cpu
        self.real_topo = Topology(db="topology.db")
        self.controllers = {}
        self.init()

    def init(self):
        self.connect_to_switches()
        self.reset_states()
        self.set_table_defaults()

    def reset_states(self):
        [controller.reset_state() for controller in self.controllers.values()]

    def connect_to_switches(self):
        for p4switch in self.topo.get_p4switches():
            thrift_port = self.topo.get_thrift_port(p4switch)
            self.controllers[p4switch] = SimpleSwitchAPI(thrift_port)

    def set_table_defaults(self):
        for controller in self.controllers.values():
            controller.table_set_default("ipv4_lpm", "drop", [])


    # Sets ipv4 routing tables
    def route(self):

        for sw_name, controller in self.controllers.items():
            for sw_dst in self.topo.get_p4switches():

                #if its ourselves we create direct connections
                if sw_name == sw_dst:
                    for host in self.topo.get_hosts_connected_to(sw_name):
                        sw_port = self.topo.node_to_node_port_num(sw_name, host)
                        host_ip = self.topo.get_host_ip(host) + "/32"
                        host_mac = self.topo.get_host_mac(host)

                        #add rule to reach hosts
                        #print "table_add at {}:".format(sw_name)
                        self.controllers[sw_name].table_add("ipv4_lpm", "set_nhop", [str(host_ip)], [str(host_mac), str(sw_port)])#, "0"])
                    #set ip of switch
                    ip = "20.{}.1.1".format(sw_name.replace('s',''))
                    for intf, node in self.topo.get_interfaces_to_node(sw_name).items():
                        port_number = self.topo.interface_to_port(sw_name, intf)
                        #switch only has 1 ip
                        controller.table_add("icmp_ingress_port", "set_src_icmp_ip", [str(port_number)], [str(ip)])
                        #make switch pingable by giving it its name
                        #controller.table_add("ipv4_lpm", "me", [ip+'/32'])
                        controller.table_add("is_it_me", "NoAction", [ip])

                else:
                    #routing towards switches
                    ip =  "20.{}.1.1/24".format(sw_dst.replace('s',''))
                    path = self.topo.get_shortest_paths_between_nodes(sw_name,sw_dst)[0]
                    next_hop = path[1] #next hop in shortest path.
                    sw_port = self.topo.node_to_node_port_num(sw_name, next_hop)
                    dst_sw_mac = self.topo.node_to_node_mac(next_hop, sw_name)
                    controller.table_add("ipv4_lpm", "set_nhop", [ip], [str(dst_sw_mac), str(sw_port)])

                    #routing towards hosts
                    if self.topo.get_hosts_connected_to(sw_dst):
                        paths = self.topo.get_shortest_paths_between_nodes(sw_name, sw_dst)
                        # assume this is the routing path given by administrator
                        path = paths[0]
                        for host in self.topo.get_hosts_connected_to(sw_dst):

                            next_hop = path[1]
                            host_ip = self.topo.get_host_ip(host) + "/24"
                            sw_port = self.topo.node_to_node_port_num(sw_name, next_hop)
                            dst_sw_mac = self.topo.node_to_node_mac(next_hop, sw_name)

                            #add rule
                            print("++++++++path:{} and ttl_needed:{}, host_ip:{}".format(path,len(path), str(host_ip)))
                            self.controllers[sw_name].table_add("ipv4_lpm", "set_nhop", [str(host_ip)],
                                                                [str(dst_sw_mac), str(sw_port)])




    def main(self):
        #print("----TOPO.node(s1): {}".format(self.topo.node('s1')))
        self.route()


if __name__ == "__main__":
    controller = RoutingController().main()
