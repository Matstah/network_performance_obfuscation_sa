import sys
from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI
import math

class Node(object):
    # A node contains the following information:
    ### -The shortest path towards the target, used to cut of the depth first search
    ### -The minimum number of hops needed to get to the target
    ### -The Neighbours it is connected to.
    def __init__(self, sw_name, sw_target):
        self.topo = Topology(db="../topology.db")
        self.topo.network_graph.remove_node('sw-cpu')
        self.name = sw_name
        self.target = sw_target
        self.link_to = self.get_neighbours()
        self.link_cost = self.get_link_cost()
        self.min_hop_paths_to_target = self.get_min_hop_paths()
        self.min_hops_to_target = self.get_min_hops_count()
        self.delay_to_target = self.get_latency_of_paths()
        self.shortest_path = self.get_shortest_path_to_target()
        self.shortest_distance #set by get_shortest_path_to_target()..


    def get_neighbours(self):
        values = self.topo.get_interfaces_to_node(self.name).values()#
        values.remove('sw-cpu')
        return [val for val in values[:] if 'h' not in val]

    def get_link_cost(self):
        link_cost = {}
        for sw in self.link_to:
            link_cost[sw] = int(self.topo.node(self.name)[sw]['delay'].replace('ms',''))
        return link_cost

    def get_min_hop_paths(self):
        paths = sorted(self.topo.network_graph.get_all_simple_paths_between_nodes(self.name, self.target), key=len)
        if paths:
            len_first = len(paths[0])
        else:
            return [()]
        return [path for path in paths if len(path[:]) == len_first ]

    def get_min_hops_count(self):
        #print(self.min_hop_paths_to_target)
        #print(len(self.min_hop_paths_to_target[0]))
        if not self.min_hop_paths_to_target: # no path
            return [0]
        return [len(path)-1 for path in self.min_hop_paths_to_target] #-1 to get nr of hops needed for src header

    def get_shortest_path_to_target(self):
        shortest_path = []
        cost = 2000000000
        for path in self.topo.network_graph.get_all_simple_paths_between_nodes(self.name, self.target):
            path_cost = self.get_latency_of_path(path)
            if path_cost < cost:
                cost = path_cost
                shortest_path = path
        if not shortest_path:
            cost = 0
        self.shortest_distance = cost
        return shortest_path

    def get_latency_of_path(self, path):
        delay = 0
        for x, y in zip(path, path[1:]):
            #print("\nDelay between x:{}, y:{} is {}\n".format(x,y,self.topo.node(x)[y]['delay'].replace('ms','')))
            delay += int(self.topo.node(x)[y]['delay'].replace('ms',''))
        return delay

    def get_latency_of_paths(self):
        return [ self.get_latency_of_path(path) for path in self.min_hop_paths_to_target]

    def Print(self):
        print("\n------Node name: {}------".format(self.name))
        print("target: {}".format(self.target))
        print("link_to: {}".format(self.link_to))
        print("min_path_to_target: {}".format(self.min_hop_paths_to_target))
        print("min_hops_to_target: {}".format(self.min_hops_to_target))
        print("delay_to_target: {}ms\n".format(self.delay_to_target))


class Graph(object):
    # The Graph class translates the network topology into a graph with nodes from Node class.
    # search_best_path() then uses the correct latency routing algo and lets it find the best path with regard to target latency.
    #
    def __init__(self, ):
        self.topo = Topology(db="../topology.db")
        self.topo.network_graph.remove_node('sw-cpu') #used to set up switch routing, as we don't want to route over sw-cpu
        self.real_topo = Topology(db="../topology.db")
        self.sw_start = ''
        self.sw_target = ''
        self.nodes = {}
        self.max_hops = 10
        self.target_cost = 2000000000
        self.inf = 2000000000


    def print_nodes(self):
        for node in self.nodes:
            node.Print()

    #helper for search

    def nodes_as_dict(self,sw_s, sw_t):
        output = []
        for sw in self.topo.get_p4switches().keys():
            output.append(Node(sw, sw_t))
            #print("sw:{0}, short_dist:{1}".format(output[-1].name, output[-1].shortest_distance))
        #output = sorted(output, key=lambda x: x.shortest_distance, reverse=False)
        dict = {}
        for node in output:
            #print("name:{}, shrt_dist:{}".format(node.name, node.shortest_distance))
            dict[node.name] = node
        return dict

