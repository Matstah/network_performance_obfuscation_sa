action set_src_icmp_ip (bit<32> src_ip){
    //hdr.ipv4_icmp.srcAddr = src_ip;
    hdr.ipv4.srcAddr = src_ip;
}

table icmp_ingress_port {
    key = {
        standard_metadata.ingress_port: exact;
    }

    actions = {
        set_src_icmp_ip;
        NoAction;
    }
    size=64;
    default_action=NoAction;
}


//test with h1 traceroute -n -w 0.5 -q 1 -T --sport=63402 --port=80 10.8.5.2
