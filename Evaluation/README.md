
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
|                   ├── evaluate_topo.py              *contains the function to look at the accuracy of latency routing
                                                                           and the function to compare different networks.*
|                   └── best_path_finder.py         *evaluate_topo.py*
|         └── Traceroute_example
|                   ├── plots
|                   ├── data
|                   └── plot_traceroute.py

└── Throughput obfuscation
|   ├── plots
|   ├── data
|   └── bw_evaluation.py
</pre>
