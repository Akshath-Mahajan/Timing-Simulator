# -------------------------------------------------------------
# Title   : Vector Processor - Timing Simulator
# Authors : Rugved Mhatre (rrm9598), Akshath Mahajan (avm6288)
# -------------------------------------------------------------

import os
import argparse

class Config(object):
    def __init__(self, iodir):
        self.filepath = os.path.abspath(os.path.join(iodir, "Config.txt"))
        self.parameters = {} # dictionary of parameter name: value as strings.

        try:
            with open(self.filepath, 'r') as conf:
                self.parameters = {line.split('=')[0].strip(): line.split('=')[1].split('#')[0].strip() for line in conf.readlines() if not (line.startswith('#') or line.strip() == '')}
            
            for key in self.parameters.keys():
                # Converting config values from string to int
                self.parameters[key] = int(self.parameters[key])
            
            print("Config - Parameters loaded from file:", self.filepath)
            # print("Config parameters:", self.parameters)
        except:
            print("Config - ERROR: Couldn't open file in path:", self.filepath)
            raise
    
    def printConfig(self):
        print("VMIPS Configuration :")
        for key in self.parameters.keys():
            if len(key) < 15:
                print(key, "\t\t:" , self.parameters[key])
            else:
                print(key, "\t:" , self.parameters[key])
        print("")

