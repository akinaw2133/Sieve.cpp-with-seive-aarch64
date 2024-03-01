import os
import optparse
import sys

import m5
from m5.defines import buildEnv

from m5.objects import *
from m5.util import addToPath, fatal

from common import Options
from common import Simulation
from common import CacheConfig
from common.Caches import *
from common.cpu2000 import *
#from FUPool import FUPool

### Create the Options Parser
parser = optparse.OptionParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)

### Parse for command line options
(options, args) = parser.parse_args()
## Override some options values to match the ARM Cortex A9

options.cpu_type = "detailed"   # The A15 is an OutOfOrder CPU
options.cpu_clock = "2GHz"
options.num_cpus = 1

options.caches = 1              # Symmetric, L1 caches
options.cacheline_size = 64

options.l1i_size = "32kB"
options.l1i_assoc = 2

options.l1d_size = "32kB"
options.l1d_assoc = 2

options.l2cache = 1
options.l2_size = "4MB"
options.l2_assoc = 1

if args:
    print ("Error: script doesn't take any positional arguments")
    sys.exit(1)

### Setup the workload to execute on the CPUs
multiprocesses = []
apps = []

if options.cmd:
    process = LiveProcess()
    process.executable = options.cmd
    process.cmd = [options.cmd] + options.options.split()
    multiprocesses.append(process)
else:
    print >> sys.stderr, "No workload specified. Exiting!\n"
    sys.exit(1)

### Optionally pipe output to a file

if options.input != "":
    process.input = options.input
if options.output != "":
    process.output = options.output
if options.errout != "":
    process.errout = options.errout

# By default, set workload to path of user-specified binary
workloads = options.cmd
numThreads = 1

if options.cpu_type == "detailed" or options.cpu_type == "Out-of-Order":
    #check for Simultaneous Multithreaded workload
    workloads = options.cmd.split(';')
    if len(workloads) > 1:
        process = []
        smt_idx = 0
        inputs = []
        outputs = []
        errouts = []
if options.input != "":
            inputs = options.input.split(';')
        if options.output != "":
            outputs = options.output.split(';')
        if options.errout != "":
            errouts = options.errout.split(';')

        for wrkld in workloads:
            smt_process = LiveProcess()
            smt_process.executable = wrkld
            smt_process.cmd = wrkld + " " + options.options
            if inputs and inputs[smt_idx]:
                smt_process.input = inputs[smt_idx]
            if outputs and outputs[smt_idx]:
                smt_process.output = outputs[smt_idx]
            if errouts and errouts[smt_idx]:
                smt_process.errout = errouts[smt_idx]
            process += [smt_process, ]
            smt_idx += 1
    numThreads = len(workloads)

### Using the provided options, setup the CPU and cache configuration

(CPUClass, test_mem_mode, FutureClass) = Simulation.setCPUClass(options)
CPUClass.numThreads = numThreads;

### Select the CPU count

np = options.num_cpus
### Assemble the system

system = System(cpu = [CPUClass(cpu_id=i) for i in xrange(np)],
                physmem = SimpleMemory(range=AddrRange("512MB")),
                membus = SystemXBar(), mem_mode = test_mem_mode)

# Create a top-level voltage domain
system.voltage_domain = VoltageDomain(voltage = options.sys_voltage)

# Create a source clock for the system and set the clock period
system.clk_domain = SrcClockDomain(clock =  options.sys_clock,
                                   voltage_domain = system.voltage_domain)

# Create a CPU voltage domain
system.cpu_voltage_domain = VoltageDomain()

# Create a separate clock domain for the CPUs
system.cpu_clk_domain = SrcClockDomain(clock = options.cpu_clock,
                                       voltage_domain =
                                       system.cpu_voltage_domain)

### Reconfigure the CPU to match the Cortex A15 specs

cpu = system.cpu[0]
cpu.decodeWidth = 3     # 2 way superscalar frontend
cpu.fetchWidth = 3
cpu.issueWidth = 3
cpu.dispatchWidth = 3

#Functional Unit definitions taken from FuncUnitConfig.py, modified to match A9
class IntALU(FUDesc):
    opList = [ OpDesc(opClass='IntAlu') ]
    count = 2

class IntMultDiv(FUDesc):
    opList = [ OpDesc(opClass='IntMult', opLat=3),
               OpDesc(opClass='IntDiv', opLat=20) ]
    count = 1

class RdWrPort(FUDesc):
    opList = [ OpDesc(opClass='MemRead'), OpDesc(opClass='MemWrite') ]
    count = 1

# Attach the Functional units
cpu.fuPool = FUPool(FUList=[IntALU(), IntMultDiv(), RdWrPort()])

### Sanity checks

if options.fastmem and (options.caches or options.l2cache):
    fatal("You cannot use fastmem in combination with caches!")
for i in xrange(np):
    if len(multiprocesses) == 1:
        system.cpu[i].workload = multiprocesses[0]
    else:
        system.cpu[i].workload = multiprocesses[i]

    if options.fastmem:
        system.cpu[i].fastmem = True

    if options.checker:
        system.cpu[i].addCheckerCpu()

### Connect up system memory

system.system_port = system.membus.slave
system.physmem.port = system.membus.master
CacheConfig.config_cache(options, system)

### Create the root, instantiate the system, and run the simulation

root = Root(full_system = False, system = system)
Simulation.run(options, root, system, FutureClass)


