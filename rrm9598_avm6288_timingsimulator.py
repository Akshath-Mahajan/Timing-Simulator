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
    def unpop(self, instr):
        self.queue = [instr] + self.queue
        return None
    
    def getNextInQueue(self):
        if len(self.queue) > 0:
            item = self.queue[0]
            return item
        else:
            print("WARNING - Queue is empty!")
            return None
        
    def __str__(self):
        return str(self.queue)
    
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
    def __init__(self, name):
        super().__init__(1)
        self.cycles = 0
        self.instr = None
        self.name = name
    def addInstr(self, instr):
        self.instr = instr
        self.cycles = instr["cycles"]
        self.setBusy()

    
    def decrement(self):
        self.cycles -= 1
        if self.cycles == 0:
            self.clearStatus()
            return True
        return False
    
    def __str__(self):
        return self.name
    
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
        self.VectorLS = FU("VectorLS")
        self.VectorADD = FU("VectorADD")
        self.VectorMUL = FU("VectorMUL")
        self.VectorDIV = FU("VectorDIV")
        self.VectorSHUF = FU("VectorSHUF")
        self.ScalarU = FU("ScalarU")

        self.IF_HALT = False
        self.ID_HALT = False
        self.EX_HALT = False

    
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
        return n_cycles + max(banks) -1
    
    
    def execute(self):
        # instr has FU
        FUs = [self.VectorLS, self.VectorADD, self.VectorDIV, self.VectorMUL, self.VectorSHUF, self.ScalarU]

        for fu in FUs:
            if fu.getStatus() == "busy":
                # print("FU {} is busy {}".format(fu, fu.cycles))
                clear_operands = fu.decrement()

                if clear_operands:
                    operands = fu.instr["operand_with_type"]
                    fu.instr = None
                    for (idx, _type) in operands:
                        if _type == "scalar":
                            self.SRFBB.clearStatus(idx)
                        if _type == "vector":
                            self.VRFBB.clearStatus(idx)
        # Halting
    
    def decode(self, current_instruction: list, instr_idx: int):
        '''
        Returns an Instruction Dictionary = {
            instructionWord: ,
            functionalUnit: VectorLS/VectorADD/VectorMUL/VectorDIV/VectorSHUF/ScalarU,
            cycles: (int),
            operand_with_type: list([idx, scalar])
                               index = 0 -> Destination Register
        }
        '''

        instruction_dict = dict()
        instruction_word = str(current_instruction[0])
        instruction_dict['instructionWord'] = instruction_word
        instruction_dict['instr_idx'] = instr_idx
                
        if instruction_word == 'HALT':
            instruction_dict['functionalUnit'] = 'ScalarU'
            instruction_dict['cycles'] = 1
            instruction_dict['operand_with_type'] = []
        elif instruction_word == 'ADDVV' or instruction_word == 'SUBVV' or (instruction_word.startswith('S') and instruction_word.endswith('VV')):
            operands = self.get_operands(current_instruction)
            instruction_dict['functionalUnit'] = 'VectorADD'
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthAdd'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'vector']]
        elif instruction_word == 'ADDVS' or instruction_word == 'SUBVS' or (instruction_word.startswith('S') and instruction_word.endswith('VS')):
            operands = self.get_operands(current_instruction)
            instruction_dict['functionalUnit'] = 'VectorADD'
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthAdd'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'scalar']]
        elif instruction_word == 'MULVV':
            operands = self.get_operands(current_instruction)
            instruction_dict['functionalUnit'] = 'VectorMUL'
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthMul'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'vector']]
        elif instruction_word == 'MULVS':
            operands = self.get_operands(current_instruction)
            instruction_dict['functionalUnit'] = 'VectorMUL'
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthMul'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'scalar']]
        elif instruction_word == 'DIVVV':
            operands = self.get_operands(current_instruction)
            instruction_dict['functionalUnit'] = 'VectorDIV'
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthDiv'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'vector']]
        elif instruction_word == 'DIVVS':
            operands = self.get_operands(current_instruction)
            instruction_dict['functionalUnit'] = 'VectorDIV'
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthDiv'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'scalar']]
        elif "PACK" in instruction_word:
            operands = self.get_operands(current_instruction)
            instruction_dict['functionalUnit'] = 'VectorSHUF'
            instruction_dict['cycles'] = self.config.parameters['pipelineDepthShuffle'] + (self.VLR.Read(0)[0] // self.config.parameters['numLanes']) - 1
            instruction_dict['operand_with_type'] = [[operands[0], 'vector'], [operands[1], 'vector'], [operands[2], 'vector']]
        elif instruction_word.startswith('LV') or instruction_word.startswith('SV'):
            operands = self.get_operands(current_instruction)
            instruction_dict['functionalUnit'] = 'VectorLS'
            instruction_dict['cycles'] = self.calculate_bank_cycles(operands[1])
            instruction_dict['operand_with_type'] = [[operands[0], 'vector']]
        else:
            instruction_dict['functionalUnit'] = 'ScalarU'
            instruction_dict['cycles'] = 1
            operands = self.get_operands(current_instruction)
            if instruction_word == 'MTCL':
                instruction_dict['operand_with_type'] = [[operands[0], 'scalar']]
                VLR_val = [eval(operands[1])]
                self.VLR.Write(0, VLR_val)
            else:
                if not operands:
                    operands = []
                instruction_dict['operand_with_type'] = [[_, 'scalar'] for _ in operands]
        return instruction_dict
    

    def dispatch_to_queue(self, instr: dict):
        # Checking Vector Data Queue
        Qs = [self.VDQ, self.VCQ, self.SCQ]
        FUs = [{"VectorLS", }, {"VectorADD", "VectorMUL", "VectorDIV", "VectorSHUF",}, {"ScalarU"}]

        for q, fus in zip(Qs, FUs):
            if len(q) < q.max_length and instr['functionalUnit'] in fus:
                # print(instr)
                # if not self.operands_in_flight(instr):
                q.add(instr)
                return True
        return False
    
    def operands_in_flight(self, instr):
        qs = [self.VDQ, self.VCQ, self.SCQ]
        fus = [
            self.VectorLS,
            self.VectorADD,
            self.VectorMUL, 
            self.VectorDIV, 
            self.VectorSHUF,
            self.ScalarU
        ]
        operands = instr["operand_with_type"]
        instr_idx = instr["instr_idx"]
        # print(operands)
        if len(operands) == 0:
            return False
        for fu in fus:
            if fu.getStatus() == "busy":
                busy_destination = fu.instr["operand_with_type"][0] # (op, type)
                # print("destination", busy_destination, fu.instr)
                busy_instr_idx = fu.instr["instr_idx"]
                for opr in operands:
                    if opr[0] == busy_destination[0] and opr[1] == busy_destination[1] and busy_instr_idx < instr_idx:
                        return True
                
        for q in qs:
            for q_instr in q.queue:
                busy_destination = q_instr["operand_with_type"][0] # (op, type)
                busy_instr_idx = q_instr["instr_idx"]

                for opr in operands:
                    if opr[0] == busy_destination[0] and opr[1] == busy_destination[1] and busy_instr_idx < instr_idx:
                        return True
        # print("NO FLIGHT")
        return False
        


    def pop_from_queues(self):
        Qs = [self.VDQ, self.VCQ, self.SCQ]
        _mapping = {
            "VectorLS": self.VectorLS,
            "VectorADD": self.VectorADD,
            "VectorMUL": self.VectorMUL,
            "VectorDIV": self.VectorDIV,
            "VectorSHUF": self.VectorSHUF,
            "ScalarU": self.ScalarU
        }
        for q in Qs:
            if len(q) > 0:
                instr = q.pop()
                fu = _mapping[instr["functionalUnit"]]
                
                if fu.getStatus() == "free" and not self.operands_in_flight(instr):
                    fu.addInstr(instr)

                    operands = instr["operand_with_type"]
                    for (operand, _type) in operands:
                        if _type == "scalar":
                            bb = self.SRFBB
                        else:
                            bb = self.VRFBB
                        bb.setBusy(operand)
                else:
                    q.unpop(instr)
                    # print("Stalling the instruction - {} is busy".format(instr["functionalUnit"]))    # fu.setBusy()
            # else:
            #     print("No instructions in Queue:", q)

    def fetch(self, idx):
        if idx < len(self.imem.instructions):
            instr = self.imem.Read(idx)
            return instr.split(" ")
    
    def q_filled(self):
        Qs = [self.VCQ, self.VDQ, self.SCQ]
        for q in Qs:
            if len(q):
                return True
        return False
    
    def fu_filled(self):
        FUs = [
            self.VectorLS,
            self.VectorADD,
            self.VectorMUL,
            self.VectorDIV,
            self.VectorSHUF,
            self.ScalarU
        ]
        for fu in FUs:
            if fu.getStatus() == "busy":
                return True
        return False

    def printStatus(self):
        print("=== Queues ===")
        print("VDQ:", self.VDQ)
        print("VCQ:", self.VCQ)
        print("SCQ:", self.SCQ)
        
        print("=== FUs ===")
        FUs = [
            self.VectorLS,
            self.VectorADD,
            self.VectorMUL,
            self.VectorDIV,
            self.VectorSHUF,
            self.ScalarU
        ]
        for fu in FUs:
            print("{}: Instr {} Cycles {} Status {}".format(fu, fu.instr, fu.cycles, fu.getStatus()))
    def run(self):
        # Printing current VMIPS configuration
        print("")
        self.config.printConfig()

        # Index to iterate through the code file
        instr_idx = 0
        instr = None
        # Decode Stage List - list which holds all inflight instructions that are yet to be decoded and pushed to the queue
        # decode_stage = []
        dispatch_success = True
        while(not self.EX_HALT):
            self.cycle += 1
            self.execute()
            
            # Halting:
            anything_in_flight = self.fu_filled() or self.q_filled()
            self.EX_HALT = self.ID_HALT and not anything_in_flight



            if not self.ID_HALT and instr:
                decoded_instr = self.decode(instr, instr_idx)
                if instr[0] == "HALT":
                    self.ID_HALT = True
                    continue # Don't dispatch halt to queue?
                dispatch_success = self.dispatch_to_queue(decoded_instr)
            # If HALT has been reached, then all previous instrs have been successfully decoded and dispatched


            # Pop regardless of decode/dispatch
            self.pop_from_queues()
            
            if not self.IF_HALT:
                instr = self.fetch(instr_idx)
                if instr[0] == "HALT":
                    self.IF_HALT = True
                if dispatch_success:
                    instr_idx += 1

            print("Cycle:", self.cycle)
            # print(self.printStatus())

            # if self.cycle > 100:
            #     break
            # self.IF_NOP = instr[0] == "HALT"

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