#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 13:31:05 2024

@author: hledirach
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
        x_bounds = [0,0]
        y_bounds = [0,0]
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
def setup(n_nodes, scenario):
        
    nodes = ns.network.NodeContainer()
    nodes.Create(n_nodes)
    if scenario == "test":
        nodes, interfaces = scenario_test(nodes)
    
    return nodes, interfaces


def scenario_test(nodes):
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
    # Set positions for nodes
    positions = ns.mobility.ListPositionAllocator()
    for i in range(n_nodes):
        position = ns.core.Vector(i * 10, 0, 0)  # Adjust coordinates as needed
        positions.Add(position)
    
    mobility = ns.mobility.MobilityHelper()
    mobility.SetMobilityModel ("ns3::WaypointMobilityModel")
    mobility.SetPositionAllocator(positions)
    mobility.Install(nodes)
    
    # Create a point-to-point helper
    pointToPoint = ns.point_to_point.PointToPointHelper()
    pointToPoint.SetDeviceAttribute("DataRate", ns.core.StringValue("5Mbps"))
    pointToPoint.SetChannelAttribute("Delay", ns.core.StringValue("2ms"))
    
    # Install network devices and link them
    devices = pointToPoint.Install(nodes)
    
    # Add IP stack to nodes
    stack = ns.internet.InternetStackHelper()
    stack.Install(nodes)
    
    # Assign IP addresses
    address = ns.internet.Ipv4AddressHelper()
    address.SetBase(ns.network.Ipv4Address("10.1.1.0"), ns.network.Ipv4Mask("255.255.255.0"))
    interfaces = address.Assign(devices)
    
    
    return nodes, interfaces

def coms_UDP(node_emit,node_reciev, interfaces, it):
    """
    Set up the UDP app for the nodes couples

    Parameters
    ----------
    node_emit : node object from ns library
        The node use as the client
    node_reciev : node object from ns library
        The node use as the server
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

def animateWaypointWalkNodes(n_nodes):
    print("starting...")

    ns.Simulator.Destroy()
    
    nodes, interfaces = setup(n_nodes,"test")
    print("nodes created, starting simulation...")
    
    for node_i in range(n_nodes-2):
        print("starting com setup...")

        it = 5001
        for node_j in range(node_i +1, n_nodes):
            node_emit = nodes.Get(node_i).__deref__()
            node_reci = nodes.Get(node_j).__deref__()
            coms_UDP(node_emit, node_reci, interfaces,it)
        it+=1
        
    # We need to setup the waypoints each node will walk on
    # In this case, we are going to make them walk in
    # the DVD Logo fashion
    
    for node_i in range(nodes.GetN()):
        node = nodes.Get(node_i).__deref__()
        mobility = node.GetObject[ns.WaypointMobilityModel]().__deref__()
        currPos = mobility.GetPosition()
        time = ns.Seconds(0.5)
        DIR = [1,1]
        while time.GetSeconds() < 100:
            dirChanged = False
            nextPos = ns.Vector(currPos.x+(2 if DIR[0] else -2),
                                currPos.y+(2 if DIR[1] else -2),
                                0
                                )
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
    
    
    # Run simulation for 100 virtual seconds
    ns.Simulator.Stop(ns.Seconds(100))
    ns.Simulator.Run()

    animateSimulation()
#%%
n_nodes = 2
animateWaypointWalkNodes(n_nodes)
