__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"


"""
Code is original from
 https://github.com/esmini/esmini/blob/2e438be3b3a176dafd296fa5e41742f886868e6f/scripts/udp_driver/udp_osi_common.py.
 Exemplary usage please also refer to the esmini repository. 
 
 * If you want to use the esmini UDPDriverController in combination with OSI, you need to:
 1. extend the OpenSCENARIO file with the UDP functionalities
     - add the Controller Catalog into the
        <CatalogLocations>

        <ControllerCatalog>
                <Directory path=<"your local path to the ESMINI UDP controller module>
        </ControllerCatalog>
    
        </CatalogLocations>
     -  extend the ego vehicle entity section like this example:
    <Entities>
        <ScenarioObject name="Ego">
               <CatalogReference catalogName="VehicleCatalog" entryName="$HostVehicle"/>
               <ObjectController>
                  <CatalogReference catalogName="ControllerCatalog" entryName="UDPDriverController">
                     <ParameterAssignments>
                         <ParameterAssignment parameterRef="BasePort" value="53995" />
                         <ParameterAssignment parameterRef="ExecMode" value="asynchronous" /> ## or synchronous
                     </ParameterAssignments>
                  </CatalogReference>
                </ObjectController>
        </ScenarioObject>
        ...
     </Entities>
 2. start the OSI Receiver and UDP sender together with your external driver models/simulators 
    (the --osi_receiver_ip is set to 127.0.0.1 by default)
 3. in another terminal window, run the scenario converter script 

"""

from socket import *
import struct

from osi3.osi_groundtruth_pb2 import GroundTruth


input_modes = {
    "driverInput": 1,
    "stateXYZHPR": 2,
    "stateXYH": 3,
    "stateH": 4,
}

base_port = 53995


class UdpSender:
    def __init__(self, ip="127.0.0.1", port=base_port):
        # Create a UDP socket
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.addr = (ip, port)

    def send(self, msg):
        self.sock.sendto(msg, self.addr)

    def close(self):
        self.sock.close()


class UdpReceiver:
    def __init__(self, ip="127.0.0.1", port=base_port, timeout=-1):
        self.buffersize = (
            8208  # MAX OSI data size (contract with esmini) + header (two ints)
        )
        # Create a UDP socket
        self.sock = socket(AF_INET, SOCK_DGRAM)
        if timeout >= 0:
            self.sock.settimeout(timeout)
        # Bind to address and ip
        self.sock.bind((ip, port))

    def receive(self):
        bytesAddressPair = self.sock.recvfrom(self.buffersize)
        message = bytesAddressPair[0]
        return message

    def close(self):
        self.sock.close()


class OSIReceiver:
    def __init__(self):
        self.udp_receiver = UdpReceiver(port=48198)
        self.osi_msg = GroundTruth()

    def receive(self):
        done = False
        next_index = 1
        complete_msg = b""

        # Large nessages might be split in multiple parts
        # esmini will add a counter to indicate sequence number 0, 1, 2...
        # negative counter means last part and message is now complete
        while not done:
            # receive header
            msg = self.udp_receiver.receive()

            # extract message parts
            header_size = 4 + 4  # counter(int) + size(unsigned int)
            counter, size, frame = struct.unpack(
                "iI{}s".format(len(msg) - header_size), msg
            )
            # print('counter {} size {}'.format(counter, size))

            if not (len(frame) == size == len(msg) - 8):
                print("Error: Unexpected invalid lengths")
                return

            if counter == 1:  # new message
                complete_msg = b""
                next_index = 1

            # Compose complete message
            if counter == 1 or abs(counter) == next_index:
                complete_msg += frame
                next_index += 1
                if counter < 0:  # negative counter number indicates end of message
                    done = True
            else:
                next_index = 1  # out of sync, reset

        # Parse and return message
        self.osi_msg.ParseFromString(complete_msg)
        return self.osi_msg

    def close(self):
        self.udp_receiver.close()
