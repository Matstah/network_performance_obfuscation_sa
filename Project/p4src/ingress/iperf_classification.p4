register<bit<32>>(iperf_bloom_cells) iperf_bloom_filter;
register<bit<2>>(iperf_sm_cells) iperf_sm;
register<bit<16>>(iperf_sm_cells) iperf_tcp_opt_mss;


action parse_payload(){
    meta.int1 = hdr.payload.payload[79:64];
    meta.int2 = hdr.payload.payload[63:48];
    meta.int3 = hdr.payload.payload[47:32];
    meta.int4 = hdr.payload.payload[31:16];
    meta.int5 = hdr.payload.payload[15:0];
}

action calc_index_iperf_blom(){
    hash(meta.b_index1, HashAlgorithm.crc16, (bit<1>)0,
        { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.tcp.srcPort,
          hdr.tcp.dstPort, hdr.ipv4.protocol}, (bit<32>)iperf_bloom_cells);
    hash(meta.b_index2, HashAlgorithm.crc32, (bit<1>)0,
        { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.tcp.srcPort,
          hdr.tcp.dstPort, hdr.ipv4.protocol}, (bit<32>)iperf_bloom_cells);
}

action read_iperf_bloom(){
    iperf_bloom_filter.read(meta.b_value1, (bit<32>)meta.b_index1);
    iperf_bloom_filter.read(meta.b_value2, (bit<32>)meta.b_index2);
}

action remove_entry_in_iperf_bloom_filter(){
    iperf_bloom_filter.write((bit<32>)meta.b_index1, meta.b_value1 - 1);
    iperf_bloom_filter.write((bit<32>)meta.b_index2, meta.b_value2 - 1);
}

action set_entry_in_iperf_bloom_filter(){
    iperf_bloom_filter.write((bit<32>)meta.b_index1, meta.b_value1 + 1);
    iperf_bloom_filter.write((bit<32>)meta.b_index2, meta.b_value2 + 1);
}

action calc_index_iperf_sm(){
    hash(meta.sm_index, HashAlgorithm.crc16, (bit<1>)0,
        { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.tcp.srcPort,
          hdr.tcp.dstPort, hdr.ipv4.protocol}, (bit<32>)iperf_sm_cells);
}
action set_sm_to_start_state(){
    iperf_sm.write((bit<32>)meta.sm_index, 0);
}

action set_sm_to_handshake_completed_state(){
    iperf_sm.write((bit<32>)meta.sm_index, 1);
}

action set_sm_to_id_send_state(){
    iperf_sm.write((bit<32>)meta.sm_index, 2);
}

action set_sm_to_default_state(){
    iperf_sm.write((bit<32>)meta.sm_index, 3);
}

action read_iperf_sm_state(){
    iperf_sm.read(meta.sm_state, (bit<32>)meta.sm_index);
}

action store_tcp_mss(){
    iperf_tcp_opt_mss.write((bit<32>)meta.sm_index, meta.tcp_mss);
}

action read_tcp_mss_from_storage(){
    iperf_tcp_opt_mss.read(meta.tcp_mss, (bit<32>)meta.sm_index);
}


table iperf_payload {
    key = {
        meta.int1 : exact;
        meta.int2 : exact;
        meta.int3 : exact;
        meta.int4 : exact;
        meta.int5 : exact;
    }
    actions = {
        NoAction;
        drop;
    }
    size = 10;
}