#Helper to remove nodes that we get best path on same path
    def search_best_path(self, type, sw_s, sw_t, target_length, max_hops ):
        best_path = []
        best_latency = 0
        best_cost = self.inf

        #self.remove_all_hosts_from_topo()
        if type == 'same_path': #does not work..
            switch_topo = self.topo
            #print("shortest paths: {}".format(self.topo.get_shortest_paths_between_nodes(sw_s,sw_t)))
            if sw_s == sw_t:
                best_path = [sw_s,sw_t]
                best_latency = 0
                best_cost = 0
            else:
                for path in self.topo.get_shortest_paths_between_nodes(sw_s, sw_t):
                    #print("NEW shortest path: {}".format(path))
                    same_path_latency, same_path, tar_len, cost = self.search_best_same_path(path, target_length, max_hops)
                    #if cost = 0, break
                    if cost < best_cost:
                        best_cost = cost
                        best_path = same_path
                        best_latency = same_path_latency
                        if best_cost == 0:
                            break

        elif type == 'simple_path': #works
            if sw_s == sw_t:
                best_path = [sw_s,sw_t]
                best_latency = 0
                best_cost = 0
            else:
                node = Node(sw_s, sw_t)
                for path in self.topo.network_graph.get_all_simple_paths_between_nodes(sw_s, sw_t):
                    path_length = node.get_latency_of_path(path)
                    cost = abs(target_length - path_length)
                    #print("cost:{}, path_length:{}".format(cost,path_length))
                    if cost < best_cost:
                        best_cost = cost
                        best_path = path
                        best_latency = path_length

        # called any path...
        elif type == 'loopy_path':
            best_path, best_latency, tar_len, cost = self.search_best_any_path(sw_s, sw_t, target_length, max_hops)

        return best_latency, best_path


    def remove_all_hosts_from_topo(self):
        for host in self.topo.get_hosts():
            #print("remove host {}".format(host))
            self.topo.network_graph.remove_node(host)

    def remove_all_unused_switches(self, path):
        used_sw = path
        for sw in self.topo.get_p4switches():
            if sw not in path:
                #print("---->{} is not in {}".format(sw, path))
                self.topo.network_graph.remove_node(sw)

    def search_best_same_path(self, path, target_length, depth):
        #precondition: path length must be smaller than depth
        cost = self.inf
        best_path =[]
        best_latency = 0
        link_pairs, link_cost = self.get_links_in_path(path)
        curr_path_length = sum(link_cost)
        curr_hop_count = len(link_pairs)
        #if cost is positive, below target. cost negative, above target
        curr_cost = target_length - curr_path_length
        depth = depth - curr_hop_count
        if curr_cost <= 0 or depth <2:
            return curr_path_length, path, target_length, curr_cost
        else: #target length is above current length.. add links to path
            link_pairs = [x for _,x in sorted(zip(link_cost,link_pairs), reverse=True)]
            link_cost.sort(reverse=True) # descending
            cost ,links_to_add = self.explore_path(curr_cost, target_length, link_pairs ,link_cost, depth)
            #print("------FINAL RESULT--- fo same path: cost:{}, links_to_add:{}".format(cost, links_to_add))
            #add links into path
            path = list(path) #change tuple to list for mutation
            #print("path:{}, links_to_add:{}".format(path,links_to_add))
            for link in links_to_add:
                i = path.index(link[0])
                link = list(link)
                rev_link = list(link)
                rev_link.reverse()
                #print("link:{}, rev_link:{}".format(link,rev_link))
                path = path[:i] + link + path[i:]

            #print("Links added to path: {}".format(path))
            node = Node(path[0], path[-1])
            best_latency = node.get_latency_of_path(path)
            best_path = path
            return best_latency, best_path, target_length, cost

    def get_links_in_path(self, path):
        link_pairs = []
        link_cost = []
        for x,y in zip(path, path[1:]):
            link_pairs.append((x,y))
            link_cost.append(int(self.topo.node(x)[y]['delay'].replace('ms','')))
        #print("link_pairs:{} and link_cost:{}".format(link_pairs, link_cost))
        return link_pairs, link_cost

    def explore_path(self, best_cost, target_length, link_pairs ,link_cost, depth):
        #print("Explore_deeper, with depth:{} and best_cost:{}".format(depth, best_cost))
        #precondition: link_pairs are sorted by link cost, descending
        #precondition: curr_cost <= 0
        #pick depth/2 many link-pairs with cost closest to target
        #stop conditions
        nr_of_links_to_add = int(depth)/2
        if nr_of_links_to_add == 0:
            #print("return: best_cost:{}, best_link_pairs: []".format(best_cost))
            return best_cost, []

        else:
            best_link_pairs = []
            curr_best_cost = best_cost
            #link_pairs are sorted by biggest link first.. will allways add max link to reach target as fast as possible
            for i, link in enumerate(link_pairs):
                #print("consider link: {} with cost 2*{}ms, depth: {},best_cost:{} curr_best_cost:{}".format(link, link_cost[i], depth, best_cost, curr_best_cost))
                curr_cost = self.inf
                curr_link_pairs = []
                #cost = taget_length - path_length
                if curr_best_cost - 2*link_cost[i] > 0:
                    #print("Condition1")
                    curr_cost, curr_link_pairs  = self.explore_path(curr_best_cost-2*link_cost[i], target_length, link_pairs, link_cost, depth-2)
                    curr_link_pairs = [link] + curr_link_pairs
                elif abs(curr_best_cost) > abs(best_cost - 2*link_cost[i]):
                    #link is above target.. but has less cost-> take it
                    #update link and best cost
                    #print("Condition 2")
                    curr_cost = best_cost - 2*link_cost[i]
                    curr_link_pairs = [link]
                    #print("Consdition 2, curr_cost:{}, curr_link_pairs:{}".format(curr_cost, curr_link_pairs))
                else:
                    #print("Condition 3")
                    pass #this link is not good, look at next

                #evaluate each branch:
                if abs(curr_cost) < abs(curr_best_cost):
                    #print("update best_cost to {} and best_link_pairs to {}".format(curr_cost, curr_link_pairs))
                    curr_best_cost = curr_cost
                    best_link_pairs = curr_link_pairs

            best_cost = curr_best_cost
            #print("return: best_cost:{}, best_link_pairs{}".format(best_cost, best_link_pairs))
            return best_cost, best_link_pairs


       #recursion

       #pick the link that brings us closest to target



