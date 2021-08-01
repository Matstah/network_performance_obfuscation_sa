/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>


/************   C O N S T A N T S  AND H E A D E R S *************/


#include "include/headers.p4"
#include "include/parsers.p4"

#define IP_ICMP_PROTO 1
#define ICMP_TTL_EXPIRED 11
//#define TIMESTAMP_WIDTH 48
//#define NR_OF_PORTS 20
//#define NR_BITS_FOR_AVERAGE_COUNTER 2 //wide for counter = 2 bit: 0,1,2,3 possible, then overflow
//#define NR_RTT_CELLS_FOR_AVERAGE_MEASUREMENT 80 //4*20 = 80, each port needs to track 4 rtt'mes, that will be used to calculate average rtt
#define iperf_bloom_cells 1024
#define iperf_sm_cells 1024

typedef bit<2> meter_color_t;

const bit<32> meter_length = 16384;


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {

    apply {
    }
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

// INCLUDES
#include "ingress/ipv4_routing.p4"
#include "ingress/src_routing.p4"
#include "ingress/iperf_classification.p4"
#include "ingress/traceroutable.p4"
#include "ingress/rate_limiting_with_meters.p4"


// Functions to match obfuscation rules and set parameters.
action set_types(){
    //traceroute = type 1
    meta.ping = 0; //type 2
    meta.iperf = 0; // type 3
    meta.tcp = 0; // type 4
    meta.udp = 0; // type 5
    meta.ipv4 = 0; // type 6
}
action set_parameters(bit<3> obf_type ,bit<8> path_id, bit<4>ttl_to_subtract ,bit<10> pack_loss, bit<16> bw){
    meta.obf_type = obf_type;
    meta.path_id = path_id;
    //meta.w_size = w_size;
    meta.ttl_to_subtract = ttl_to_subtract;
    meta.pack_loss_rate = pack_loss;
    //meta.meter_id = meter_id;
    meta.bw = bw;
}
table consider_flow {
    //if destination is consideret, match them with types set in consider_srcAddr.
    key = {
        hdr.ipv4.srcAddr : range;
        hdr.ipv4.dstAddr : range;
        meta.ping : ternary; //type 2
        meta.iperf : ternary; // type 3
        meta.tcp : ternary; // type 4
        meta.udp : ternary; // type 5
        meta.ipv4 : ternary; // type 6
        hdr.ipv4.ttl : ternary; //traceroute, zype 1
    }
    actions = {
        NoAction;
        set_parameters;
    }
}


    apply {

        /************* Routing ***********/
        // srcRouting Header received, forward respectively- nothing else.
        if(hdr.srcRoutes[0].isValid()){
            if(hdr.srcRoutes[0].bos == 1) { //bos: bottom of stack
                srcRoute_finish();
            }
            // Pop's srcRoutes[0] and sets egress port
            srcRoute_nhop();
            return;
        }//END srcRoute



        /************* CLASSIFY TRAFFIC TYPE ***********/
        // initiate variables for classification
        set_types();

        // classify ipv4
        if(hdr.ipv4.isValid()){
            meta.ipv4 = 1;
        }

        // classify ping packets
        if(hdr.icmp.isValid() && hdr.icmp.type == 8 && hdr.icmp.code == 0){
            //echo type = 8, code = 0 ==> ping request
            meta.ping = 1;
        }else{
            meta.ping = 0;
        }

        // classify UDP
        if(hdr.ipv4.protocol == 17){
            // UDP
            meta.udp = 1;
        }else{
            meta.udp = 0;
        }

        // classify TCP, classify iperf
        if(hdr.tcp.isValid()){
            meta.tcp = 1;

            // Check packet for default iperf values.
            if(hdr.tcp.dstPort == 5001 || hdr.tcp.dstPort == 5201){
                //iperf and iperf3 default port
                meta.iperf = 1;
            }else if(hdr.payload.isValid()){
                //check payload for 0123456789 //default input for iperf v1
                parse_payload();
                if(iperf_payload.apply().hit){
                    //default iperf1 payload of 0123456789 repeating..
                    meta.iperf = 1;}
            }


            if(meta.iperf == 0){
                //Packet has no default iperf values, check counting filter for mark.
                calc_index_iperf_blom();
                read_iperf_bloom();
                if(meta.b_value1 > 0 && meta.b_value2 > 0){
                    //Flow in iperf Bloom filter
                    if(hdr.tcp.syn == 1 && hdr.tcp.ack == 0){
                        // restart to classify new flow, packet cannot belong to iperf flow.
                        remove_entry_in_iperf_bloom_filter();
                        calc_index_iperf_sm();
                        set_sm_to_start_state();
                        store_tcp_mss();
                        meta.iperf = 0;

                    }else if(hdr.tcp.rst == 1 || hdr.tcp.fin == 1){
                        // end of iperf flow, remove from bloom filter
                        remove_entry_in_iperf_bloom_filter();
                        meta.iperf = 1;
                    }else{
                        // packet belongs to marked iperf flow
                        meta.iperf = 1;}

                }else{
                    //Flow NOT in iperf bloom filter
                    calc_index_iperf_sm();
                    read_iperf_sm_state();
                    if(hdr.tcp.syn == 1 && hdr.tcp.ack == 0){
                        //start sm to classify new flow
                        set_sm_to_start_state(); //state<-0
                        store_tcp_mss();

                    }else if(meta.sm_state == 3){
                        // in default state. Stay there.
                        meta.iperf = 0;

                    }else if(meta.sm_state == 0){
                        //in start state
                        if(hdr.tcp.ack == 1 && !hdr.payload.isValid()){
                            //Ack response to SynAck from iperf server.
                            set_sm_to_handshake_completed_state(); //state<-1
                        }else{
                            set_sm_to_default_state();} //state<-3

                    }else if(meta.sm_state == 1){
                        //in handshake completed state
                        if(hdr.tcp.ack == 1 && hdr.tcp.psh == 1 && (meta.tcp_payload_len == 24 || meta.tcp_payload_len == 37)){
                            //24 bytes for iperf header, 37bytes for iperf3 header
                            //store_iperf_flow_id();
                            set_sm_to_id_send_state(); //state<-2
                        }else{
                            set_sm_to_default_state();} //state<-3

                    }else if(meta.sm_state == 2){
                        //in iperf header send state
                        set_sm_to_default_state(); //reset sm for new flows anyways..// state<-3
                        read_tcp_mss_from_storage();
                        bit<16> mss = meta.tcp_mss - (((bit<16>)hdr.tcp.dataOffset-5) * 4);

                        if(meta.tcp_payload_len == mss || meta.tcp_payload_len == 1446 || meta.tcp_payload_len == 9448){
                            // iperf1 & iperf3 send maximum sized packet.
                            set_entry_in_iperf_bloom_filter();
                            meta.iperf = 1;
                        }
                    }
                }
            }//END iperf classification
        }else{
            meta.tcp = 0;
        }//END tcp classification


        ///// All Flows Are Now Classified


        // Match classified packet with obfuscation rules
        if(consider_flow.apply().hit){

            // Obfuscate packet by given parameters..
            bit<8> switches_traversed = (bit<8>)meta.ttl_to_subtract + 1;
            if((switches_traversed < hdr.ipv4.ttl) || meta.obf_type == 1){
                // traceroute packet only enter here when they have to be obfuscated.

                // whaaaat?---> because traceroute is tcp,
                //and therefore would create problems when considering tcp.. same for UDP

                // SET SOURCE ROUTING HEADER FOR PATH/LATENCY MANIPULATION
                path_id_to_path.apply();
                //substract correct ttl!

                // SET PACKET LOSS
                if (meta.pack_loss_rate == 0){
                    // no packet loss
                }else{
                    bit<10> probability;
                    random(probability, 10w1, 10w1000); //get random number inrange [1,100], inclusive
                    if (probability <= meta.pack_loss_rate) {  //random uniformly distributed..
                        drop();
                        return;
                    }
                }

                // SET THROUGHPUT VARIABLES
                if(meta.bw == 0){
                    //don't change bandwidth
                }else{
                        // find meter counter belonging to packet
                        calc_meter_index();
                        // next, update responsible meter
                        meter_id_to_meter_read.apply();
                        //drops packet if rate exceeded
                        m_filter.apply();
                }
            }else{
                // Packet is a traceroute packet, but there is no rule for it
                // it will be drop inside our network, but traceroute is not considered so we leave it pass
                // This allows us to obfuscate udp/ tcp traffic for the destination
                // without having any influence on the traceraute (might also be udp/tcp).
                meta.src_routing = 0;
            }
        }//end if(rule == matched)

        // No rule for (src,dst) flow, handle as normal ipv4 traffic.
        if (meta.src_routing == 0 && !hdr.srcRoutes[0].isValid()){

            // Traceroute response
            if (hdr.ipv4.isValid() && (hdr.ipv4.ttl == 1 || hdr.ipv4.ttl ==0) ){ //==0 will be from routed packet.. ignored by consider_flow table
                hdr.ipv4.ttl =1; //hack, correction

                // Set new headers valid
                hdr.ipv4_icmp.setValid();
                hdr.icmp.setValid();

                // Set egress port == ingress port
                standard_metadata.egress_spec = standard_metadata.ingress_port;

                //Ethernet: Swap map addresses
                bit<48> tmp_mac = hdr.ethernet.srcAddr;
                hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
                hdr.ethernet.dstAddr = tmp_mac;

                //Building new Ipv4 header for the ICMP packet
                // By keeping ipv4_icmp as old and change ipv4 to new
                //Copy original header (for simplicity)
                hdr.ipv4_icmp = hdr.ipv4;
                //Set destination address as traceroute originator
                hdr.ipv4.dstAddr = hdr.ipv4_icmp.srcAddr;
                //Set src IP to the IP assigned to the switch interface
                icmp_ingress_port.apply(); //set by routing-controller

                //Set protocol to ICMP
                hdr.ipv4.protocol = IP_ICMP_PROTO;
                //Set default TTL
                hdr.ipv4.ttl = 65; //will result in 64 after ipv4_lpm table

                //Create ICMP header with, unused stais unused
                hdr.icmp.type = ICMP_TTL_EXPIRED;
                hdr.icmp.code = 0;

                //set icmp Data // reuse meta header
                if(hdr.tcp.isValid()){
                    //IP Length to 56 bytes (reply ip(20) + ICMP(8) + received IP header(20) + 8 bytes of data)
                    hdr.ipv4.totalLen = 56;
                    meta.int1 = hdr.tcp.srcPort;
                    meta.int2 = hdr.tcp.dstPort;
                    meta.int3 = hdr.tcp.seqNo[31:16];
                    meta.int4 = hdr.tcp.seqNo[15:0];
                    //make sure all the packets are length 70.. so wireshark does not complain when tpc/uds options,etc
                    truncate((bit<32>)70);
                }else if(hdr.udp.isValid()){
                    //IP Length to 56 bytes (reply ip(20) + ICMP(8) + received IP header(20) + 8 bytes of data)
                    hdr.ipv4.totalLen = 56;
                    meta.int1 = hdr.udp.srcPort;
                    meta.int2 = hdr.udp.dstPort;
                    meta.int3 = hdr.udp.len;
                    meta.int4 = hdr.udp.checksum;
                    //make sure all the packets are length 70.. so wireshark does not complain when tpc/uds options,etc
                    truncate((bit<32>)70);
                }else{
                    hdr.ipv4_icmp.setInvalid();
                }
            }//END Traceroute

            // PING response
            //check if ping is for me by is_it_me.apply()
            if(hdr.icmp.isValid() && meta.ping == 1 && is_it_me.apply().hit){
                //reply to ping echo request

                // Set egress port == ingress port
                standard_metadata.egress_spec = standard_metadata.ingress_port;

                //Ethernet: Swap map addresses
                bit<48> tmp_mac = hdr.ethernet.srcAddr;
                hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
                hdr.ethernet.dstAddr = tmp_mac;
                //Ip
                bit<32> tmp_ip = hdr.ipv4.srcAddr;
                hdr.ipv4.srcAddr = hdr.ipv4.dstAddr;
                hdr.ipv4.dstAddr = tmp_ip;

                hdr.ipv4.ttl = 65; //will result in 64 after ipv4_lpm
                // icmp to echo reply
                hdr.icmp.type = 0;
                hdr.icmp.code = 0;
            }//END echo response
            //ipv4 routing
            if(hdr.ipv4.isValid()) {
                // classify ipv4
                // meta.ipv4 = 1;
                // simple routing based on shortest path given by controller.
                ipv4_lpm.apply(); // sets path length-> meta.nr_of_hops = total ttl lost on path
            }
        }//END of NOT considered flows
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

    apply {

        if (hdr.tcp.isValid()) {
            // Values set for tcp checksum || little Hack here ;)
            meta.reserved = 0;
            meta.tcp_totalLen = hdr.ipv4.totalLen - 20;
        }
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply {
    	update_checksum(
    	    hdr.ipv4.isValid(),
                { hdr.ipv4.version,
    	          hdr.ipv4.ihl,
                  hdr.ipv4.dscp,
                  hdr.ipv4.ecn,
                  hdr.ipv4.totalLen,
                  hdr.ipv4.identification,
                  hdr.ipv4.flags,
                  hdr.ipv4.fragOffset,
                  hdr.ipv4.ttl,
                  hdr.ipv4.protocol,
                  hdr.ipv4.srcAddr,
                  hdr.ipv4.dstAddr },
                  hdr.ipv4.hdrChecksum,
                  HashAlgorithm.csum16);

        //http://www.tcpipguide.com/free/t_TCPChecksumCalculationandtheTCPPseudoHeader-2.htm#Figure_218
        update_checksum_with_payload(
            hdr.tcp.isValid() && hdr.ipv4.isValid() && hdr.tcp_options.isValid(),
            {   hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr,
                meta.reserved,
                hdr.ipv4.protocol,
                meta.tcp_totalLen,
                hdr.tcp.srcPort,
                hdr.tcp.dstPort,
                hdr.tcp.seqNo,
                hdr.tcp.ackNo,
                hdr.tcp.dataOffset,
                hdr.tcp.res,
                hdr.tcp.cwr,
                hdr.tcp.ece,
                hdr.tcp.urg,
                hdr.tcp.ack,
                hdr.tcp.psh,
                hdr.tcp.rst,
                hdr.tcp.syn,
                hdr.tcp.fin,
                hdr.tcp.window,
                hdr.tcp.urgentPtr,
                hdr.tcp_options.options,
                hdr.payload.payload //needs to be added because we parsed it. If not valid, will be ignored
            },
            hdr.tcp.checksum,
            HashAlgorithm.csum16);


        //changed to with_payload
        update_checksum( // for traceroute responses..
            hdr.icmp.isValid() && (hdr.tcp.isValid() || hdr.udp.isValid()) && hdr.ipv4_icmp.isValid(),
                { hdr.icmp.type,
                  hdr.icmp.code,
                  hdr.icmp.unused,
                  hdr.ipv4_icmp.version,
        	      hdr.ipv4_icmp.ihl,
                  hdr.ipv4_icmp.dscp,
                  hdr.ipv4_icmp.ecn,
                  hdr.ipv4_icmp.totalLen,
                  hdr.ipv4_icmp.identification,
                  hdr.ipv4_icmp.flags,
                  hdr.ipv4_icmp.fragOffset,
                  hdr.ipv4_icmp.ttl,
                  hdr.ipv4_icmp.protocol,
                  hdr.ipv4_icmp.hdrChecksum,
                  hdr.ipv4_icmp.srcAddr,
                  hdr.ipv4_icmp.dstAddr,
                  meta.int1,
                  meta.int2,
                  meta.int3,
                  meta.int4
                  },
                  hdr.icmp.checksum,
                  HashAlgorithm.csum16);



        update_checksum_with_payload( // for ping echo responses & request
            hdr.icmp.isValid() && !(hdr.tcp.isValid()) && !(hdr.udp.isValid()),
                { hdr.icmp.type,
                  hdr.icmp.code,
                  hdr.icmp.unused
                  },
                  hdr.icmp.checksum,
                  HashAlgorithm.csum16);

    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
