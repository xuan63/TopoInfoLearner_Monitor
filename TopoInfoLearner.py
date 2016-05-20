from ryu.base import app_manager
from ryu.topology import event
from ryu.controller import ofp_event
from ryu.ofproto import ofproto_v1_3
from ryu.lib.dpid import dpid_to_str
from ryu.topology.switches import Link ,Host
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.topology.api import get_switch, get_link, get_host
import copy
import json
import pprint

Switch_set = {}   #save the information of all switches in topo   
Link_set = []     #save the information of all links in topo      
Host_set = []     #save the information of all hosts in topo
Switch_feature_set = {}  #save the iformaion of OFPSwitchFeatures 

class TopoInfoLearner(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TopoInfoLearner, self).__init__(*args, **kwargs)
        self.topo_switches = []
        self.topo_links = []
        self.topo_hosts = []

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        # print '*'*40,"Switch_set",'*'*40
        msg = ev.msg
        dp_id = dpid_to_str(msg.datapath_id)
        if( Switch_feature_set.has_key(dp_id) == False):
            n_buffers = msg.n_buffers  #max packets buffered at once
            n_tables = msg.n_tables    #max tables saved at once
            Switch_feature_set[dp_id] = {}
            Switch_feature_set[dp_id]["n_buffers"] = n_buffers
            Switch_feature_set[dp_id]["n_tables"] = n_tables
        # pprint.pprint(Switch_feature_set)
        Switch_feature_json = json.dumps(Switch_feature_set, indent=4)
        Sfj_file = open('./Info/Static/Switch_feature_json.json','w+')
        Sfj_file.write(Switch_feature_json)
        Sfj_file.close()
        self.logger.info("******_switch_features_handler, gets Switch_feature_set of %s******", dp_id)

    @set_ev_cls(event.EventSwitchEnter)
    def _switch_enter_handler(self, ev):
        # get_switch(self, None) outputs the list of switches object.
        self.topo_switches = get_switch(self, None)
        # get_link(self, None) outputs the list of links object.
        self.topo_links = get_link(self, None)

        """
        Now you have saved the links and switches of the topo. But they are object, we need to use to_dict() to trans them  
        """
        # print '*'*40,"Switch_set",'*'*40
        for switch in self.topo_switches:
            dp = switch.dp
            dp_no = dpid_to_str(dp.id)
            if (Switch_set.has_key(dp_no) == False):
                ports = switch.ports
                Switch_set[dp_no] = [port.to_dict() for port in ports]
        # pprint.pprint(Switch_set)
        Switch_set_json = json.dumps(Switch_set, indent=4)
        Ssj_file = open('./Info/Static/Switch_json.json','w+')
        Ssj_file.write(Switch_set_json)
        Ssj_file.close()

        # print '*'*40,"Link_set",'*'*40
        Link_set = [ link.to_dict() for link in self.topo_links ]
        # pprint.pprint(Link_set)
        Link_set_json = json.dumps(Link_set, indent=4)
        Lsj_file = open('./Info/Static/Link_json.json','w+')
        Lsj_file.write(Link_set_json)
        Lsj_file.close()
        self.logger.info("******_switch_enter_handler, Switch_set & Link_set******")

    @set_ev_cls(event.EventHostAdd)
    def _host_add_handler(self, ev):
        # get_host(self, None) outputs the list of hosts object.
        self.topo_hosts = get_host(self, None)

        # print '*'*40,"Switch_set",'*'*40
        Host_set = [ host.to_dict() for host in self.topo_hosts ]
        # pprint.pprint(Host_set)
        Host_set_json = json.dumps(Host_set, indent=4)
        Hsj_file = open('./Info/Static/Host_json.json','w+')
        Hsj_file.write(Host_set_json)
        Hsj_file.close()
        self.logger.info("******_host_add_handler, Host_set******" )
