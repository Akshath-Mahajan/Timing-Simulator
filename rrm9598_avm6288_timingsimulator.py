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
        self.statuses = ['free' for _ in range(self.length)]

    def setBusy(self, idx = 0):
        if idx < self.length:
            self.statuses[idx] = 'busy'
        else:
            print("ERROR - Invalid index access in the busy board!")
    
    def clearStatus(self, idx = 0):
        if idx < self.length:
            self.statuses[idx] = 'free'
        else:
            print("ERROR - Invalid index access in the busy board!")

    def getStatus(self, idx = 0):
        if idx < self.length:
            return self.statuses[idx]
        else:
            print("ERROR - Invalid index access in the busy board!")
            return None

class FU(BusyBoard):
    def __init__(self):
        super().__init__(1)
        self.cycles = 0
        self.instr = None

    def addInstr(self, instr):
        self.instr = instr
        self.cycles = instr["clock"]
    
    def decrement(self):
        self.cycles -= 1
        if self.cycles == 0:
            self.clearStatus()
            return True
        return False
    
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

        # Register Files' Busy Boards
        self.SRFBB = BusyBoard(self.RFs["SRF"].reg_count)
        self.VRFBB = BusyBoard(self.RFs["VRF"].reg_count)
        
        # Functional Unit Busy Boards
        self.VectorLS = FU()
        self.VectorADD = FU()
        self.VectorMUL = FU()
        self.VectorDIV = FU()
        self.VectorSHUF = FU()
        self.ScalarU = FU()

    
    def get_operands(self, instruction: list):
        if len(instruction) == 4:
            destination = str(instruction[1])
            operand1 = str(instruction[2])
            operand2 = str(instruction[3])
            destination_reg_idx = int(destination[2:])
            operand1_reg_idx = int(operand1[2:])
            if operand2.isdigit() or operand2[0] == '-':
                imm = int(operand2)
                return [destination_reg_idx, operand1_reg_idx, imm]
            else:
                operand2_reg_idx = int(operand2[2:])
                return [destination_reg_idx, operand1_reg_idx, operand2_reg_idx]
        elif len(instruction) == 3:
            destination = str(instruction[1])
            operand1 = str(instruction[2])
            destination_reg_idx = int(destination[2:])
            if operand1.startswith('('):
                address = eval(operand1)
                return [destination_reg_idx, address]
            else:
                operand1_reg_idx = int(operand1[2:])
                return [destination_reg_idx, operand1_reg_idx]
        elif len(instruction) == 2:
            operand1 = str(instruction[1])
            if operand1.startswith('('):
                address = eval(operand1)
                return [address]
            else:
                operand1_reg_idx = int(operand1[2:])
                return [operand1_reg_idx]
        else:
            return None
    
    
    def calculate_bank_cycles(self, addresses):
        # Takes in addersses, return n_cycles
        
        n_cycles = self.config.parameters["vlsPipelineDepth"]  # Initial pipeline depth
        n_banks = self.config.parameters["vdmNumBanks"]
        n_lanes = 1

        banks = [0 for _ in range(n_banks)]
        # print("Banks:", n_banks, "Lanes:", n_lanes)
        addrs = []
        for i in range((len(addresses) // n_lanes) + 1):
            start_idx = i*n_lanes
            end_idx   = (i+1)*n_lanes

            addrs.append(
                addresses[start_idx:end_idx]
            )
        # print("Addrs:", addrs)
        # addrs = [[addresses to issue at cycle 1], [addresses to issue at cycle 2]]

        for adrs in addrs:
            # adrs = [0, 1, 2, 3]
            # print("Loading addresses:", adrs)
            for adr in adrs:
                if banks[adr % n_banks] != 0:   # Bank [adr % n_bank] is busy?
                    # print("Hit:", adr)
                    banks[adr % n_banks] += 1   # Add 1 cycle to resolve conflict
                banks[adr % n_banks] += self.config.parameters["vdmBankBusyTime"] # Add however many cycles are required in general to finish load/store
            # print(banks)
            # Reduce remaining cycles for each bank
            for i in range(n_banks):
                if banks[i] > 0:
                    banks[i] -= 1
            n_cycles += 1
            # print(banks)
        
        # If anything is left in bank busy, then add it to n_banks
        return n_cycles + max(banks)
    
    
    def execute(self):
        # instr has FU
        FUs = [self.VectorLS, self.VectorADD, self.VectorDIV, self.VectorMUL, self.VectorSHUF, self.ScalarU]

        for fu in FUs:
            if fu.getStatus() == "busy":
                clear_operands = fu.decrement()

                if clear_operands:
                    operands = fu.instr["operand_with_type"]
                    for (idx, _type) in operands:
                        if _type == "scalar":
                            self.SRFBB.clearStatus(idx)
                        if _type == "vector":
                            self.VRFBB.clearStatus(idx)

    
    def decode(self, current_instruction: list):
        '''
        Returns an Instruction Dictionary = {
            instructionWord: ,
            functionalUnit: VectorLS/VectorADD/VectorMUL/VectorDIV/VectorSHUF/ScalarU,
            operands: list(int),
            destination: (int),
            cycles: (int),
            operand_with_type: list([idx, scalar])
        }
        '''

        instruction_dict = dict()
        instruction_word = str(current_instruction[0])
                
        if instruction_word == 'HALT':
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'ScalarU'
            instruction_dict['operands'] = None
            instruction_dict['destination'] = None
            instruction_dict['cycles'] = 1
            instruction_dict['operand_with_type'] = []
        elif instruction_word == 'ADDVV' or instruction_word == 'SUBVV':
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorADD'
            instruction_dict['operands'] = [operands[1], operands[2]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthAdd'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'vector']]
        elif instruction_word == 'ADDVS' or instruction_word == 'SUBVS':
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorADD'
            instruction_dict['operands'] = [operands[1], operands[2]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthAdd'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'scalar']]
        elif instruction_word == 'MULVV':
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorMUL'
            instruction_dict['operands'] = [operands[1], operands[2]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthMul'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'vector']]
        elif instruction_word == 'MULVS':
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorMUL'
            instruction_dict['operands'] = [operands[1], operands[2]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthMul'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'scalar']]
        elif instruction_word == 'DIVVV':
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorDIV'
            instruction_dict['operands'] = [operands[1], operands[2]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthDiv'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'vector']]
        elif instruction_word == 'DIVVS':
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorDIV'
            instruction_dict['operands'] = [operands[1], operands[2]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthDiv'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'scalar']]
        elif instruction_word.startswith('S') and instruction_word.endswith('VV'):
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorADD'
            instruction_dict['operands'] = [operands[1], operands[2]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthAdd'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'vector']]
        elif instruction_word.startswith('S') and instruction_word.endswith('VS'):
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorADD'
            instruction_dict['operands'] = [operands[1], operands[2]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthAdd'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'scalar']]
        elif "PACK" in instruction_word:
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorSHUF'
            instruction_dict['operands'] = [operands[1], operands[2]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthShuffle'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'vector']]
        elif instruction_word.startswith('LV') or instruction_word.startswith('SV'):
            operands = self.get_operands(current_instruction)
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'VectorLS'
            instruction_dict['operands'] = [operands[1]]
            instruction_dict['destination'] = [operands[0]]
            instruction_dict['cycles'] = self.calculate_bank_cycles(operands[1])
            instruction_dict['operand_with_type'] = [[operands[0], 'vector']]
        else:
            instruction_dict['instructionWord'] = instruction_word
            instruction_dict['functionalUnit'] = 'ScalarU'
            instruction_dict['operands'] = [operands[1]]
            instruction_dict['destination'] = [operands[0]]
            # TODO - Add memory bank calculated cycles here...
            instruction_dict['cycles'] = 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector']]
        return instruction_dict
    

    def dispatch_to_queue(self, next_instruction: dict):
        # Checking Vector Data Queue
        if len(self.VDQ) < self.VDQ.max_length:
            # Get the next decoded instruction
            # Checking if the Vector Load/Store functional unit is available
            if self.VectorLS.getStatus() == 'free':
                # Now check if the operands are available
                operand = next_instruction['operands'][0]
                if self.VRFBB.getStatus(operand) == 'free':
                    print("Pushing to Vector Data dispatch queue!") 
                    self.VDQ.add(next_instruction)
                    self.VRFBB.setBusy(operand)
                else:
                    print("Stalling the instruction, as operand is busy!")
            else:
                print("Stalling the instruction, as Vector Load/Store Unit is busy!")
        else:
            print("Vector Data Queue is full!")
        
        # Checking Vector Compute Queue
        if len(self.VCQ) < self.VCQ.max_length:
            # Get the next instruction from VCQ
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
                            print("Pushing to Vector Compute dispatch queue!") 
                            self.VCQ.add(next_instruction)
                            self.VRFBB.setBusy(operand1)
                            self.SRFBB.setBusy(operand2)
                            self.VRFBB.setBusy(destination)
                        else:
                            print("Stalling the instruction, as operands are busy!")
                    else:
                        # Checking if all the operands are available 
                        if self.VRFBB.getStatus(operand1) == 'free' and self.VRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                            print("Pushing to Vector Compute dispatch queue!") 
                            self.VCQ.add(next_instruction)
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
                            print("Pushing to Vector Compute dispatch queue!") 
                            self.VCQ.add(next_instruction)
                            self.VRFBB.setBusy(operand1)
                            self.SRFBB.setBusy(operand2)
                            self.VRFBB.setBusy(destination)
                        else:
                            print("Stalling the instruction, as operands are busy!")
                    else:
                        # Checking if all the operands are available 
                        if self.VRFBB.getStatus(operand1) == 'free' and self.VRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                            print("Pushing to Vector Compute dispatch queue!")
                            self.VCQ.add(next_instruction)
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
                            print("Pushing to Vector Compute dispatch queue!")
                            self.VCQ.add(next_instruction)
                            self.VRFBB.setBusy(operand1)
                            self.SRFBB.setBusy(operand2)
                            self.VRFBB.setBusy(destination)
                        else:
                            print("Stalling the instruction, as operands are busy!")
                    else:
                        # Checking if all the operands are available 
                        if self.VRFBB.getStatus(operand1) == 'free' and self.VRFBB.getStatus(operand2) == 'free' and self.VRFBB.getStatus(destination) == 'free':
                            print("Pushing to Vector Compute dispatch queue!")
                            self.VCQ.add(next_instruction)
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
                        print("Pushing to Vector Compute dispatch queue!")
                        self.VCQ.add(next_instruction)
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
            print("Vector Compute Queue is full!")
        
        # Checking Scalar Compute Queue
        if len(self.SCQ) < self.SCQ.max_length:
            # Get the next instruction from SCQ
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
                    self.SCQ.add(next_instruction)
                    self.SRFBB.setBusy(operand1)
                    self.SRFBB.setBusy(operand2)
                    self.SRFBB.setBusy(destination)
                else:
                    print("Stalling the instruction, as operands are busy!")
            else:
                print("Stalling the instruction, as Scalar Unit is busy!")
        else:
            print("Scalar Compute Queue is full!")


    def run(self):
        # Printing current VMIPS configuration
        print("")
        self.config.printConfig()

        # Line Number to iterate through the code file
        line_number = 0
        
        # Current instruction is initialised as None
        current_instruction = None

        # Decoded Instructions List = list which holds all inflight instructions that are yet to be decoded and pushed to the queue
        # All stalled instructions  are present here...
        decoded_instructions = []

        while(True):

            # TODO - Add halting conditing here.
            

            # --- Executing Active Instructions ---
            # TODO - WRITE THIS CODE!
            if self.VectorLS.getStatus() == 'busy':
                print("Executing inflight Vector Load/Store instructions...")
            else:
                print("No inflight Vector Load/Store instructions!")
            
            if self.VectorADD.getStatus() == 'busy':
                print("Executing inflight Vector ADD/SUB instructions...")
            else:
                print("No inflight Vector ADD/SUB instructions!")

            if self.VectorMUL.getStatus() == 'busy':
                print("Executing inflight Vector MUL instructions...")
            else:
                print("No inflight Vector MUL instructions!")

            if self.VectorDIV.getStatus() == 'busy':
                print("Executing inflight Vector DIV instructions...")
            else:
                print("No inflight Vector DIV instructions!")

            if self.VectorSHUF.getStatus() == 'busy':
                print("Executing inflight Vector Shuffle instructions...")
            else:
                print("No inflight Vector Shuffle instructions!")

            if self.ScalarU.getStatus() == 'busy':
                print("Executing inflight Scalar instructions...")
            else:
                print("No inflight Scalar instructions!")


            
            # --- Pop Instructions ---
            # TODO - ADD CODE TO SEND TO BACKEND FOR EXECUTION
            # Checking Vector Data Queue
            if len(self.VDQ) != 0:
                # Get the next instruction from VDQ
                next_instruction = self.VDQ.getNextInQueue()
                if self.VectorLS.getStatus() == 'free':
                    self.VDQ.pop()
                    self.VectorLS.setBusy()
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
                        self.VCQ.pop()
                        self.VectorADD.setBusy()
                    else:
                        print("Stalling the instruction, as Vector ADD/SUB Unit is busy!")
                elif next_instruction['functionalUnit'] == 'VectorMUL':
                    # Checking if the Vector MUL functional unit is available
                    if self.VectorMUL.getStatus() == 'free':
                        self.VCQ.pop()
                        self.VectorMUL.setBusy()
                    else:
                        print("Stalling the instruction, as Vector MUL Unit is busy!")
                elif next_instruction['functionalUnit'] == 'VectorDIV':
                    # Checking if the Vector DIV functional unit is available
                    if self.VectorDIV.getStatus() == 'free':
                        self.VCQ.pop()
                        self.VectorDIV.setBusy()
                    else:
                        print("Stalling the instruction, as Vector DIV Unit is busy!")
                elif next_instruction['functionalUnit'] == 'VectorSHUF':
                    # Checking if the Vector Shuffle functional unit is available
                    if self.VectorSHUF.getStatus() == 'free':
                        self.VCQ.pop()
                        self.VectorSHUF.setBusy()
                    else:
                        print("Stalling the instruction, as Vector Shuffle Unit is busy!")
                else:
                    print("ERROR - Invalid Functional Unit! Check code!")
            else:
                print("No instructions in Vector Compute Queue!")
            
            # Checking Scalar Compute Queue
            if len(self.SCQ) != 0:
                # Get the next instruction from SCQ
                next_instruction = self.SCQ.getNextInQueue()
                # Checking if the Scalar functional unit is available
                if self.ScalarU.getStatus() == 'free':
                    self.SCQ.pop()
                    self.ScalarU.setBusy()
                else:
                    print("Stalling the instruction, as Scalar Unit is busy!")
            else:
                print("No instructions in Scalar Compute Queue!")


            # --- Decoding Instructions ---
            # TODO - CHANGE ALL THIS CODE!
            if current_instruction != None:
                instruction_dict = self.decode(current_instruction)
                decoded_instructions.append(instruction_dict)

            # --- Dispatch to Queue ---
            if len(decoded_instructions) != 0:
                for instruction in decoded_instructions:
                    self.dispatch_to_queue(instruction)

            # --- Fetching Instructions ---
            # TODO - VERIFY ALL THIS CODE!
            line = self.imem.Read(line_number)
            current_instruction = line.split(" ")
            
            print("Fetched Instruction :", current_instruction)
            print("")
            
            line_number += 1
            self.cycle += 1
        
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