from SimPy.Simulation import *
from numpy.random import seed, uniform, exponential, poisson
import numpy as np
import random
import argparse
import matplotlib.pyplot as plt
from itertools import chain




# First Name:   Dan 
# Last Name:    Brown
# BU ID:        U63795118

#You can add any extra helper methods to these classes as you see fit#.


#You must modify this class#
class Parameters:
    '''In this class, you must just define the following variables of your distribution:
    These variables will be hardcoded with values. Please refer to the assignment handout what
    these values must be. You can use the values appropiately in your code by calling Parameters.NAME_OF_VARIABLE
    --For Poisson Arrivals and Exponential Service Time
      1) lambda for poisson arrivals
      2) Ts for service time

    --For Uniform Arrivals and Uniform Service Time
       3) interarrivalTimeMin and interarrivalTimeMax for Uniform distribution.
       4) serviceTimeMin and serviceTimeMax for Uniform distribution.
    5. numberOfServers in your computing system
    6. simulationTime in hrs. '''
    # For Poisson Arrivals and Exponential Service Time:  
    interArrival = 0
    
    TsCPU = 0.02
    TsNet = 0.025
    TsDisk = 0.1

    # Other parameters:
    numberOfServers = 1
    simulationTime = 0          # in minutes (120 min = 2 hours)
    RandomSeed = 123
    steadyState = 0
    #statistics
    wLen = 0
    wLength = []
    wLengthMon = []
    Tw = []
    wait = 0
    Arrivals_cpu = []
    Arrivals_disk = []
    Arrivals_net = []
    exits = []
    exitsAvgs = []
    response_times = []



##### Processes #####
# Customer
class Packet(Process):
    state = "cpu"

    def behavior_of_single_packetExp(self, cpu, disk, net):
        
        if self.state == "cpu":
            #print("disk")
            arriveCpu = now()
            Parameters.Arrivals_cpu.append(arriveCpu)   #add all times of arrival of packet to a list
            
            Parameters.wLen += 1       # helps calculate length of queue; increment queue (number of packets waiting) length counter

            #if not(self.name in chain(*Parameters.response_times)):
                #Parameters.response_times.append((self.name, arriveCpu))
            
            yield request,self,cpu 
                                    
            # wait before collecting data (wait for system to reach steady state):
            #if now() > Parameters.steadyState:
            #Parameters.wait = now()-arriveCpu
            #wM.observe(wait)

            Ts = exponential(Parameters.TsCPU)

            yield hold,self,Ts                          
            yield release,self,cpu
            Parameters.wLen -= 1    # packet gets serviced, therefore, decrement number of packets waiting by one 
            
            #*** CONDITIONALS for cpu****
            step_rnd = uniform(0,1)
            
            #if ((step_rnd >= 0.4) and (step_rnd < 0.9)):
                #packet exits system 
            if (step_rnd < 0.4):
                #packet goes to network
                #print("cpu to network")
                p = Packet(name = self.name)
                p.state = "net"
                activate(p,p.behavior_of_single_packetExp(cpu, disk, net))
            elif ((step_rnd >= 0.4) and (step_rnd < 0.9)):
                #packet exits system 
                Parameters.exits.append(now())    
            elif step_rnd >= 0.9:
                #packet goes to disk
                #print("cpu to disk")
                p = Packet(name = self.name)
                p.state = "disk"
                activate(p,p.behavior_of_single_packetExp(cpu, disk, net))
                
        elif self.state == "disk":
            #print("disk")
            #arriveDisk = now()
            Parameters.Arrivals_disk.append(now())
            
            yield request,self,disk
                                    
            #wait = now()-arriveDisk
            #wM.observe(wait)

            Ts = exponential(Parameters.TsDisk)

            yield hold,self,Ts                          
            yield release,self,disk
            
            #*** CONDITIONALS for disk****
            step_rnd = uniform(0,1)
               
            if step_rnd >= 0.5:
                #packet goes to cpu
                #print("disk to cpu")
                p = Packet(name = self.name)
                p.state = "cpu"
                activate(p,p.behavior_of_single_packetExp(cpu, disk, net))
                
            else:
                #packet goes to network
                #print("disk to network")
                p = Packet(name = self.name)
                p.state = "net"
                activate(p,p.behavior_of_single_packetExp(cpu, disk, net))

        elif self.state == "net":
            #print("net")
            #arriveNet = now()
            Parameters.Arrivals_net.append(now())
            
            yield request,self,net
                                    
            #wait = now()-arrive
            #wM.observe(wait)

            Ts = exponential(Parameters.TsNet)

            yield hold,self,Ts                          
            yield release,self,net
            
            #*** CONDITIONALS for netowrk****
            # In this case, network packets have 100% chance to (automatically) go back to cpu
            
            #packet goes to cpu
            #print("network to cpu")
            p = Packet(name = self.name)
            p.state = "cpu"
            activate(p,p.behavior_of_single_packetExp(cpu, disk, net))
        



# Packet Generator class.
class PacketGenerator(Process):
        # for experimental dist arrival rate
        def createPacketsExp(self, cpu, disk, net):
            i = 0
            while True:
                #creates new packet
                rnd = exponential(Parameters.interArrival)
                yield hold, self, rnd
                p = Packet(name = "Packet " + str(i))
                activate(p,p.behavior_of_single_packetExp(cpu, disk, net))      # behavior for packet using exponential dist
                i+= 1


