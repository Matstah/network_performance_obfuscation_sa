/*************************************************************************
*********************** P A R S E R  *******************************
*************************************************************************/

/******* MAIN PARSER **********/
parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }
    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType){
            TYPE_IPV4: parse_ipv4;
            TYPE_SRCROUTING : parse_source_routing;
            default: accept;
        }
    }

    state parse_source_routing {
        packet.extract(hdr.srcRoutes.next);
        transition select(hdr.srcRoutes.last.bos) {
            1: parse_ipv4;
            0: parse_source_routing; //lets us loop, till bottom of stack reached..
            default : accept;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol){
            1 : parse_icmp;
            17: parse_udp;
            6  : parse_tcp;
            200: parse_tcp;
            //17 : parse_udp;
            default : accept;
        }
    }
    state parse_icmp {
        packet.extract(hdr.icmp);
        transition accept;
    }
    state parse_udp{
        packet.extract(hdr.udp);
        transition accept;
    }
    state parse_tcp {
        packet.extract(hdr.tcp);
        //for checksum calculation
        meta.tcp_totalLen = hdr.ipv4.totalLen - ((bit<16>)hdr.ipv4.ihl * 4); // subtract ip header, no option= 5*32 bits = 20bytes
        meta.reserved = 0;
        transition select(hdr.tcp.dataOffset){
            5 :accept;
            default: parse_tcp_option;
        }
    }
    state parse_tcp_option {
        transition select(hdr.ipv4.protocol){
            6 : parse_tcp_option_as_varbit;
        }
    }
    state parse_tcp_option_as_varbit {
        bit<4> n = hdr.tcp.dataOffset - 5;
        packet.extract(hdr.tcp_options, (bit<32>) ((bit<32>)n * 32));  //void extract<T>(out T headerLvalue, in bit<32> variableFieldSize);  // variableFieldSize = number of bits to be extracted
        transition parse_payload;
    }
    state parse_payload {
        meta.tcp_payload_len = meta.tcp_totalLen - ((bit<16>)hdr.tcp.dataOffset * 4);
        transition select(meta.tcp_payload_len){
            //payload < 24 bytes
            0 : accept; 1 : accept; 2 : accept; 3 : accept; 4 : accept;
            5 : accept; 6 : accept; 7 : accept; 8 : accept; 9 : accept;
            10 : accept;11 : accept; 12 : accept; 13 : accept; 14 : accept;
            15 : accept; 16 : accept; 17 : accept; 18 : accept; 19 : accept;
            20 : accept; 21 : accept; 22 : accept; 23 : accept;
            default : extract_payload; // payload.len >= 24 bytes
        }
    }
    state extract_payload {
        packet.extract(hdr.payload); //first 24 bytes of payload
        transition accept;
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {

        //parsed headers have to be added again into the packet.
        packet.emit(hdr.ethernet);

        //srcRouting header
        packet.emit(hdr.srcRoutes);

        packet.emit(hdr.ipv4);

        //if icmp traceroute response:
        packet.emit(hdr.icmp);
        packet.emit(hdr.ipv4_icmp);

        //Depars Network and Transport layer:
        packet.emit(hdr.udp);

        packet.emit(hdr.tcp);
        packet.emit(hdr.tcp_options); //tcp option as varbit

        packet.emit(hdr.payload);

    }
}
