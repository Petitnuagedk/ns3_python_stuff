#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 13:31:05 2024

@author: hledirach

usefull like : https://www.nsnam.org/docs/release/3.19/doxygen/manet-routing-compare_8cc_source.html
               https://www.nsnam.org/docs/models/html/index.html
"""

from matplotlib import pyplot as plt
from ns import ns


#%%
coordinatesHistoric = []

# Create an event in C++ for the following python function
ns.cppyy.cppdef("""
   namespace ns3
   {
       EventImpl* pythonMakeEvent(void (*f)(NodeContainer&), NodeContainer& nodes)
       {
           return MakeEvent(f, nodes);
       }
   }
""")



#%%
def getNodeCoordinates(nodeContainer : ns.NodeContainer) -> None:
    global coordinatesHistoric

    coordinates = {}
    for node_i in range(nodeContainer.GetN()):
        node = nodeContainer.Get(node_i).__deref__()
        mobility = node.GetObject[ns.MobilityModel]().__deref__()
        position = mobility.GetPosition()
        coordinates[f"Node {node.GetId()}"] = ((position.x), (position.y))
    coordinatesHistoric.append((ns.Simulator.Now().GetSeconds(), coordinates))

    # Re-schedule after every 1 second
    event = ns.pythonMakeEvent(getNodeCoordinates, nodeContainer)
    ns.Simulator.Schedule(ns.Seconds(1), event)
    
def animateSimulation():
    global coordinatesHistoric
    
    # Save a copy and clean historic for the next animation
    coordinatesHistoricCopy = coordinatesHistoric
    coordinatesHistoric = []
    
    # Animate coordinates from the simulation
    from matplotlib.animation import FuncAnimation
    
    fig = plt.figure()
    plots = {}
    def init():
        # Initialize animation artists
        for (node, coordinate) in coordinatesHistoricCopy[0][1].items():
            plots[node] = plt.scatter(*coordinate, label=node)

        # Determine animation bounds
        x_bounds = [9999,0]
        y_bounds = [9999,0]
        for i in range(len(coordinatesHistoricCopy)):
            for (node, coordinate) in coordinatesHistoricCopy[i][1].items():
                if (coordinate[0] > x_bounds[1]):
                    x_bounds[1] = coordinate[0]
                if (coordinate[1] > y_bounds[1]):
                    y_bounds[1] = coordinate[1]
                    
        # Add a margin to the bounds
        x_bounds[0] -= 1
        y_bounds[0] -= 1
        x_bounds[1] += 1
        y_bounds[1] += 1
        
        # Set animation bounds
        plt.xlim(x_bounds)
        plt.ylim(y_bounds)

    def animate(i):
        
        for (node, coordinate) in coordinatesHistoricCopy[i][1].items():
            plots[node].set_offsets(coordinate)
    
    # Animate the historic of coordinates
    anim = FuncAnimation(fig, animate, init_func=init,
                             frames = len(coordinatesHistoricCopy),
                             interval = 100, repeat=True)
    
    # Display the interactive animation
    plt.show(anim)
    
    # Prevent plotting the final frame as a static image
    plt.close()
    return

#%%
def setup(scenario):
        

    if scenario == "test":
        nodes, interfaces = mob_wifi_setup()
    
    return nodes, interfaces


def mob_wifi_setup():
    """
    This fonction creat two nodes in a common network (subnet mask 255.255.255.0) and 

    Parameters
    ----------
    nodes : TYPE
        DESCRIPTION.

    Returns
    -------
    nodes : TYPE
        DESCRIPTION.
    interfaces : TYPE
        DESCRIPTION.

    """
    
    nodes = ns.network.NodeContainer()
    nodes.Create(5)
    # Set positions for nodes
    positions = ns.mobility.ListPositionAllocator()
    for i in range(nodes.GetN()):
        position = ns.core.Vector(i * 10, 0, 0)  # Adjust coordinates as needed
        positions.Add(position)
    
    mobility = ns.mobility.MobilityHelper()
    mobility.SetMobilityModel ("ns3::WaypointMobilityModel")
    mobility.SetPositionAllocator(positions)
    mobility.Install(nodes)
    
    
    #################
    
    
    # Create a point-to-point helper : only for N ----- N
    # pointToPoint = ns.point_to_point.PointToPointHelper()
    # pointToPoint.SetDeviceAttribute("DataRate", ns.core.StringValue("5Mbps"))
    # pointToPoint.SetChannelAttribute("Delay", ns.core.StringValue("2ms"))
    # Install network devices and link them
    # devices = pointToPoint.Install(nodes) 
    # Add IP stack to nodes
    
    channel = ns.wifi.YansWifiChannelHelper.Default()
    
    # ////2/////
    channel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel")
    channel.AddPropagationLoss ("ns3::FriisPropagationLossModel")
    # ////2/////
    #Create a channel by using defrault Yet Another Network Simulator
    #channel model, this channel servers for communication between wireless nodes

    phy = ns.wifi.YansWifiPhyHelper()
    #Create a helper object to configure physical layer of Wifi nodes
    #Still use Yans
    phy.SetChannel(channel.Create())
    #Related to phy from previousline, create the channel with
    #physical layer. Outter line is setting chaneel for wifi nodes
    #By default, the WifiHelper (the typical use case for WifiPhy creation) will
    #configure the WIFI_STANDARD_80211ax standard by default. 

    #####Standard definiation undefined
    # ns.wifi.SetStandard(WIFI_STANDAR4.Two clients with one server (UDP)----How two client communicate through the server???​D_80211n)
    phy.Set("ChannelSettings", ns.core.StringValue("{0, 40, BAND_5GHZ, 0}"))
    #the operating channel will be channel 38 in the 5 GHz band,
    #which has a width of 40 MHz, and the primary20 channel will be the 20 MHz
    #subchannel with the lowest center frequency (index 0).

    mac = ns.wifi.WifiMacHelper()
    # ////2/////
    mac.SetType ("ns3::AdhocWifiMac")
    # ////2/////
    # mac = ns.wifi.WifiMacHelper()
    #Create a helper object to configure MAC layer of wifi nodes
    ssid = ns.wifi.Ssid("ns-3-ssid")
    #Create a ssid for wifi network, which identifies a wifi network

    wifi = ns.wifi.WifiHelper()
    
    # ////2/////
    wifi.SetRemoteStationManager ("ns3::ConstantRateWifiManager",
                                 "DataMode", ns.core.StringValue("DsssRate11Mbps"),
                                 "ControlMode", ns.core.StringValue ("DsssRate11Mbps"))
    # ////2/////
    #Create a helper object to set up wifi network

    mac.SetType(
        "ns3::StaWifiMac", "Ssid", ns.wifi.SsidValue(ssid), "ActiveProbing", ns.core.BooleanValue(False)
    )
    #Set the type of MAC layer for station devices as 'ns3::StaWifiMac'
    #Applied SSID for station device from precious definition
    #Disable active probling from station device with ns.core.Boolean
    staDevices = wifi.Install(phy, mac, nodes)
    #Connect station device with station wifi nodes, applying precious
    #physical and MAC layer settings, store them in staDevices
    stack = ns.internet.InternetStackHelper()
    #Create an internetstack helper object to configure and install
    #internet protocol stacks on nodes
    stack.Install(nodes)
    
    stack = ns.internet.InternetStackHelper()
    stack.Install(nodes)
    ns.internet.Ipv4GlobalRoutingHelper.PopulateRoutingTables()
    # Assign IP addresses
    address = ns.internet.Ipv4AddressHelper()
    address.SetBase(ns.network.Ipv4Address("10.1.1.0"), ns.network.Ipv4Mask("255.255.255.0"))
    interfaces = address.Assign(staDevices)
    
    return nodes, interfaces

def coms_UDP(node_emit,node_reciev, interfaces, it):
    """
    Set up the UDP app for the nodes couples

    Parameters
    ----------
    node_emit : node object from ns library
        The node use as the server
    node_reciev : index of the node object from ns library
        The node use as the client
    interfaces : Address object from ns library
        Interfaces of the nodes (holds their addresses)

    Returns
    -------
    None.

    """
    port = it
    echoServer = ns.applications.UdpEchoServerHelper(port)
    serverApps = echoServer.Install(node_emit)
    serverApps.Start(ns.core.Seconds(1.0))
    serverApps.Stop(ns.core.Seconds(10.0))
    
    # enable printing out the messages as packets are sent and recieved during simulation
    ns.core.LogComponentEnable("UdpEchoClientApplication", ns.core.LOG_LEVEL_ALL)
    ns.core.LogComponentEnable("UdpEchoServerApplication", ns.core.LOG_LEVEL_ALL)
    
    echoClient = ns.applications.UdpEchoClientHelper(interfaces.GetAddress(node_reciev).ConvertTo(), port)
    echoClient.SetAttribute("MaxPackets", ns.core.UintegerValue(5))
    echoClient.SetAttribute("Interval", ns.core.TimeValue(ns.core.Seconds (1.0)))
    echoClient.SetAttribute("PacketSize", ns.core.UintegerValue(1024))
    
    clientApps = echoClient.Install(node_emit)
    clientApps.Start(ns.core.Seconds(1.0))
    clientApps.Stop(ns.core.Seconds(10.0))
    return
#%%

def behavior_test1(node_A, node_B, dirChange):
    """
    Update the position of the nodes in the scenario test 1

    Parameters
    ----------
    currPos : ns.Vector
        Coordinates of the current position (2D)
    node_indx : int
        Index of the node that needs nex coordinates

    Returns
    -------
        None.

    """
    
    r = [node_A,node_B]
    for n in r:
        if n is node_A:
            mobility = n.GetObject[ns.WaypointMobilityModel]().__deref__()
            currPos = mobility.GetPosition()
            time = ns.Seconds(0.5)
            
            nextPos = ns.Vector(currPos.x,
                                currPos.y+(2 if dirChange else -2),
                                0)     
            time = ns.Seconds(1+time.GetSeconds())
            wpt = ns.Waypoint (time, nextPos);
            mobility.AddWaypoint(wpt)
            currPos = nextPos
        if n is node_B:
            mobility = n.GetObject[ns.WaypointMobilityModel]().__deref__()
            currPos = mobility.GetPosition()
            time = ns.Seconds(0.5)
            nextPos = ns.Vector(currPos.x,
                                currPos.y,
                                0)
            time = ns.Seconds(1+time.GetSeconds())
            wpt = ns.Waypoint (time, nextPos);
            mobility.AddWaypoint(wpt)
            currPos = nextPos
    return
#%%

def animateWaypointWalkNodes(scneario):
    print("starting...")

    ns.Simulator.Destroy()
    
    nodes, interfaces = setup(scenario)
    print("nodes created, starting simulation...")
    
    for node_i in range(nodes.GetN()-1):
        it = 5001
        for node_j in range(node_i +1, nodes.GetN()):
            print("starting com setup between node ", node_i, " and node ", node_j)
            node_emit = nodes.Get(node_i).__deref__()
            coms_UDP(node_emit, node_j, interfaces,it)
            it+=1
    
    print("com is setup")
    # We need to setup the waypoints each node will walk on
    # In this case, we are going to make them walk in
    # the DVD Logo fashion
    behavior = "t"
    if behavior == "test":
        behavior_test1(nodes.Get(0).__deref__(),nodes.Get(1).__deref__(),True)
    else:
        for node_i in range(nodes.GetN()):
            node = nodes.Get(node_i).__deref__()
            mobility = node.GetObject[ns.WaypointMobilityModel]().__deref__()
            currPos = mobility.GetPosition()
            time = ns.Seconds(0.5)
            DIR = [1,1]
            while time.GetSeconds() < 100:
                # Behavior model goes here
                
                dirChanged = False
                
                nextPos = ns.Vector(currPos.x+(2 if DIR[0] else -2),
                                    currPos.y+(2 if DIR[1] else -2),
                                    0)
                if DIR[0] == 0:
                    if nextPos.x < 0:
                        DIR[0] = 1
                        dirChanged = True
                else:
                    if nextPos.x > 100:
                        DIR[0] = 0
                        dirChanged = True
    
                if DIR[1] == 0:
                    if nextPos.y < 0:
                        DIR[1] = 1
                        dirChanged = True
                else:
                    if nextPos.y > 100:
                        DIR[1] = 0
                        dirChanged = True
    
                # Skip next position since it goes out of bounds
                if dirChanged:
                    continue
                
                time = ns.Seconds(1+time.GetSeconds())
                wpt = ns.Waypoint (time, nextPos);
                mobility.AddWaypoint(wpt)
                currPos = nextPos

    # Schedule getNodeCoordinates to run after 1 second of simulation
    event = ns.pythonMakeEvent(getNodeCoordinates, nodes)
    ns.Simulator.Schedule(ns.Seconds(1), event)
    
    #monitor data  look into GnuplotHelper
    flowm = ns.flow_monitor.FlowMonitorHelper()
    flowm.InstallAll()
    # Run simulation for 100 virtual seconds
    ns.Simulator.Stop(ns.Seconds(100))
    ns.Simulator.Run()
    flowm.SerializeToXmlFile("QoS_Report.xml", True, True);
    animateSimulation()
#%%

scenario = "test"
animateWaypointWalkNodes(scenario)

