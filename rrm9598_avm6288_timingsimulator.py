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
        if len(self.queue) < self.max_length:
            self.queue.append(item)
            return True
        else:
            print("ERROR - Queue already full!")
            return False
        
    def pop(self):
        if len(self.queue) > 0:
            item = self.queue[0]
            self.queue = self.queue[1:]
            return item
        else:
            print("ERROR - Queue is empty!")
            return None
    
    def getNextInQueue(self):
        if len(self.queue) > 0:
            item = self.queue[0]
            return item
        else:
            print("WARNING - Queue is empty!")
            return None
        
    def __str__(self):
        return_string = '[' + ", ".join(self.queue) + ']'
        return return_string
    
    def __len__(self):
        return len(self.queue)
    
class BusyBoard():
    def __init__(self, length: int):
        self.length = length
        self.register_statuses = ['free' for _ in range(self.length)]

    def setBusy(self, idx = 0):
        if idx < self.length:
            self.register_statuses[idx] = 'busy'
        else:
            print("ERROR - Invalid index access in the busy board!")
    
    def clearStatus(self, idx = 0):
        if idx < self.length:
            self.register_statuses[idx] = 'free'
        else:
            print("ERROR - Invalid index access in the busy board!")

    def getStatus(self, idx = 0):
        if idx < self.length:
            return self.register_statuses[idx]
        else:
            print("ERROR - Invalid index access in the busy board!")
            return None

# TODO - Check if you can create classes for Frontend and Backend

