/******** All functions for ipv4 routing********/

/*
//IP routing at network edge
action drop() {
    mark_to_drop();
}

action set_nhop(macAddr_t dstAddr, egressSpec_t port) {

    //set the src mac address as the previous dst, this is not correct right?
    hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;

   //set the destination mac address that we got from the match in the table
    hdr.ethernet.dstAddr = dstAddr;

    //set the output port that we also get from the table
    standard_metadata.egress_spec = port;

    //decrease ttl by 1
    hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
}
*/

//routing based on src header
action srcRoute_nhop() {
    standard_metadata.egress_spec = (bit<9>)hdr.srcRoutes[0].port;
    hdr.srcRoutes.pop_front(1); // pops one from stack..
}

action srcRoute_finish() {
    hdr.ethernet.etherType = TYPE_IPV4;
}


//setup of src routing header
//action set_nhop(macAddr_t dstAddr, egressSpec_t port) defined in traceroute..
action hop0(bit<4> ttl, bit<9> port0){
    standard_metadata.egress_spec = port0;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;
    meta.src_routing = 1;
}

action hop1(bit<4> ttl, bit<9> port0, bit<7> port) {
    standard_metadata.egress_spec = port0;
    hdr.ethernet.etherType = TYPE_SRCROUTING;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;

    hdr.srcRoutes[0].setValid();
    hdr.srcRoutes[0].port = port;
    hdr.srcRoutes[0].bos = 1;
}

action hop2(bit<4> ttl, bit<9> port0, bit<7> port1, bit<7> port2) {
    hdr.ethernet.etherType = TYPE_SRCROUTING;
    standard_metadata.egress_spec = port0;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;

    hdr.srcRoutes[0].setValid();
    hdr.srcRoutes[0].port = port1;
    hdr.srcRoutes[0].bos = 0;

    hdr.srcRoutes[1].setValid();
    hdr.srcRoutes[1].port = port2;
    hdr.srcRoutes[1].bos = 1;
}

action hop3(bit<4> ttl, bit<9> port0, bit<7> port1, bit<7> port2, bit<7> port3) {
    hdr.ethernet.etherType = TYPE_SRCROUTING;
    standard_metadata.egress_spec = port0;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;

    hdr.srcRoutes[0].setValid();
    hdr.srcRoutes[0].port = port1;
    hdr.srcRoutes[0].bos = 0;

    hdr.srcRoutes[1].setValid();
    hdr.srcRoutes[1].port = port2;
    hdr.srcRoutes[1].bos = 0;

    hdr.srcRoutes[2].setValid();
    hdr.srcRoutes[2].port = port3;
    hdr.srcRoutes[2].bos = 1;
}

action hop4(bit<4> ttl, bit<9> port0, bit<7> port1, bit<7> port2, bit<7> port3, bit<7> port4) {
    hdr.ethernet.etherType = TYPE_SRCROUTING;
    standard_metadata.egress_spec = port0;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;

    hdr.srcRoutes[0].setValid();
    hdr.srcRoutes[0].port = port1;
    hdr.srcRoutes[0].bos = 0;

    hdr.srcRoutes[1].setValid();
    hdr.srcRoutes[1].port = port2;
    hdr.srcRoutes[1].bos = 0;

    hdr.srcRoutes[2].setValid();
    hdr.srcRoutes[2].port = port3;
    hdr.srcRoutes[2].bos = 0;

    hdr.srcRoutes[3].setValid();
    hdr.srcRoutes[3].port = port4;
    hdr.srcRoutes[3].bos = 1;
}

action hop5(bit<4> ttl, bit<9> port0, bit<7> port1, bit<7> port2, bit<7> port3, bit<7> port4, bit<7> port5) {
    hdr.ethernet.etherType = TYPE_SRCROUTING;
    standard_metadata.egress_spec = port0;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;

    hdr.srcRoutes[0].setValid();
    hdr.srcRoutes[0].port = port1;
    hdr.srcRoutes[0].bos = 0;

    hdr.srcRoutes[1].setValid();
    hdr.srcRoutes[1].port = port2;
    hdr.srcRoutes[1].bos = 0;

    hdr.srcRoutes[2].setValid();
    hdr.srcRoutes[2].port = port3;
    hdr.srcRoutes[2].bos = 0;

    hdr.srcRoutes[3].setValid();
    hdr.srcRoutes[3].port = port4;
    hdr.srcRoutes[3].bos = 0;

    hdr.srcRoutes[4].setValid();
    hdr.srcRoutes[4].port = port5;
    hdr.srcRoutes[4].bos = 1;
}

action hop6(bit<4> ttl, bit<9> port0, bit<7> port1, bit<7> port2, bit<7> port3, bit<7> port4, bit<7> port5, bit<7> port6) {
    hdr.ethernet.etherType = TYPE_SRCROUTING;
    standard_metadata.egress_spec = port0;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;

    hdr.srcRoutes[0].setValid();
    hdr.srcRoutes[0].port = port1;
    hdr.srcRoutes[0].bos = 0;

    hdr.srcRoutes[1].setValid();
    hdr.srcRoutes[1].port = port2;
    hdr.srcRoutes[1].bos = 0;

    hdr.srcRoutes[2].setValid();
    hdr.srcRoutes[2].port = port3;
    hdr.srcRoutes[2].bos = 0;

    hdr.srcRoutes[3].setValid();
    hdr.srcRoutes[3].port = port4;
    hdr.srcRoutes[3].bos = 0;

    hdr.srcRoutes[4].setValid();
    hdr.srcRoutes[4].port = port5;
    hdr.srcRoutes[4].bos = 0;

    hdr.srcRoutes[5].setValid();
    hdr.srcRoutes[5].port = port6;
    hdr.srcRoutes[5].bos = 1;
}

