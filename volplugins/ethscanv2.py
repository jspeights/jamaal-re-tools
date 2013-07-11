# Volatility    
# Copyright (c) 2010, 2011, 2012, 2013 Jamaal Speights <jamaal.speights@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details. 
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA 

# ETHSCAN - Recover ethernet packets from memory 
# 
# This plugin will attempt to recovere packets from memory. 
# Packets found in memory can be saved as individual raw binary files or 
# each packet will be saved to a pcap file.  
#
#ProcName: VMip.exe PID: 180  Base Address: 0x162000  End Address: 0x163000
#IPv4 (0x0800) 
#Protocol UDP (17)
#Src: 172.16.176.1:31982 (00:50:56:c0:00:08), Dst: 172.16.176.255:35072 (ff:ff:ff:ff:ff:ff)
#Data (92 Bytes)
#0x00000000  ff ff ff ff ff ff 00 50 56 c0 00 08 08 00 45 00   .......PV.....E.
#0x00000010  00 4e 97 dc 00 00 40 11 29 a1 ac 10 b0 01 ac 10   .N....@.).......
#0x00000020  b0 ff ee 7c 00 89 00 3a 6d 90 67 45 01 10 00 01   ...|...:m.gE....
#0x00000030  00 00 00 00 00 00 20 46 48 45 50 46 43 45 4c 45   .......FHEPFCELE
#0x00000040  48 46 43 45 50 46 46 46 41 43 41 43 41 43 41 43   HFCEPFFFACACACAC
#0x00000050  41 43 41 43 41 42 4e 00 00 20 00 01               ACACABN.....



import struct
import os 
import volatility.plugins.common as common 

import volatility.commands as commands
import volatility.utils as utils
import volatility.scan as scan
import volatility.obj as obj
import volatility.debug as debug
import volatility.plugins.taskmods as taskmods
import volatility.cache as cache
from binascii import hexlify
from binascii import unhexlify

#compair command line option to has_dpkt
#-p pcap.out  if has_dpkt == True: 
try:
    import dpkt 
    from dpkt import pcap 
    from dpkt.pcap import Writer 
    has_dpkt = True
except ImportError:
    has_dpkt = False

        
