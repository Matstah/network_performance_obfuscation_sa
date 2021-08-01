//METER RATE LIMITING

// allows for bytes/seconds
meter(meter_length, MeterType.bytes) meter1;
meter(meter_length, MeterType.bytes) meter2;
meter(meter_length, MeterType.bytes) meter3;
meter(meter_length, MeterType.bytes) meter4;
meter(meter_length, MeterType.bytes) meter5;
meter(meter_length, MeterType.bytes) meter6;
meter(meter_length, MeterType.bytes) meter7;
meter(meter_length, MeterType.bytes) meter8;
meter(meter_length, MeterType.bytes) meter9;
meter(meter_length, MeterType.bytes) meter10;


action calc_meter_index(){
    //ipv4.protocol is used to differentiate different traffic types
    hash(meta.meter_index, HashAlgorithm.crc16, (bit<1>)0, {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, meta.obf_type}, meter_length);
}

action meter1_action(){
    meter1.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}
action meter2_action(){
    meter2.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}
action meter3_action(){
    meter3.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}
action meter4_action(){
    meter4.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}
action meter5_action(){
    meter5.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}
action meter6_action(){
    meter6.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}
action meter7_action(){
    meter7.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}
action meter8_action(){
    meter8.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}
action meter9_action(){
    meter9.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}
action meter10_action(){
    meter10.execute_meter<bit<32>>(meta.meter_index, meta.meter_tag);
}


table meter_id_to_meter_read {
    key = {
        meta.bw : exact; //meter id, in range [1,10]
        }
    actions = {
        meter1_action;
        meter2_action;
        meter3_action;
        meter4_action;
        meter5_action;
        meter6_action;
        meter7_action;
        meter8_action;
        meter9_action;
        meter10_action;
        NoAction;
    }
    size = 10;
}

//handles meter tags.. drops packets if sending rate is to high
table m_filter {
    key = {
        meta.meter_tag : exact; // contains the meter value // green, yellow, red
    }
    actions = {
        drop;
        NoAction;
    }
    size = 3;
}
