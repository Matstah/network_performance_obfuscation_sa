# SA-2019-04_Network_Performance_Obfuscation

Semester Thesis of Matthias Stähli, Spring 2019

mstaehli@ethz.ch

# File Organization
The main README is `Project/README.md` where you can test the project immediately and get a lot of information as well.

<pre>
**reduced view**
├── Project
│   ├── **see below**
├── Evaluation
|   ├── **see below**
├── Presentation
└── Report
</pre>

## Project
See comments enclosed in \*.
<pre>

├── controller                            *main controllers*
|   ├── routing_controller.py             *takes care of normal ipv4 routing*

|   ├── obfuscation_controller.py         *calculates and sets obfuscation rules*
|   ├── iperf_detector.py                 *helper to the obfuscation-controller
                                           to stock the iperf classification tables*
|   ├── Input_parser.py                   *handling the command line interface
                                           to add new obfuscation rules. Validates
                                           and calculates obfuscation rules for the
                                           obfuscation controller.*
|   └── Graph_algo.py                     *Contains all algorithms used to find
                                           path with latency closest to the
                                           target latency.

├── p4src                                 *P4 program for performance obfuscation*
                                          *we have split the program into files
                                          according to functionality*
│   ├── pipeline.p4                       *basic file that "includes" the others*
│   ├── include
│   │   ├── headers.p4                    
│   │   └── parsers.p4
│   └── ingress
│       ├── src_routing.p4
│       ├── traceroutable.p4
│       ├── rate_limiting_with_meters.p4
│       ├── ipv4_routing.p4
│       └── iperf_classification.p4

├── log                                   *contains log files for debugging*
├── pcap                                  *contains log files for debugging*

├── Utils                                 *Utils contains TopoHelper which
                                          gathers some useful information about
                                          the topology.*

├── p4app.json                            *Default setup and topoloy for p4run*

├── bw_evaluation_topo.json               *Setup and topoloy used to evaluate
                                          the bandwidth obfuscation*

└── topology.db                           *created by p4run*  

</pre>

## Evaluation
Contains the scripts and data used to make the evaluation plots.
<pre>
**reduced view**
├── Packet loss obfuscation
│      ├── plots
│      ├── data
│      └── evaluate_loss.py
|
├── Latency obfuscation
|         ├── Latency_routing
|                   ├── plots
|                   ├── topos
|                   ├── evaluate_topo.py
|                   └── best_path_finder.py         *helper for evaluate_topo.py*
|         └── Traceroute_example
|                   ├── plots
|                   ├── data
|                   └── plot_traceroute.py

└── Throughput obfuscation
|   ├── plots
|   ├── data
|   └── bw_evaluation.py
</pre>