protocols = {
        0x00:  'HOPOPT', 
        0x01:  'ICMP', 
        0x02:  'IGMP', 
        0x03:  'GGP', 
        0x04:  'IPv4', 
        0x05:  'ST', 
        0x06:  'TCP', 
        0x07:  'CBT', 
        0x08:  'EGP', 
        0x09:  'IGP', 
        0x0A:  'BBN-RCC-MON', 
        0x0B:  'NVP-II', 
        0x0C:  'PUP', 
        0x0D:  'ARGUS', 
        0x0E:  'EMCON', 
        0x0F:  'XNET', 
        0x10:  'CHAOS', 
        0x11:  'UDP', 
        0x12:  'MUX', 
        0x13:  'DCN-MEAS', 
        0x14:  'HMP', 
        0x15:  'PRM', 
        0x16:  'XNS-IDP', 
        0x17:  'TRUNK-1', 
        0x18:  'TRUNK-2', 
        0x19:  'LEAF-1', 
        0x1A:  'LEAF-2', 
        0x1B:  'RDP', 
        0x1C:  'IRTP', 
        0x1D:  'ISO-TP4', 
        0x1E:  'NETBLT', 
        0x1F:  'MFE-NSP', 
        0x20:  'MERIT-INP', 
        0x21:  'DCCP', 
        0x22:  '3PC', 
        0x23:  'IDPR', 
        0x24:  'XTP', 
        0x25:  'DDP', 
        0x26:  'IDPR-CMTP', 
        0x27:  'TP++', 
        0x28:  'IL', 
        0x29:  'IPv6', 
        0x2A:  'SDRP', 
        0x2B:  'IPv6-Route', 
        0x2C:  'IPv6-Frag', 
        0x2D:  'IDRP', 
        0x2E:  'RSVP', 
        0x2F:  'GRE', 
        0x30:  'MHRP', 
        0x31:  'BNA', 
        0x32:  'ESP', 
        0x33:  'AH', 
        0x34:  'I-NLSP', 
        0x35:  'SWIPE', 
        0x36:  'NARP', 
        0x37:  'MOBILE', 
        0x38:  'TLSP', 
        0x39:  'SKIP', 
        0x3A:  'IPv6-ICMP', 
        0x3B:  'IPv6-NoNxt', 
        0x3C:  'IPv6-Opts', 
        0x3D:  'Any host internal protocol', 
        0x3E:  'CFTP', 
        0x3F:  'Any local network', 
        0x40:  'SAT-EXPAK', 
        0x41:  'KRYPTOLAN', 
        0x42:  'RVD MIT', 
        0x43:  'IPPC', 
        0x44:  'Any distributed file system ', 
        0x45:  'SAT-MON SATNET', 
        0x46:  'VISA', 
        0x47:  'IPCV', 
        0x48:  'CPNX', 
        0x49:  'CPHB', 
        0x4A:  'WSN', 
        0x4B:  'PVP', 
        0x4C:  'BR-SAT-MON', 
        0x4D:  'SUN-ND', 
        0x4E:  'WB-MON', 
        0x4F:  'WB-EXPAK', 
        0x50:  'ISO-IP', 
        0x51:  'VMTP', 
        0x52:  'SECURE-VMTP', 
        0x53:  'VINES', 
        0x54:  'TTP', 
        0x54:  'IPTM', 
        0x55:  'NSFNET-IGP', 
        0x56:  'DGP', 
        0x57:  'TCF', 
        0x58:  'EIGRP', 
        0x59:  'OSPF', 
        0x5A:  'Sprite-RPC', 
        0x5B:  'LARP', 
        0x5C:  'MTP Multicast Transport Protocol', 
        0x5D:  'AX.25', 
        0x5E:  'IPIP', 
        0x5F:  'MICP', 
        0x60:  'SCC-SP', 
        0x61:  'ETHERIP', 
        0x62:  'ENCAP', 
        0x63:  'Any private encryption scheme', 
        0x64:  'GMTP', 
        0x65:  'IFMP', 
        0x66:  'PNNI', 
        0x67:  'PIM', 
        0x68:  'ARIS', 
        0x69:  'SCPS', 
        0x6A:  'QNX', 
        0x6B:  'A/N', 
        0x6C:  'IPComp', 
        0x6D:  'SNP', 
        0x6E:  'Compaq-Peer', 
        0x6F:  'IPX-in-IP', 
        0x70:  'VRRP', 
        0x71:  'PGM', 
        0x72:  'Any 0-hop protocol', 
        0x73:  'L2TP', 
        0x74:  'DDX', 
        0x75:  'IATP', 
        0x76:  'STP', 
        0x77:  'SRP', 
        0x78:  'UTI', 
        0x79:  'SMP', 
        0x7A:  'SM', 
        0x7B:  'PTP', 
        0x7C:  'IS-IS over IPv4', 
        0x7D:  'FIRE', 
        0x7E:  'CRTP', 
        0x7F:  'CRUDP', 
        0x80:  'SSCOPMCE', 
        0x81:  'IPLT', 
        0x82:  'SPS', 
        0x83:  'PIPE', 
        0x84:  'SCTP', 
        0x85:  'FC', 
        0x86:  'RSVP-E2E-IGNORE', 
        0x87:  'Mobility Header', 
        0x88:  'UDP Lite', 
        0x89:  'MPLS-in-IP', 
        0x8A:  'manet', 
        0x8B:  'HIP', 
        0x8C:  'Shim6', 
        0xFE:  'Unknown'
}

