/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_START_MEASUREMENT = 0x2000;
const bit<16> TYPE_LINK_LATENCY = 0x1000;
const bit<16> TYPE_SRCROUTING = 0x1111;

#define MAX_HOPS 9

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;



header ethernet_t { //2*6 + 2 = 14bytes
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}


/// S O U R C E - R O U T I N G ///
header srcRoute_t {
    bit<7>   port;
    bit<1>    bos; //Bottom Of Stack
}

typedef srcRoute_t[MAX_HOPS] srcRoute_stack;

/// I p v 4 ///
header ipv4_t { //
    bit<4>    version;
    bit<4>    ihl;
    bit<6>    dscp;
    bit<2>    ecn;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

/// U D P ///
header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> len;
    bit<16> checksum;
}

/// T C P + O P T I O N S ///
header tcp_t{
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset; //up to 40 bytes of options in the header.. defines total header length, max 60bytes
    bit<4>  res;
    bit<1>  cwr;
    bit<1>  ece;
    bit<1>  urg;
    bit<1>  ack;
    bit<1>  psh;
    bit<1>  rst;
    bit<1>  syn;
    bit<1>  fin;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

// tcp option as varbit
header tcp_options_t {
    varbit<320> options;
}

/// P A Y L O A D    S A M P L E ///
header sample_payload_t{
    bit<192> payload; //24 bytes
}

/// C O N T R O L E R - H E A D E R S///
header controller_t{
    bit<8> cloneType;
    bit<16> etherType;
}

/// I C M P - H E A D E R ///
header icmp_t {
   bit<8> type;
   bit<8> code;
   bit<16> checksum;
   bit<32> unused;
}

struct metadata {
    // traffic types to classify
    bit<1> ping;
    bit<1> iperf;
    bit<1> tcp;
    bit<1> udp;
    bit<1> ipv4;

    // Traceroute classification
    bit<8> nr_hops_on_path;

    //reply icmp echos
    bit<1> src_routing;

    // iperf traffic classification
    bit<2> sm_state;
    bit<16> int1;
    bit<16> int2;
    bit<16> int3;
    bit<16> int4;
    bit<16> int5;
    bit<16> b_index1;
    bit<16> b_index2;
    bit<32> b_value1;
    bit<32> b_value2;
    bit<16> sm_index;
    bit<16> tcp_payload_len;
    bit<16> tcp_mss;

    //used to tell switch what is possible on link..
    //bit<1> entry_type; // 0=link from ext, 1= link from intern. if next link is under our control/ oposite switch ours..
    //bit<2> travel_type; // 0=int-ext, 1=ext-int, 2=int-int, 3=ext-ext,
    //bit<8> e2e_id;

    //used for bandwidth calculation
    bit<32> loss_rate; //basically meter tag
    bit<16> tcp_window;
    bit<8>  tcp_w_scale;

    // given as input parameters
    bit<3> obf_type;
    bit<8> path_id;
    //bit<16> w_size;
    bit<10> pack_loss_rate;
    //bit<3> meter_id; // 2³ = 8 diff meters..
    bit<16> bw;
    bit<4> ttl_to_subtract;

    //used for loss rate/ rate limiting
    bit<32> meter_tag;
    bit<32> meter_index;

    //used for tcp checksum
    bit<16> tcp_totalLen;
    bit<8>  reserved;
}

error {
    TcpDataOffsetTooSmall/*,
    TcpOptionTooLongForHeader,
    TcpBadSackOptionLength*/
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4_icmp;
    icmp_t       icmp;
    ipv4_t       ipv4;
    udp_t        udp;
    tcp_t        tcp;
    tcp_options_t tcp_options;//tcp option as varbit
    controller_t controller;
    sample_payload_t payload;
    srcRoute_stack srcRoutes;
}