#SEARCH ALGO
    def search_best_any_path(self, sw_s, sw_t, target_length, max_hops):
        #precondition, sw cannot be a host!
        #print("\n-----search started: sw_start:{}, sw_target:{}-----".format(sw_s, sw_t))
        #set all nodes based on s and t:
        self.nodes = self.nodes_as_dict(sw_s, sw_t)
        self.max_hops = max_hops
        self.target_cost = target_length
        best_path = []
        depth = max_hops
        min_cost = self.inf

        #check reachability condition:
        link_cost = self.nodes[sw_s].link_cost # link names
        next_sw = min(link_cost.items(), key=lambda x: x[1]) #get sw name of mallest link
        if not self.nodes[sw_s].shortest_distance < self.target_cost and not self.target_cost == 0:
            #print("fail 1")
            best_path = self.nodes[sw_s].shortest_path
            path_length = self.nodes[sw_s].shortest_distance
            target_length = self.target_cost
            best_cost = abs(self.target_cost - path_length)
            #print("best_path:{}, path_len:{}, tar_cost:{}, best_cost:{}".format(best_path, path_length, target_length,best_cost))
        elif sw_s == sw_t and self.target_cost < 1.5 * next_sw[1] or  max_hops < 2:
            #print("fail 2")
            if self.target_cost < next_sw[1] or  max_hops < 2:
                #print("fail 3")
                best_path = [sw_s, sw_s]
                path_length = 0
                target_length = self.target_cost
                best_cost = abs(self.target_cost - path_length)

            else:
                #print("fail 4")
                best_path = [sw_s, next_sw[0], sw_t]
                path_length = 2*next_sw[1]
                target_length = self.target_cost
                best_cost = abs(self.target_cost - path_length)
        else:
            #start recursion                       #length, depth, min_cost, node
            best_cost, best_path = self.go_search_deeper(0, depth, min_cost, self.nodes[sw_s])
            path_length = self.nodes[sw_s].get_latency_of_path(best_path)

        #print results
        #cost, best_path = self.go_deeper(start_state, depth, 0)
        if sw_t not in best_path:
            best_path = 'ERROR: target not reached in {} steps'.format(depth)
            path_length = 'ERROR: target not reached in {} steps'.format(depth)
            target_length = 'ERROR: target not reached in {} steps'.format(depth)
            best_cost = ' ERROR: target not reached in {} steps'.format(depth)

        #print("------------------------------------\nALPHA_BETA_Terminated. Results: \ncost:{}".format(best_cost))
        #print("best_path: {}".format(best_path))
        #print("path_length:{}".format(path_length))
        #print("target_length".format(target_length))
        #print("best_cost / diff to target:{}".format(best_cost))
        #print("------------------------------------\n")
        return best_path, path_length, target_length, best_cost




    def go_search_deeper(self, length, depth, min_cost, node):
        string = ''
        for i in range(self.max_hops - depth):
            string += '-'
        string += '>'
        #print("{0}go_deeper() on state:{1}, with min_cost{2}, length S->{1}:{3}, depth:{4}".format(string, node.name, min_cost, length, depth))

        #save path from this node, value to return at the end
        best_path = []
        curr_cost = abs(self.target_cost-length)

        #stop conditions: at sw_target with no hops left
        #check if cost is needed..
        if (depth == 1 or depth == 0 or (curr_cost==0)) and node.name == node.target:
            #print("Condition final state: depth:{}, name:{}".format(depth, node.name))
            dist_to_target = abs(self.target_cost - length)
            if min_cost >= dist_to_target:
                #current path is better than previous
                min_cost = dist_to_target
                best_path = [node.name]
            else:
                min_cost = self.inf
                best_path = []
            #print("<--return(Condition final state) from {} depth:{}: min_cost{}".format(node.name, depth, min_cost))
            return min_cost, best_path

        # are on target, above target cost, but under or equal to min_cost.. take it!
        if node.name == node.target:
            if self.target_cost < length:
                #print("on target node, but above target value")
                if curr_cost <= min_cost:
                    #print("better than min_cost, update & return")
                    #print("<--return({})(target node, but better than current): cost:{}, path:{}".format(node.name, curr_cost, [node.name]))
                    return curr_cost, [node.name]
                else:
                    #print("worse than best")
                    #print("<--return({})(target node, worse than best: cost{}, path{})".fomat(node.name, min_cost,[]))
                    return self.inf, []

        # if need to return due to hops, ams shortest is above best, and largest is above best, drop
        if depth == node.min_hops_to_target[0]:
            #print("x_Condition out of hops: depth:{}, name:{}".format(depth, node.name))
            #check if any hop path is better, if yes return, else drop
            updated = False
            for i, path in enumerate(node.min_hop_paths_to_target):
                path_cost = abs(self.target_cost -length -node.delay_to_target[i])
                #print("For_loop: dist_to_target:{} <= min_cost:{}; path:{}".format(path_cost, min_cost, path))
                if path_cost <= min_cost:
                    updated = True
                    min_cost = path_cost
                    best_path = path
            if not updated:
                min_cost = self.inf
                best_path = []
            #print("<--return(Condition hops) from {} depth{}: min_cost:{}, best_path:{}".format(node.name, depth, min_cost, list(best_path) ))
            return min_cost, list(best_path) #best_path includes this and end


        # overshoot condition.. should actually be precondition.. extra savety
        if length + node.shortest_distance > self.target_cost + min_cost:
            if node.target == node.shortest_path[1] and len(node.shortest_path) == 2: #next switch == target
                #print("Overshoot, but next is the target")
                return abs(self.target_cost -length - node.shortest_distance), node.shortest_path
            #dist to target will only increase.. so we stop
            #print("Overshoot with shortest path: lenght:{}, short_dist:{}, shrt_path:{}, min_cost:{}".format(length, node.shortest_distance, node.shortest_path, min_cost))
            return self.inf, []


        #move deeper...
        depth -= 1
        cost_updates = False
        #sort link by shortest path to target first.. monotonic approach to target_cost
        node.link_to = sorted(node.link_to, key=lambda x: self.nodes[x].shortest_distance, reverse=False)

        #check neigbour switches/nodes
        for next_sw in node.link_to:
            #print("{} consider {}".format(node.name, next_sw))
            next_node = self.nodes[next_sw]

            #to keep bound on distance from target. Always consider steps needed to target
            if depth < next_node.min_hops_to_target[0]:
                continue #can not reach target in depth number of steps
                #print("condition 1: Run out of hops")

            link_cost = node.link_cost[next_sw]
            #shortest_dist_to_target allows to checks if target can be reached with better cost
            shortest_dist_to_target = length + link_cost + next_node.shortest_distance


            if shortest_dist_to_target >= self.target_cost + min_cost:
                #cutoff, cost will strictly monotonically increase
                #print("--skip next_node {}. shortest_dist_to_target:{} > upper_bound{} = True".format(next_sw,shortest_dist_to_target, self.target_cost+min_cost))
                continue ##skip this neighbour/next_node
            elif abs(self.target_cost - shortest_dist_to_target) > min_cost:
                # must be below self.target_cost - min_cost=lower bound.. explore
                #print("below lower_bound")
                pass
            else: #lower than upper bound, higher than lower bound, explore
                #print("closer to target cost")
                ## update cost
                #min_cost = abs(self.target_cost - shortest_dist_to_target)
                min_cost = abs(self.target_cost-length-link_cost)

            #recursion
            next_length = length + link_cost
            #print("recurstion")
            new_dist, path_to_add = self.go_search_deeper(next_length, depth, min_cost, next_node)
            #print("{}|| :new_dist:{}, path_to_add:{}".format(node.name, new_dist, path_to_add))

            #only update values if they are better..
            if new_dist < min_cost or len(best_path)==0:#(new_dist<self.inf and len(best_path) == 0):
                #if this newer true, then all neigbours are bad, so return inf
                cost_updates = True
                #print("update min_cost{} by new_dist{}".format(min_cost, new_dist))
                min_cost = new_dist
                best_path = path_to_add
                #stop explore if we have found best solution
                if min_cost == 0:
                    #print("min_cost = 0")
                    break
        best_path = [node.name] + list(best_path)
        if not cost_updates and node.name == node.target:
            #print("Stop & return terminal node, as all moves away from target increase cost")
            best_path = [node.name]
        elif not cost_updates:
            min_cost = self.inf
            best_path = []
        #print("<-return: go_deeper() on {} from depth:{}: min_cost:{}, best_path:{}".format(node.name,depth,min_cost,best_path))
        return min_cost, best_path