ethertypes = {
    0x0800:  'IPv4', 
    0x0806:  'ARP', 
    0x0842:  'Wake-on-LAN', 
    0x22F3:  'IETF TRILL Protocol', 
    0x6003:  'DECnet Phase IV', 
    0x8035:  'Reverse ARP', 
    0x809B:  'AppleTalk', 
    0x80F3:  'AppleTalk ARP', 
    0x8100:  'VLAN-tagged', 
    0x8137:  'IPX', 
    0x8138:  'IPX', 
    0x8204:  'QNX Qnet', 
    0x86DD:  'IPv6', 
    0x8808:  'Ethernet flow control', 
    0x8809:  'Slow Protocols (IEEE 802.3)', 
    0x8819:  'CobraNet', 
    0x8847:  'MPLS unicast', 
    0x8848:  'MPLS multicast', 
    0x8863:  'PPPoE Discovery Stage', 
    0x8864:  'PPPoE Session Stage', 
    0x8870:  'Jumbo Frames', 
    0x887B:  'HomePlug 1.0 MME', 
    0x888E:  'IEEE 802.1X', 
    0x8892:  'PROFINET Protocol', 
    0x889A:  'SCSI over Ethernet', 
    0x88A2:  'ATA over Ethernet', 
    0x88A4:  'EtherCAT', 
    0x88A8:  '802.1ad & IEEE 802.1aq', 
    0x88AB:  'Ethernet Powerlink', 
    0x88CC:  'LLDP', 
    0x88CD:  'SERCOS', 
    0x88E1:  'HomePlug AV MME', 
    0x88E3:  'Media Redundancy Protocol (IEC62439-2)', 
    0x88E5:  'MAC security (IEEE 802.1AE)', 
    0x88F7:  'Precision Time Protocol (IEEE 1588)', 
    0x8902:  'IEEE 802.1ag', 
    0x8906:  'FCoE', 
    0x8914:  'FCoE Initialization Protocol', 
    0x8915:  'RDMA over Converged Ethernet (RoCE)', 
    0x9000:  'Ethernet Configuration Testing Protocol', 
    0x9100:  'Q-in-Q', 
    0xCAFE:  'Veritas Low Latency Transport (LLT)'
}             
        
class PacketDataClass(object):
    """PacketDataClass Class returns Ethernet and Protocol types by get_ethtype and get_prototye methods"""
    def __init__(self):
        self.MTU = 1500
        self.checksum = ""
        self.checksumValue = 0 
        self.IPv4Header = 0x0800
        self.IPv6Header = 0x86DD        
        self.IPv4 =  struct.pack('>H', self.IPv4Header)   
        self.IPv6 =  struct.pack('>H', self.IPv6Header)   
        self.ethertypes = ethertypes
        self.protocols = protocols
              
    def checksum_ipv4(self, data):
        """checksum vlidation for ipv4,  Returns zero on success"""
        z=0 
        carry_byte=rbytes=""
        for i in range(0, len(data) - 1, 2):
            z += struct.unpack('>H', data[i:i+2])[0]
        checksum = hex(z)[2:]
        carry_byte = checksum[0]
        rbytes= checksum[1:] #remainder_bytes
        checksum = int(rbytes, 0x10)+int(carry_byte, 0x10)
        return (~checksum & 0xFFFF)   #verified bytes   
        
    def ipv6_ispktValid(self, eth):
        """ Checks last 3 bytes of Src/Dst Addr to last 6 bytes of Src/Dst Mac address 
              Bytes should be equal validing the packet as IPv6 """
                
        ethsrcbytes = eth.obj_vm.read(eth.ethv6Src.obj_offset, 6)
        ethdstbytes = eth.obj_vm.read(eth.ethv6Dst.obj_offset, 6)

        ipsrcbytes = eth.obj_vm.read(eth.ipv6Src.obj_offset,  eth.ipv6Src.size())
        ipdstbytes = eth.obj_vm.read(eth.ipv6Dst.obj_offset,  eth.ipv6Dst.size())
        
#        print hexlify(ethsrcbytes[-3:]),  " ethsrcbytes"
#        print hexlify(ethdstbytes[-3:]),  " ethdstbytes"
#        print hexlify(ipsrcbytes[-3:]),  " ipsrcbytes"
#        print hexlify(ipdstbytes[-3:]),  " ipdstbytes"

        return any((ethsrcbytes[-3:], ethdstbytes[-3:], ipsrcbytes[-3:], ipdstbytes[-3:]))
    
    
    def get_ethtype(self, lookup):
        """ returns the ethernet type from lookup (int) returning (Pv4(str)  2048(int) 0x0800(str))"""
        ethnum = lookup
        ethstr = self.ethertypes.get(ethnum, "Unknown")
        ethnumstr = "0x%04X" % ethnum
        return ethstr, ethnum, ethnumstr  
        
    def get_prototye(self, lookup):
        """ returns the protocol type from lookup (int) returning (TCP(str), 6(int) 0x6(str))"""
        protonum = lookup
        protostr = self.protocols.get(protonum, "Unknown")
        protonumstr = "0x%04X" % protonum        
        return protostr,protonum, protonumstr

    def check_IPV4(self, eth):
        """returns True if frame has valid IPv4 packet"""
        if eth.ipv4Ver & 0xF0 == 0x40: 
            if eth.ipv4TotalLen <= self.MTU:
                self.checksum = ''.join([chr(cs) for cs in eth.ipv4CheckSum])
                self.checksumValue = self.checksum_ipv4(self.checksum)
                if self.checksumValue == 0:
                    return True 
                else:
                    return False 
                    
    def check_IPV6(self, eth):
        """returns True if frame has valid IPv4 packet"""
        
        if eth.ipv6Ver == 0x60:
            if eth.ethType ==  0x86dd:
                self.ipv6_ispktValid(eth)
                print "DEBUG IPv6 packet found from class"
                return True
            else:
                return False
            
            