class IMEM(object):
    def __init__(self, iodir):
        self.size = pow(2, 16) # Can hold a maximum of 2^16 instructions.
        self.filepath = os.path.abspath(os.path.join(iodir, "Resolved_Code.txt"))
        self.instructions = []

        try:
            with open(self.filepath, 'r') as insf:
                self.instructions = [ins.split('#')[0].strip() for ins in insf.readlines() if not (ins.startswith('#') or ins.strip() == '')]
            print("IMEM - Instructions loaded from file:", self.filepath)
            # print("IMEM - Instructions:", self.instructions)
        except:
            print("IMEM - ERROR: Couldn't open file in path:", self.filepath)
            raise

    def Read(self, idx): # Use this to read from IMEM.
        if idx < self.size:
            return self.instructions[idx]
        else:
            print("IMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)

class DMEM(object):
    # Word addressible - each address contains 32 bits.
    def __init__(self, name, iodir, addressLen):
        self.name = name
        self.size = pow(2, addressLen)
        self.min_value  = -pow(2, 31)
        self.max_value  = pow(2, 31) - 1
        self.ipfilepath = os.path.abspath(os.path.join(iodir, name + ".txt"))
        self.opfilepath = os.path.abspath(os.path.join(iodir, name + "OP.txt"))
        self.data = []

        try:
            with open(self.ipfilepath, 'r') as ipf:
                self.data = [int(line.strip()) for line in ipf.readlines()]
            print(self.name, "- Data loaded from file:", self.ipfilepath)
            # print(self.name, "- Data:", self.data)
            self.data.extend([0x0 for i in range(self.size - len(self.data))])
        except:
            print(self.name, "- ERROR: Couldn't open input file in path:", self.ipfilepath)
            raise

    def Read(self, idx: int): # Use this to read from DMEM.
        if idx < self.size:
            return self.data[idx]
        else:
            print("DMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)
            return None

    def Write(self, idx: int, val: int): # Use this to write into DMEM.
        if idx < self.size:
            self.data[idx] = val
            return self.data[idx]
        else:
            print("DMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)
            return None

    def dump(self):
        try:
            with open(self.opfilepath, 'w') as opf:
                lines = [str(data) + '\n' for data in self.data]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", self.opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", self.opfilepath)
            raise

class RegisterFile(object):
    def __init__(self, name, count, length = 1, size = 32):
        self.name       = name
        self.reg_count  = count
        self.vec_length = length # Number of 32 bit words in a register.
        self.reg_bits   = size
        self.min_value  = -pow(2, self.reg_bits-1)
        self.max_value  = pow(2, self.reg_bits-1) - 1
        self.registers  = [[0x0 for e in range(self.vec_length)] for r in range(self.reg_count)] # list of lists of integers

    def Read(self, idx: int):
        if idx < self.reg_count:
            return self.registers[idx]
        else:
            print(self.name, "- ERROR: Invalid register access at index: ", idx, " with register count: ", self.reg_count)
            return None

    def Write(self, idx: int, val: list):
        if idx < self.reg_count:
            if len(val) == self.vec_length:
                for i in range(len(val)):
                    if val[i] > self.max_value:
                        print(self.name, "- WARNING: Register write overflow at index: ", idx, " with vector index: ", i)
                        # Handling Overflow Exception by setting the value as the maximum value
                        val[i] = self.max_value
                    elif val[i] < self.min_value:
                        print(self.name, "- WARNING: Register write overflow at index: ", idx, " with vector index: ", i)
                        # Handling Overflow Exception by setting the value as the minimum value
                        val[i] = self.min_value
                    else:
                        pass
                self.registers[idx] = val
                return self.registers[idx]
            else:
                print(self.name, "- ERROR: Invalid register write at index: ", idx, " with vector length: ", len(val))
                return None
        else:
            print(self.name, "- ERROR: Invalid register write at index: ", idx, " with register count: ", self.reg_count)
            return None

    def dump(self, iodir):
        opfilepath = os.path.abspath(os.path.join(iodir, self.name + ".txt"))
        try:
            with open(opfilepath, 'w') as opf:
                row_format = "{:<13}"*self.vec_length
                lines = [row_format.format(*[str(i) for i in range(self.vec_length)]) + "\n", '-'*(self.vec_length*13) + "\n"]
                lines += [row_format.format(*[str(val) for val in data]) + "\n" for data in self.registers]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", opfilepath)
            raise

class Queue():
    def __init__(self, max_length: int):
        self.queue = []
        self.max_length = max_length
    
    def add(self, item):
        if (len(self.queue) < self.max_length):
            self.queue.append(item)
            return True
        else:
            print("ERROR - Queue already full!")
            return False
        
    def pop(self):
        if (len(self.queue) > 0):
            item = self.queue[0]
            self.queue = self.queue[1:]
            return item
        else:
            print("ERROR - Queue is empty!")
            return None
        
    def __str__(self):
        return_string = '[' + ", ".join(self.queue) + ']'
        return return_string
    
    def __len__(self):
        return len(self.queue)
    
class BusyBoard():
    def __init__(self, length: int):
        self.length = length
        self.register_statuses = [0 for _ in range(self.length)]

    def setBusy(self, idx: int):
        if idx < self.length:
            self.register_statuses[idx] = 1
        else:
            print("ERROR - Invalid index access in the busy board!")
    
    def clearStatus(self, idx: int):
        if idx < self.length:
            self.register_statuses[idx] = 0
        else:
            print("ERROR - Invalid index access in the busy board!")

    def getStatus(self, idx: int):
        if idx < self.length:
            return self.register_statuses[idx]
        else:
            print("ERROR - Invalid index access in the busy board!")
            return None

class Core():
    def __init__(self, imem: IMEM, sdmem: DMEM, vdmem: DMEM, config: Config):
        # cycle counter
        self.cycle = 0

        self.RFs = {"SRF": RegisterFile("SRF", 8),
                    "VRF": RegisterFile("VRF", 8, 64)}
        
        # Vector Length Register
        self.VLR = RegisterFile("VL", 1)
        self.VLR.Write(0, [self.RFs["VRF"].vec_length])
        
        # Initializing Vector Data Queue, Vector Compute Queue, Scalar Compute Queue
        self.VDQ = Queue(config.parameters["dataQueueDepth"])
        self.VCQ = Queue(config.parameters["computeQueueDepth"])
        self.SCQ = Queue(config.parameters["computeQueueDepth"])

        self.SRFBB = BusyBoard(self.RFs["SRF"].reg_count)
        self.VRFBB = BusyBoard(self.RFs["VRF"].reg_count)
        
    def run(self):
        # Printing current VMIPS configuration
        print("")
        config.printConfig()

        # Line Number to iterate through the code file
        line_number = 0

        while(True):
            # --- FETCH Stage ---
            current_instruction = imem.Read(line_number)
            current_instruction = current_instruction.split(" ")

            line_number += 1
            self.cycle += 1

            print("Current Instruction :", current_instruction)
            print("")

            # --- DECODE Stage ---
            instruction_word = str(current_instruction[0])
            self.cycle += 1

            if instruction_word == "HALT":
                # --- EXECUTE : HALT --- 
                break
            elif instruction_word.startswith("LV") or instruction_word.startswith("SV"):
                if len(self.VDQ) == self.VDQ.max_length:
                    print("ERROR - VDQ IS FULL! Cannot fetch any more vector load/store instructions!")
                    # reducing line number to re-fetch instruction, and check again if the queue is empty
                    line_number -= 1
                else:
                    self.VDQ.add(current_instruction)
            elif instruction_word.startswith("ADDV") or instruction_word.startswith("SUBV") or instruction_word.startswith("MULV") or instruction_word.startswith("DIVV"):
                if len(self.VCQ) == self.VCQ.max_length:
                    print("ERROR - VCQ IS FULL! Cannot fetch any more vector compute instructions!")
                    # reducing line number to re-fetch instruction, and check again if the queue is empty
                    line_number -= 1
                else:
                    self.VCQ.add(current_instruction)
            elif "PACK" in instruction_word:
                if len(self.VCQ) == self.VCQ.max_length:
                    print("ERROR - VCQ IS FULL! Cannot fetch any more vector compute instructions!")
                    # reducing line number to re-fetch instruction, and check again if the queue is empty
                    line_number -= 1
                else:
                    self.VCQ.add(current_instruction)
            else:
                if len(self.SCQ) == self.SCQ.max_length:
                    print("ERROR - SCQ IS FULL! Cannot fetch any more vector compute instructions!")
                    # reducing line number to re-fetch instruction, and check again if the queue is empty
                    line_number -= 1
                else:
                    self.SCQ.add(current_instruction)

        
        print("------------------------------")
        print(" Total Cycles: ", self.cycle)
        print("------------------------------")

    def dumpregs(self, iodir):
        for rf in self.RFs.values():
            rf.dump(iodir)

if __name__ == "__main__":
    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='Vector Core Functional Simulator')
    parser.add_argument('--iodir', default="", type=str, help='Path to the folder containing the input files - instructions and data.')
    args = parser.parse_args()

    iodir = os.path.abspath(args.iodir)
    print("IO Directory:", iodir)

    # Parse Config
    config = Config(iodir)

    # Parse IMEM
    imem = IMEM(iodir)  
    # Parse SMEM
    sdmem = DMEM("SDMEM", iodir, 13) # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
    # Parse VMEM
    vdmem = DMEM("VDMEM", iodir, 17) # 512 KB is 2^19 bytes = 2^17 K 32-bit words. 

    # Create Vector Core
    vcore = Core(imem, sdmem, vdmem, config)

    # Run Core
    vcore.run()   
    # vcore.dumpregs(iodir)

    # sdmem.dump()
    # vdmem.dump()

    # THE END