class Core():
    def __init__(self, imem: IMEM, sdmem: DMEM, vdmem: DMEM, config: Config):
        self.imem = imem
        self.sdmem = sdmem
        self.vdmem = vdmem
        self.config = config
        
        # cycle counter
        self.cycle = 0

        self.RFs = {"SRF": RegisterFile("SRF", 8),
                    "VRF": RegisterFile("VRF", 8, 64)}
        
        # Vector Length Register
        self.VLR = RegisterFile("VL", 1)
        self.VLR.Write(0, [self.RFs["VRF"].vec_length])
        
        # Initializing Vector Data Queue, Vector Compute Queue, Scalar Compute Queue
        self.VDQ = Queue(self.config.parameters["dataQueueDepth"])
        self.VCQ = Queue(self.config.parameters["computeQueueDepth"])
        self.SCQ = Queue(self.config.parameters["computeQueueDepth"])

        # Vector Register File Busy Boards
        self.SRFBB = BusyBoard(self.RFs["SRF"].reg_count)
        self.VRFBB = BusyBoard(self.RFs["VRF"].reg_count)
        
        # Functional Unit Busy Boards
        self.VectorLS = BusyBoard(1)
        self.VectorADD = BusyBoard(1)
        self.VectorMUL = BusyBoard(1)
        self.VectorDIV = BusyBoard(1)
        self.VectorSHUF = BusyBoard(1)
        self.ScalarU = BusyBoard(1)
    
    def run(self):
        # Printing current VMIPS configuration
        print("")
        self.config.printConfig()

        # Line Number to iterate through the code file
        line_number = 0

        while(True):
            # --- Executing Active Instructions ---
            # TODO - WRITE THIS CODE!

            # --- Pop Instructions ---
            # Checking Vector Data Queue
            if len(self.VDQ) != 0:
                # Get the next instruction from VDQ
                next_instruction = self.VDQ.getNextInQueue()
                # Checking if the Vector Load/Store functional unit is available
                if self.VectorLS.getStatus() == 'free':
                    # Now check if the operands are available
                    operand = next_instruction['operands'][0]
                    if self.VRFBB.getStatus(operand) == 'free':
                        print("Pushing to execution:", next_instruction)
                        self.VDQ.pop()
                        self.VectorLS.setBusy()
                        self.VRFBB.setBusy(operand)
                    else:
                        print("Stalling the instruction, as operand is busy!")
                else:
                    print("Stalling the instruction, as Vector Load/Store Unit is busy!")
            else:
                print("No instructions in Vector Data Queue!")
            
            # Checking Vector Compute Queue
            if len(self.VCQ) != 0:
                # Get the next instruction from VCQ
                next_instruction = self.VCQ.getNextInQueue()
                # Get the instruction unit
                if next_instruction['functionalUnit'] == 'VectorADD':
                    # Checking if the Vector ADD/SUB functional unit is available
                    if self.VectorADD.getStatus() == 'free':
                        # Now getting the operands of the instruction
                        operand1 = next_instruction['operands'][0]
                        operand2 = next_instruction['operands'][1]
                        destination = next_instruction['destination']
                        # Checking if it is a Vector and Scalar operation
                        if 'VS' in next_instruction['instructionWord']:
                            # Checking if all the operands are available 
                            if self.VRFBB.getStatus(operand1) == 'free' and self.SRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                                print("Pushing to execution:", next_instruction)
                                self.VCQ.pop()
                                self.VectorADD.setBusy()
                                self.VRFBB.setBusy(operand1)
                                self.SRFBB.setBusy(operand2)
                                self.VRFBB.setBusy(destination)
                            else:
                                print("Stalling the instruction, as operands are busy!")
                        else:
                            # Checking if all the operands are available 
                            if self.VRFBB.getStatus(operand1) == 'free' and self.VRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                                print("Pushing to execution:", next_instruction)
                                self.VCQ.pop()
                                self.VectorADD.setBusy()
                                self.VRFBB.setBusy(operand1)
                                self.VRFBB.setBusy(operand2)
                                self.VRFBB.setBusy(destination)
                            else:
                                print("Stalling the instruction, as operands are busy!")
                    else:
                        print("Stalling the instruction, as Vector ADD/SUB Unit is busy!")
                elif next_instruction['functionalUnit'] == 'VectorMUL':
                    # Checking if the Vector MUL functional unit is available
                    if self.VectorMUL.getStatus() == 'free':
                        # Now getting the operands of the instruction
                        operand1 = next_instruction['operands'][0]
                        operand2 = next_instruction['operands'][1]
                        destination = next_instruction['destination']
                        # Checking if it is a Vector and Scalar operation
                        if 'VS' in next_instruction['instructionWord']:
                            # Checking if all the operands are available 
                            if self.VRFBB.getStatus(operand1) == 'free' and self.SRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                                print("Pushing to execution:", next_instruction)
                                self.VCQ.pop()
                                self.VectorMUL.setBusy()
                                self.VRFBB.setBusy(operand1)
                                self.SRFBB.setBusy(operand2)
                                self.VRFBB.setBusy(destination)
                            else:
                                print("Stalling the instruction, as operands are busy!")
                        else:
                            # Checking if all the operands are available 
                            if self.VRFBB.getStatus(operand1) == 'free' and self.VRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                                print("Pushing to execution:", next_instruction)
                                self.VCQ.pop()
                                self.VectorMUL.setBusy()
                                self.VRFBB.setBusy(operand1)
                                self.VRFBB.setBusy(operand2)
                                self.VRFBB.setBusy(destination)
                            else:
                                print("Stalling the instruction, as operands are busy!")
                    else:
                        print("Stalling the instruction, as Vector MUL Unit is busy!")
                elif next_instruction['functionalUnit'] == 'VectorDIV':
                    # Checking if the Vector DIV functional unit is available
                    if self.VectorDIV.getStatus() == 'free':
                        # Now getting the operands of the instruction
                        operand1 = next_instruction['operands'][0]
                        operand2 = next_instruction['operands'][1]
                        destination = next_instruction['destination']
                        # Checking if it is a Vector and Scalar operation
                        if 'VS' in next_instruction['instructionWord']:
                            # Checking if all the operands are available 
                            if self.VRFBB.getStatus(operand1) == 'free' and self.SRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                                print("Pushing to execution:", next_instruction)
                                self.VCQ.pop()
                                self.VectorDIV.setBusy()
                                self.VRFBB.setBusy(operand1)
                                self.SRFBB.setBusy(operand2)
                                self.VRFBB.setBusy(destination)
                            else:
                                print("Stalling the instruction, as operands are busy!")
                        else:
                            # Checking if all the operands are available 
                            if self.VRFBB.getStatus(operand1) == 'free' and self.VRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                                print("Pushing to execution:", next_instruction)
                                self.VCQ.pop()
                                self.VectorDIV.setBusy()
                                self.VRFBB.setBusy(operand1)
                                self.VRFBB.setBusy(operand2)
                                self.VRFBB.setBusy(destination)
                            else:
                                print("Stalling the instruction, as operands are busy!")
                    else:
                        print("Stalling the instruction, as Vector DIV Unit is busy!")
                elif next_instruction['functionalUnit'] == 'VectorSHUF':
                    # Checking if the Vector Shuffle functional unit is available
                    if self.VectorSHUF.getStatus() == 'free':
                        # Now getting the operands of the instruction
                        operand1 = next_instruction['operands'][0]
                        operand2 = next_instruction['operands'][1]
                        destination = next_instruction['destination']
                        # Checking if all the operands are available 
                        if self.VRFBB.getStatus(operand1) == 'free' and self.VRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                            print("Pushing to execution:", next_instruction)
                            self.VCQ.pop()
                            self.VectorSHUF.setBusy()
                            self.VRFBB.setBusy(operand1)
                            self.VRFBB.setBusy(operand2)
                            self.VRFBB.setBusy(destination)
                        else:
                            print("Stalling the instruction, as operands are busy!")
                    else:
                        print("Stalling the instruction, as Vector Shuffle Unit is busy!")
                else:
                    print("ERROR - Invalid Functional Unit! Check code!")
            else:
                print("No instructions in Vector Compute Queue!")
            
            if len(self.SCQ) != 0:
                # Get the next instruction from SCQ
                next_instruction = self.SCQ.getNextInQueue()
                # Checking if the Scalar functional unit is available
                if self.ScalarU.getStatus() == 'free':
                    # Now getting the operands of the instruction
                    # TODO - CHECK FOR VARIABLE OPERAND LENGTHS HERE!
                    operand1 = next_instruction['operands'][0]
                    operand2 = next_instruction['operands'][1]
                    destination = next_instruction['destination']
                    # Checking if all the operands are available 
                    if self.SRFBB.getStatus(operand1) == 'free' and self.SRFBB.getStatus(operand2) == 'free' and self.SRFBB.getStatus(destination) == 'free':
                        print("Pushing to execution:", next_instruction)
                        self.SCQ.pop()
                        self.ScalarU.setBusy()
                        self.SRFBB.setBusy(operand1)
                        self.SRFBB.setBusy(operand2)
                        self.SRFBB.setBusy(destination)
                    else:
                        print("Stalling the instruction, as operands are busy!")
                else:
                    print("Stalling the instruction, as Scalar Unit is busy!")
            else:
                print("No instructions in Scalar Compute Queue!")

            # --- Dispatch to Queue ---
            # TODO - WRITE THIS CODE!

            # --- Decoding Instructions ---
            # TODO - CHANGE ALL THIS CODE!
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

            # --- Fetching Instructions ---
            # TODO - CHANGE ALL THIS CODE!
            current_instruction = self.imem.Read(line_number)
            current_instruction = current_instruction.split(" ")

            line_number += 1
            self.cycle += 1

            print("Current Instruction :", current_instruction)
            print("")
        
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