class EthScanVTypes(obj.ProfileModification):
    """ EthScanVTypes packet structure """
    
    def modification(self, profile):        
        """updates profile with ethVtype which helps define frame/packet data structure for ethernet/ipv4/ipv6 """
        ethVtype = {
        'ethFrame': [ 0x0, {
            'ethDst' : [ 0x0, ['array', 6,  ['unsigned char']]],
            'ethSrc': [ 0x6, ['array', 6,  ['unsigned char']]],       
            'ethType': [ 0x0c, ['unsigned be short']],         
            'ipv4Ver': [0x0e, ['unsigned char']], 
            'ipv4CheckSum': [ 0x0e, ['array', 20,  ['unsigned char']]],            
            'ipv4DSF': [0xf, ['unsigned char']], 
            'ipv4TotalLen': [0x10, ['unsigned be short']], 
            'ipv4IDENT': [0x12, ['unsigned short']], 
            'ipv4FLAG': [0x14, ['unsigned char']],
            'ipv4OffSet': [0x14, ['unsigned short']],         # // ipv4OffSet = ipv4FLAG offset + size of 2 bytes
            'ipv4TTL': [0x16, ['unsigned char']],  
            'ipv4ProtoType': [0x17, ['unsigned char']],  
            'ipv4Checksum': [0x18, ['unsigned short']],  
            'ipv4Source': [0x1a, ['IpAddress']],  
            'ipv4Dest': [0x1e, ['IpAddress']],  
             'ipv4SrcPort' : [0x22, ['unsigned short']],  
             'ipv4DstPort' : [0x24, ['unsigned short']],  
             'ethv6Dst': [0x0, ['Ipv6Address']],                 # // IPV6  Frame & Packet Structure
             'ethv6Src': [0x6, ['Ipv6Address']],                 
             'ipv6Ver': [0x0e, ['unsigned char']], 
            'ipv6TotalLen': [0x12, ['unsigned be short']],             
            'ipv6NextHeader': [0x13, ['unsigned char']], 
            'ipv6CheckSumUDP': [0x38, ['unsigned short']],     
            'ipv6CheckSumTCP': [0x46, ['unsigned short']],          
            'ipv6Src': [0x16, ['Ipv6Address']],  
            'ipv6Dst': [0x26, ['Ipv6Address']],  
                            }], 
        }
        profile.vtypes.update(ethVtype)