# Monitor Generator class.
class MonitorGen(Process):
        def createMon(self,cpu, disk, net):
            
            i = 0
            # create poisson distribution (with lambda = 1, for 100 seconds)
            rnd_list = poisson(1,Parameters.simulationTime - Parameters.steadyState)
            #print "rnd list" , len(rnd_list)
            #print rnd_list
            for x in rnd_list:
                yield hold, self, x
                #print(Parameters.wLen)
                Parameters.wLength.append(Parameters.wLen)
                
                #using monitoring object:
                Parameters.wLengthMon.append(len(cpu.waitQ))

                # this is for getting exit rate for the system
                if (len(Parameters.exits) > 0):
                    diff_exits = np.diff(Parameters.exits)
                    exitAvgTime = (sum(diff_exits) / float(len(diff_exits)))
                    exitAvg = (1.0/exitAvgTime)
                else:
                    exitAvg = 0
                Parameters.exitsAvgs.append(exitAvg)
                Parameters.exits = []   #reset for next average calculation
                i+= 1
        


#You do not need to modify this class.
class ComputingSystem(Resource):
    pass




def modelMM2():
    global f
    f = open('data.txt', 'w')
    #print "Creating experiment for MM2"
    
    #Parameters.numberOfServers = 2     
    
    seed(Parameters.RandomSeed)
    #cs = Resource(capacity=Parameters.numberOfServers,monitored=True, monitorType=Monitor)

    
    cpu=ComputingSystem(capacity=2,monitored=True, monitorType=Monitor) 
    disk=ComputingSystem(capacity=1,monitored=True, monitorType=Monitor)
    net=ComputingSystem(capacity=1,monitored=True, monitorType=Monitor) 
    
    
    global wM
    wM = Monitor()
    
    initialize()

    s = PacketGenerator('Process')
    activate(s, s.createPacketsExp(cpu, disk, net), at=0.0)

    Mon = MonitorGen('Process')     # create instance of monitor class
    activate(Mon, Mon.createMon(cpu, disk, net), at= Parameters.steadyState)
    
    simulate(until= Parameters.simulationTime)

   # print "Wlength" , Parameters.wLength
    #print (len(Parameters.wLength))
    
    #avg_wLength = (sum(Parameters.wLength) / float(len(Parameters.wLength)))
    #print "Average length of queue (w) is: ", avg_wLength
    
    avg_wLength2 = (sum(Parameters.wLengthMon) / float(len(Parameters.wLengthMon)))
    print "Average length of CPU queue with Monitor (w) is: ", avg_wLength2

    sample_deviation_Cpu = np.std(Parameters.wLengthMon)
    print "sample deviation for cpu requests waiting (w) is " , sample_deviation_Cpu
    
    #------ lambdas for subsystems
   
   # difference between time of arrivals of a packet and next packet
    time_diff_cpu = np.diff(Parameters.Arrivals_cpu)
    time_diff_disk = np.diff(Parameters.Arrivals_disk)
    time_diff_net = np.diff(Parameters.Arrivals_net)
    # avg of the time-differences will give us the average time between packets;
    # So, in order to get lambda (the rate of arrivals per second), we need to divide
    # 1 by the avg of the time-differences
    avg_cpu_times = (sum(time_diff_cpu) / float(len(time_diff_cpu)))
    avg_disk_times = (sum(time_diff_disk) / float(len(time_diff_disk)))
    avg_net_times = (sum(time_diff_net) / float(len(time_diff_net)))
    
    lambda_cpu = (1.0/avg_cpu_times)
    lambda_disk = (1.0/avg_disk_times)
    lambda_net = (1.0/avg_net_times)

    #print "time list for cpu" , time_diff_cpu
    print "lambda for cpu: " , lambda_cpu
    print "lambda for disk: " , lambda_disk
    print "lambda for net: " , lambda_net
    
    
    #plotting code:
    # just uncomment out one of these to run and see the corresponding graphs
    '''
    # for Hw4 part 2a
    # for this one, set Parameters.simulationTime to 100, and Parameters.steadyState = 0
    x = [z+1 for z in range(0,Parameters.simulationTime)]
    y = Parameters.wLengthMon
    plt.scatter(x, y)
    plt.xlabel('Time (in seconds)')
    plt.ylabel('Number of requests waiting in CPU (w)')
    plt.show()
    
    
    # for Hw4 part 2b
    # for this one, set Parameters.steadyState = 0 in the model() function, and set Parameters.steadyState to something larger than 100
    x = [z+1 for z in range(Parameters.steadyState,Parameters.simulationTime)]
    y = Parameters.exitsAvgs
    plt.scatter(x, y)
    plt.xlabel('Time (in seconds)')
    plt.ylabel('Exiting rate for the system')
    plt.show()
    '''
    

    f.close()
    
    #return w
    
    

#You can modify this model method#.
# *This is the experiment (where we initialize everything and run it; this is not the same as a model for MVC
#   (Model View Controller) )
def model():
    
    Parameters.simulationTime = 140      #higher simulation times => better aproximation to analytical
    Parameters.steadyState = 40        # change this to 0 when testing out my plotting code for graphing
    
    Parameters.RandomSeed = 123     # just to make sure
    Lambda = 40   # 40 times per second
    Parameters.interArrival = 1.0/Lambda
    
    Parameters.TsCPU = .02
    Parameters.TsDisk = .1
    Parameters.TsNet = .025
    
    modelMM2()
           
    
    
    

#Change the below, as per the requirements of the assignment.
if __name__ == "__main__":
    model()