#if __name__ == "__main__":

    #node = Node('s8', 's1')
    #node.Print()

    #graph = Graph()

#TEST CASES FOR GRAPH: FINDING PATHS TO CLOSEST COSTS..
    ## tests if we can find closest value above the target value
    #graph.search_best_any_path('s1', 's8', 100, 8) #best cost: 105
    ## tests if we get path closest to target value under limited hops
    #graph.search_best_any_path('s1', 's8', 100, 3)
    ## tests if corner case for one hop works
    #graph.search_best_any_path('s1', 's2', 20, 8)
    ## tests if onli considers valid paths
    #graph.search_best_any_path('s1', 's2', 100, 8)
    ## tests if we can loop on link to reach specific cost
    #graph.search_best_any_path('s1', 's2', 120, 5)
    ## tests if it finds the closest larger link and stays on it
    #graph.search_best_any_path('s1', 's2', 200, 5)
    ## tests if it finds the closest larger link and stays on it, but trades of if other path might be better
    #graph.search_best_any_path('s1', 's2', 200, 4)
    ## tests if get a path backwards to same node..
    #graph.search_best_any_path('s1', 's1',50 , 1)
    ## tests if this really works...:
    #graph.search_best_any_path('s1', 's1',50 , 3)
    #graph.search_best_any_path('s1', 's1',35 , 3)
    #graph.search_best_any_path('s1','s1',120,10)
    #graph.search_best_any_path('s1', 's1', 29 , 3)
    #graph.search_best_any_path('s1', 's1', 50, 1)# need at least 2 hops..
    #graph.search_best_any_path('s1', 's1', 50, 2)
    #graph.search_best_any_path('s1', 's1', 19 , 2)# 18 = shortest link is 20..
    #graph.search_best_any_path('s1', 's2', 18, 1)
    #graph.search_best_any_path('s1','s1',1, 10) #this works.. returns same switch
    #graph.search_best_any_path('s1','s1',0,10) #this works.. returns same switch
    #for short distances with overshoot or undershoot of goal:
    #graph.search_best_any_path('s1','s8',120,10) #return length 115
    #graph.search_best_any_path('s1','s2', 45, 10)
    #graph.search_best_any_path('s1','s2', 30, 10)
    #graph.search_best_any_path('s1','s2', 40, 10) #one path is 20, one is 60.. in the middle, should pick upper

    ## tests finds shortest path
    #graph.search_best_any_path('s7', 's5', 10, 8)
    ## tests less hops than shortest path
    #graph.search_best_any_path('s1', 's8', 65, 2) #should just return shortest path..

    #find longest path
    #graph.search_best_any_path('s1','s8',graph.inf,10)

    #scalabile?? no, exploads... 13-14 takes way longer..
    #graph.search_best_any_path('s1','s8',graph.inf,14)

    #weard behaviour found:
    #graph.search_best_any_path('s1','s5',80 ,10) #returns 100, should 80
    #graph.search_best_any_path('s1','s6',140 ,10) #returns 100, should 80