class FindEthFrame(scan.ScannerCheck):
    """ ScannerCheck to verify the IPv4 protocol, standard header length and protocol """
    def __init__(self, address_space, needles = None):
        scan.ScannerCheck.__init__(self, address_space) 
        self.packet =  PacketDataClass()
        self.ipv4 = self.packet.IPv4    # 0x0800 (bin)
        self.ipv6 = self.packet.IPv6    # 0x86dd (bin)
        self.ipv4Header = self.packet.IPv4Header    #0x0800 (int)
        self.ipv6Header = self.packet.IPv6Header    #0x86dd (int)
        self.MTU = self.packet.MTU
        self.nextvalv4 = 0 
        self.nextvalv6  = 0 
        self.nextValue = 0 
        

    def check(self, offset):
        """checks for valid ipv4/ipv6 packets"""    

        eth = obj.Object('ethFrame', vm = self.address_space, offset = offset)
        
        # // IPv4 header check so check_IPV4() method isnt called needlesssly 
        if eth.ethType == self.ipv4Header:
            if self.packet.check_IPV4(eth):
                return eth

        if eth.ethType == self.ipv6Header:
            if self.packet.check_IPV6(eth):
                return eth

    #// Skip bytes based upon ethertypes from the PacketDataClass Class 
    def skip(self, data, offset):
        try:
            self.nextvalv4 = data.index(self.ipv4, offset + 1)
            self.nextvalv6 = data.index(self.ipv6, offset + 1)
            
            if self.nextvalv4 != self.nextvalv6:
                self.nextValue = min(self.nextvalv4, self.nextvalv6)
            else:
                self.nextValue = max(self.nextvalv4, self.nextvalv6)
            
            # // return() 
            # // len(self.ipv4) == 2 
            # // 0xC = ethFrame start 
            return (self.nextValue-len(self.ipv4)-0xC)-offset 
            
        except ValueError:
            ## Substring is not found - skip to the end of this data buffer
            
            #print "debug error returning ", hex(len(data) - offset)
           # print "debug error data len is ",  hex(len(data))
            #print "debug error offset is ",  hex(offset)
            return len(data) - offset            
            
class EthScanner(scan.BaseScanner):
    checks = [('FindEthFrame', {})]

#class EthDataControl(object):
#    """Controls data, options and text formatting"""
#    def __init__(self, config, *args, **kwargs):
#        self.config = config 
#        self.adderss_space = self.address_space 
#        print "debug"

class EthDataControl(object):
    """Controls data, options and text formatting"""
    def __init__(self, config, address_space,  *args, **kwargs):
        self.config = config         
        self.address_space = address_space

        # // Check if SAVE_PCAP or SAVE_RAW is True 
        if any((self.config.SAVE_PCAP, self.config.SAVE_RAW)):
        
            # // test if SAVE_PCAP or SAVE_RAW options are set: 
            # // make sure the dump directory is set else generate error and exit 
            if self.config.DUMP_DIR == None:
                debug.error("Please specify a dump directory (--dump-dir)")
                
            # // make sure the output directory is real, if not exit 
            if not os.path.isdir(self.config.DUMP_DIR):
                debug.error(self.config.DUMP_DIR + " is not a directory")
                
            # // Check if Save Pcap option was set 
            if self.config.SAVE_PCAP != None:
                
                # // Make sure dpkt is installed if not exit 
                if not has_dpkt:
                    debug.error("Install dpkt http://code.google.com/p/dpkt/")
                # // If dpkt is install, check filename to make sure it ends with cap 
                else:
                    self.pcapfile = self.config.SAVE_PCAP
                    if self.pcapfile[-3:].lower() != "cap":
                        self.pcapfile = self.pcapfile + ".pcap"
                    # // define output file path and filename plus initial pcw file descriptor 
                    self.pcapfile = open(os.path.join(self.config.DUMP_DIR, self.pcapfile), 'wb')
                    self.pcw = dpkt.pcap.Writer(self.pcapfile)
        print "HI"
       
        #win_memObj = self.return_pid_task_pages()
##        print "win_memObj", win_memObj
##        for x in win_memObj:
##            print x 
#        for pid, task, pagedata in win_memObj:
#            task_space = task.get_process_address_space()
#            currentProc = ("{0} pid: {1:6}\n".format(task.ImageFileName, pid))           
#            print currentProc
#
#    def return_pid_task_pages(self):
#        try:
#            tasks = taskmods.DllList.calculate(self)            
#            for task in tasks:
#                print "debug a", task
#                if task.UniqueProcessId:
#                    pid = task.UniqueProcessId
#                    task_space = task.get_process_address_space()
#                    pages = task_space.get_available_pages()
#                yield pid, task, pages            
#        except:
#            yield False 


#    def buildAddressMaps(self, outfd, pktoffset, ptpobj):
#        """fdsafdsfadsfds fdasfdsfdsafdsaf"""
#        for pid, task, pagedata in ptpobj:
#            task_space = task.get_process_address_space()
#            currentProc = ("{0} pid: {1:6}\n".format(task.ImageFileName, pid))
#            offset = 0 
#            for p in pagedata:
#                pa = task_space.vtop(p[0])
#                if pa != None:
#                    if pktoffset >= pa and pktoffset <= pa+p[1]: 
#                        mapAddrList = [str(task.ImageFileName), int(pid), pa, p[1]]
#                        return mapAddrList
#                    else:
#                        offset += p[1]
#        return None         
        
