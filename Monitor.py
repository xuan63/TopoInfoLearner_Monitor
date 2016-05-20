from ryu.base import app_manager
from ryu.topology.switches import Switches
from ryu.ofproto import ofproto_v1_3
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from operator import attrgetter
from ryu.controller import ofp_event
from ryu.lib.dpid import dpid_to_str
from ryu.lib.port_no import port_no_to_str
from ryu.lib import hub
import json
import pprint

Freq = 2            # second
BandWidth = 100     # Mbps
Port_stats = {}     #real-time information of each port of each switch    
Flow_stats = {}     #real-time information of each flow of each switch 

# def calRBW( new_tbytes, old_tbytes=None): # calculate Remain BandWidth
#     if(old_tbytes==None):
#         return BandWidth-new_tbytes*8/1024/1024/Freq
#     else:
#         return BandWidth-(new_tbytes-old_tbytes)*8/1024/1024/Freq


class Monitor(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)
        self.datapaths={}
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER,DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        dpid = datapath.id
        if( dpid!=None ):
            dpid_str = dpid_to_str(dpid)
        if ev.state == MAIN_DISPATCHER:
            self.logger.debug('register datapath :%s', dpid_str)
            self.datapaths[dpid] = datapath
            Port_stats[dpid_str] = {}
            Flow_stats[dpid_str] = {}
        elif ev.state == DEAD_DISPATCHER:
            if dpid in self.datapaths:
                self.logger.debug('unregister datapath :%s', dpid_str)
                del self.datapaths[dpid]
                del Port_stats[dpid_str]
                del Flow_stats[dpid_str]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(Freq)

    def _request_stats(self, datapath):
        # print '\n'*2, '*'*70
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        # print '*'*100
        body = ev.msg.body
        dpid_str = dpid_to_str(ev.msg.datapath.id)
        for stat in sorted(body, key=attrgetter('port_no')):
            port_data = {}          #save th port data   {'rx-pkts':  ,'tx-pkts':  }
            port_no = stat.port_no
            # if (hex(port_no) != '0xfffffffe'):         # except for the port to controller
            # calculate Remain BandWidth 
            new_tbytes = stat.tx_bytes
            port_no_str = port_no_to_str(port_no)
            if(  Port_stats[dpid_str].has_key(port_no_str)==True ):
                old_tbytes = Port_stats[dpid_str][port_no_str]['tx_bytes']
                remainBandWidth = self.calRBW( new_tbytes, old_tbytes )
            else:
                # print '******the case of first statics******'
                remainBandWidth = self.calRBW(new_tbytes=new_tbytes)  # the case of first statics
            port_data['rx-pkts'] = stat.rx_packets
            port_data['tx-pkts'] = stat.tx_packets
            port_data['rx-bytes'] = stat.rx_bytes
            port_data['tx_bytes'] = stat.tx_bytes
            port_data['rx-errors'] = stat.rx_errors
            port_data['tx-errors'] = stat.tx_errors
            port_data['rx_dropped'] = stat.rx_dropped
            port_data['tx_dropped'] = stat.tx_dropped
            port_data['remainBandWidth-Mbps'] = remainBandWidth
            Port_stats[dpid_str][port_no_str]= port_data
        # pprint.pprint(Port_stats)
        Port_stats_json=json.dumps(Port_stats, indent=4)
        # print Port_stats_json
        f = open('./Info/Dynamic/Port_stats.json','w+')
        # time = time.strftime('%Y-%m-%d %H:%M:%S')
        # f.write(time+'\n')
        f.write(Port_stats_json)
        f.close()
        self.logger.info("******_port_stats_reply_handler, gets Port_stats of %s******", dpid_str)

    def calRBW( self, new_tbytes, old_tbytes=None): # calculate Remain BandWidth
        if(old_tbytes==None):
            return BandWidth-new_tbytes*8/1024/1024/Freq
        else:
            return BandWidth-(new_tbytes-old_tbytes)*8/1024/1024/Freq

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid_str = dpid_to_str(ev.msg.datapath.id) 
        flow_data = ev.msg.to_jsondict()['OFPFlowStatsReply']['body']      
        Flow_stats[dpid_str] = flow_data
        Flow_stats_json=json.dumps(Flow_stats, indent=4)
        # print Flow_stats_json
        f = open('./Info/Dynamic/Flow_stats.json','w+')
        f.write(Flow_stats_json)
        f.close()
        self.logger.info("******_flow_stats_reply_handler, gets Flow_stats of %s******", dpid_str)