action hop7(bit<4> ttl, bit<9> port0, bit<7> port1, bit<7> port2, bit<7> port3, bit<7> port4, bit<7> port5, bit<7> port6, bit<7> port7) {
    hdr.ethernet.etherType = TYPE_SRCROUTING;
    standard_metadata.egress_spec = port0;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;

    hdr.srcRoutes[0].setValid();
    hdr.srcRoutes[0].port = port1;
    hdr.srcRoutes[0].bos = 0;

    hdr.srcRoutes[1].setValid();
    hdr.srcRoutes[1].port = port2;
    hdr.srcRoutes[1].bos = 0;

    hdr.srcRoutes[2].setValid();
    hdr.srcRoutes[2].port = port3;
    hdr.srcRoutes[2].bos = 0;

    hdr.srcRoutes[3].setValid();
    hdr.srcRoutes[3].port = port4;
    hdr.srcRoutes[3].bos = 0;

    hdr.srcRoutes[4].setValid();
    hdr.srcRoutes[4].port = port5;
    hdr.srcRoutes[4].bos = 0;

    hdr.srcRoutes[5].setValid();
    hdr.srcRoutes[5].port = port6;
    hdr.srcRoutes[5].bos = 0;

    hdr.srcRoutes[6].setValid();
    hdr.srcRoutes[6].port = port7;
    hdr.srcRoutes[6].bos = 1;
}

action hop8(bit<4> ttl, bit<9> port0, bit<7> port1, bit<7> port2, bit<7> port3, bit<7> port4, bit<7> port5, bit<7> port6, bit<7> port7, bit<7> port8) {
    hdr.ethernet.etherType = TYPE_SRCROUTING;
    standard_metadata.egress_spec = port0;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;

    hdr.srcRoutes[0].setValid();
    hdr.srcRoutes[0].port = port1;
    hdr.srcRoutes[0].bos = 0;

    hdr.srcRoutes[1].setValid();
    hdr.srcRoutes[1].port = port2;
    hdr.srcRoutes[1].bos = 0;

    hdr.srcRoutes[2].setValid();
    hdr.srcRoutes[2].port = port3;
    hdr.srcRoutes[2].bos = 0;

    hdr.srcRoutes[3].setValid();
    hdr.srcRoutes[3].port = port4;
    hdr.srcRoutes[3].bos = 0;

    hdr.srcRoutes[4].setValid();
    hdr.srcRoutes[4].port = port5;
    hdr.srcRoutes[4].bos = 0;

    hdr.srcRoutes[5].setValid();
    hdr.srcRoutes[5].port = port6;
    hdr.srcRoutes[5].bos = 0;

    hdr.srcRoutes[6].setValid();
    hdr.srcRoutes[6].port = port7;
    hdr.srcRoutes[6].bos = 0;

    hdr.srcRoutes[7].setValid();
    hdr.srcRoutes[7].port = port8;
    hdr.srcRoutes[7].bos = 1;
}

action hop9(bit<4> ttl, bit<9> port0, bit<7> port1, bit<7> port2, bit<7> port3, bit<7> port4, bit<7> port5, bit<7> port6, bit<7> port7, bit<7> port8, bit<7> port9) {
    hdr.ethernet.etherType = TYPE_SRCROUTING;
    standard_metadata.egress_spec = port0;
    hdr.ipv4.ttl = hdr.ipv4.ttl - (bit<8>)ttl;

    hdr.srcRoutes[0].setValid();
    hdr.srcRoutes[0].port = port1;
    hdr.srcRoutes[0].bos = 0;

    hdr.srcRoutes[1].setValid();
    hdr.srcRoutes[1].port = port2;
    hdr.srcRoutes[1].bos = 0;

    hdr.srcRoutes[2].setValid();
    hdr.srcRoutes[2].port = port3;
    hdr.srcRoutes[2].bos = 0;

    hdr.srcRoutes[3].setValid();
    hdr.srcRoutes[3].port = port4;
    hdr.srcRoutes[3].bos = 0;

    hdr.srcRoutes[4].setValid();
    hdr.srcRoutes[4].port = port5;
    hdr.srcRoutes[4].bos = 0;

    hdr.srcRoutes[5].setValid();
    hdr.srcRoutes[5].port = port6;
    hdr.srcRoutes[5].bos = 0;

    hdr.srcRoutes[6].setValid();
    hdr.srcRoutes[6].port = port7;
    hdr.srcRoutes[6].bos = 0;

    hdr.srcRoutes[7].setValid();
    hdr.srcRoutes[7].port = port8;
    hdr.srcRoutes[7].bos = 0;

    hdr.srcRoutes[8].setValid();
    hdr.srcRoutes[8].port = port9;
    hdr.srcRoutes[8].bos = 1;
}

table path_id_to_path {
    key = {
        meta.path_id : exact;
    }
    actions = {
        NoAction;
        hop0;
        hop1;
        hop2;
        hop3;
        hop4;
        hop5;
        hop6;
        hop7;
        hop8;
        hop9;
    }
}