class EthScan(common.AbstractWindowsCommand):
    """Scans and dumps complete ethernet frames from memory while vildating legitmate ipv4/ipv6 packets"""
    
    def __init__(self, config, *args, **kwargs):
        commands.Command.__init__(self, config, *args, **kwargs)
        config.remove_option("OFFSET")
        config.add_option('DUMP-DIR', short_option = 'D', default = None,           
                          cache_invalidator = False,
                          help = 'Directory in which to dump executable files')
        config.add_option('SAVE-PCAP', short_option = 'P', default = None,
                          cache_invalidator = False,
                          help = 'Create a pcap file from recovered packets of given name: "Example: -p out.pcap" (requires dpkt)')
        config.add_option("SAVE-RAW", short_option = 'r', default = False, action = 'store_true',
                        help = 'Create binary files of each pcap found in memory based off the packet counter: ')
        self.config = config 

    def calculate(self):       
        
        address_space = utils.load_as(self._config, astype = 'physical')
        print 'debug  ', address_space
        ethDC = EthDataControl(self.config, address_space)
#        
#
#        for offset in EthScanner().scan(address_space):
#            objct = obj.Object('ethFrame', vm = address_space, offset = offset)
#            yield  objct
#
#    def render_text(self, outfd, data):
#        """output collected data as text while processing options and saving output data to disk"""
#                
#        #ethDC = EthDataControl(self.config, self.address_space)
#        #Create a Print output Class for printing output 
#        #Accept command line arguments (or be aware of them)
#        # the Class 
#        
##        ptpobj = self.getPTP()
##        for chkobj in ptpobj:
##            if chkobj == False:
##                nomapAddrList = True
##            else:
##                nomapAddrList = False 
##
##            
##        # // Set pcap file name
##
##        counter = 0
##        for objct in data:
##            # // Find packet process, pid, and address range 
##            pktoffset = objct.ethDst.obj_offset
##            if nomapAddrList == False:
##                print "debug ",  nomapAddrList
##                mapAddrList = self.mapOffsetToAddr(outfd, pktoffset, ptpobj)
##            else:
##                mapAddrList = False  
##            # // mapAddrList: Proc Name, PID, START ADDR, END ADDR 
##            # // just to be safe we set all values to "" 
##            # // That way we can still use them even if they don't carry a value 
##            procName = ""
##            pid = ""
##            base_addr = ""
##            end_addr = ""
##            
##            if mapAddrList:
##                if mapAddrList[0] != None:
##                    procName = mapAddrList[0]
##                if mapAddrList[1] != None:
##                    pid = mapAddrList[1]
##                if mapAddrList[2] != None:
##                    base_addr = hex(mapAddrList[2])
##                if mapAddrList[3] != None:
##                    end_addr = hex(mapAddrList[2] + mapAddrList[3])
##
##            source = objct.ipv4Source.v()
##            dest = objct.ipv4Dest.v()
##            srcport = str(objct.ipv4SrcPort.v())
##            destport = str(objct.ipv4DstPort.v())
##
##            #// Packet Size 
##            psize = objct.ipv4TotalLen.v()
##            pdata = objct.obj_vm.read(objct.ipv4Ver.obj_offset, psize)
##            
##            # // 0xE the size of 
##            # // DST MAC ADDR + SRC MAC ADDR + PACKET TYPE (0x0800 for example)
##            # // The IP header starts at 0xE offset which is normally 0x45 (Version + header length) 
##            pheader = objct.obj_vm.read(objct.ethDst.obj_offset, 0xe)
##            
##            #Mac Addr 
##            macdst =  objct.obj_vm.read(objct.ethDst.obj_offset, objct.ethSrc.size())       
##            macsrc =  objct.obj_vm.read(objct.ethSrc.obj_offset, objct.ethSrc.size())    
##
##            # // Packet ID  (0x800 for example)
##            #etype = objct.obj_vm.read(objct.ethType.obj_offset, objct.ethType.size())
##            etype = objct.ethType.v()
##            
##            # // Convert Mac Address by unpacking into fmt string 
##            # // ':'.join(h[i:i+2] for i in range(0,12,2))
##            macsrc = "%02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("6B",macsrc)
##            macdst = "%02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("6B",macdst)
##            
##            # // ProtoType Number [17 (0x11) = UDP, 0x6 = TCP] for example
##            proto = objct.ipv4ProtoType.v()
##                        
##            # // Packet Types Class instance to lookup either Ethernet Frame Type or Protocol Type 
##            # // Methods: get_prototye(int value) | returns Protocol string description 
##            # // Methods: get_ethtype(int value) | returns Frame Type string description 
##            ptypes =  PacketDataClass()
##            
##            # // Gets Protocol String 
##            protoStr = ptypes.get_prototye(proto)[0]
##            # // Get Ethernet Frame Name and Numeric representation
##            ethname,ethnum, ethnumstr = ptypes.get_ethtype(etype)
##            
##            # // create a full packet 
##            fullpacket = pheader+pdata
##
##            # // Text Output 
##            outfd.write("Packets Found: " + str(counter) + "\n")
##            
##            outfd.write("ProcName: {0} PID: {1}  Base Address: {2}  End Address: {3}\n".format(procName, pid, base_addr, end_addr))
##            outfd.write(ethname + " (" + ethnumstr + ") " + "\n")
##            outfd.write("Protocol "+ protoStr + " " + "("+str(proto)+")" + "\n")
##            outfd.write("Src: " + source +":" + srcport + " (" +macsrc+"), " + "Dst: " + dest +":" + destport + " (" +macdst+")" +"\n""")            
##            outfd.write("Data " + "(" + str(len(pheader+pdata)) + " Bytes" +")" + "\n" )
##            
##            for offset, hextext, chars in utils.Hexdump(fullpacket):
##                outfd.write("{0:#010x}  {1:<48}  {2}\n".format(offset, hextext, ''.join(chars)))
##                
##            # // Build and save to the pcap file 
##            if self._config.SAVE_PCAP:
##                eth = dpkt.ethernet.Ethernet(fullpacket)
##                pcw.writepkt(eth)
##
##            # // Raw Packets saved to --dump-dir 
##            # //Format is PACKET NUM __ visual reminded __ IPSRC __ IP SRCPORT __ DST __IP DESTPORT __ PROTOCOL . BIN  
##            # // Example: ProcName_PID__0__pktnum__SRC_210.146.64.4_20480__DST_81.131.67.131_42762__TCP.bin
##            if self._config.SAVE_RAW:
##                filename =  procName + "__"+ str(pid)+ "__"+str(counter) + "__pktnum" + "__SRC_" + source +"_" + srcport  +"__DST_" + dest +"_" + destport + "__" + protoStr + ".bin"
##                fh = open(os.path.join(self._config.DUMP_DIR, filename), 'wb')
##                fh.write(fullpacket)
##                fh.close()
##                
##            outfd.write("\n")
##            counter += 1
##            
##            outfd.write("Packets Found: " + str(counter) + "\n")
##        if self._config.SAVE_PCAP:
##            pcw.close()
##        
##    # // Make Physical to Process translation 
##    # // First get pid, task and pages
##    def getPTP(self):    
##        try:
##            tasks = taskmods.DllList.calculate(self)
##            for task in tasks:
##                if task.UniqueProcessId:
##                    pid = task.UniqueProcessId
##                    task_space = task.get_process_address_space()
##                    pages = task_space.get_available_pages()
##                yield pid, task, pages            
##        except:
##            yield False 
##
##                
##
##    # // Find the ProcName/PID by searching the pagedata.  
##    # // pktoffset = physical packet offset.
##    # // If this is between a page address base address + size 
##    # // Return the last process associated with this loop
##    def mapOffsetToAddr(self, outfd, pktoffset, ptpobj):
##        for pid, task, pagedata in ptpobj:
##            task_space = task.get_process_address_space()
##            currentProc = ("{0} pid: {1:6}\n".format(task.ImageFileName, pid))
##            offset = 0 
##            for p in pagedata:
##                pa = task_space.vtop(p[0])
##                if pa != None:
##                    if pktoffset >= pa and pktoffset <= pa+p[1]: 
##                        mapAddrList = [str(task.ImageFileName), int(pid), pa, p[1]]
##                        return mapAddrList
##                    else:
##                        offset += p[1]
##        return None 