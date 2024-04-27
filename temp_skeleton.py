import os
import argparse

class Config(object):
    def __init__(self, iodir):
        self.filepath = os.path.abspath(os.path.join(iodir, "Config.txt"))
        self.parameters = {} # dictionary of parameter name: value as strings.

        try:
            with open(self.filepath, 'r') as conf:
                self.parameters = {line.split('=')[0].strip(): line.split('=')[1].split('#')[0].strip() for line in conf.readlines() if not (line.startswith('#') or line.strip() == '')}
            print("Config - Parameters loaded from file:", self.filepath)
            print("Config parameters:", self.parameters)
        except:
            print("Config - ERROR: Couldn't open file in path:", self.filepath)
            raise

class IMEM(object):
    def __init__(self, iodir):
        self.size = pow(2, 16) # Can hold a maximum of 2^16 instructions.
        self.filepath = os.path.abspath(os.path.join(iodir, "Code.asm"))
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

    def Read(self, idx): # Use this to read from DMEM.
        if idx < self.size:
            return self.data[idx]
        else:
            print("DMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)
            return None
    def Write(self, idx, val): # Use this to write into DMEM.
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

    def Read(self, idx):
        if idx < self.reg_count:
            return self.registers[idx]
        else:
            print(self.name, "- ERROR: Invalid register access at index: ", idx, " with register count: ", self.reg_count)
            return None

    def Write(self, idx, val):
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

class Core():
    def __init__(self, imem, sdmem, vdmem, config:Config):
        self.IMEM = imem
        self.SDMEM = sdmem
        self.VDMEM = vdmem
        self.config = config

        self.RFs = {"SRF": RegisterFile("SRF", 8),
                    "VRF": RegisterFile("VRF", 8, 64)}
        
        # Your code here.
        ### Special Purpose Registers
        self.SRs = {"VM": RegisterFile("VM", 1, 1, 66), # extra bits to avoid overflow error, explained further in document
                     "VL": RegisterFile("VL", 1)}
        # Initialising Vector Length Register as the MVL
        self.SRs["VL"].Write(0, [self.RFs["VRF"].vec_length])


        # Pipeline depth = latency
        self.latency = {
            "mul": self.config.parameters["pipelineDepthMul"],
            "div":  self.config.parameters["pipelineDepthDiv"],
            "add": self.config.parameters["pipelineDepthAdd"],
            "shuffle": self.config.parameters["pipelineDepthShuffle"],
            
            # Banking
            "data": self.config.parameters["vlsPipelineDepth"],
            "bankbusy": self.config.parameters["vdmBankBusyTime"],
        }

        self.n_banks = self.config.parameters["vdmNumBanks"]
        self.n_lanes = self.config.parameters["numLanes"]

        # Dispatch Queues (will be the busy boards)
        self.vector_data_queue = []
        self.vector_compute_queue = []
        self.scalar_queue = []
        # Here, element = # Cycles remaining

        # self.FETCH_NOP = False
        # self.DECODE_NOP = False
        # self.EXECUTE_NOP = False

        self.program = []

    def execute(self):
        queues = [self.vector_data_queue, self.vector_compute_queue, self.scalar_queue]

        for q in queues:
            if len(q) > 0:
                q[0] -= 1
                if q[0] == 0:
                    q.pop(0)

    def add_to_queue(self, n_cycles, q, max_depth):
        if len(q) < max_depth:
            q.append(n_cycles)
            return True
        return False

    def calculate_bank_cycles(self, addresses):
        # Takes in addersses, return n_cycles
        
        n_cycles = self.latency["data"]  # Initial pipeline depth
        banks = [0 for _ in range(self.n_banks)]
        n_banks = self.n_banks
        n_lanes = self.n_lanes
        # print("Banks:", n_banks, "Lanes:", n_lanes)

        n_lanes = 1 # Acc to tim
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
                banks[adr % n_banks] += self.latency["bankbusy"] # Add however many cycles are required in general to finish load/store
            # print(banks)
            # Reduce remaining cycles for each bank
            for i in range(n_banks):
                if banks[i] > 0:
                    banks[i] -= 1
            n_cycles += 1
            # print(banks)
        
        # If anything is left in bank busy, then add it to n_banks
        return n_cycles + max(banks)


    def dispatch(self, instr_state):
        # Instr state contains what was decoded about the instruction.
        if instr_state is None:
            return True
        
        if instr_state["is_scalar"]:
            # Add 1 cycle for any scalar instruction
            success = self.add_to_queue(1, self.scalar_queue, self.config.parameters["dataQueueDepth"])
            return success
        
        # Vector instructions
        if instr_state["is_data"]:
            # Data instructions
            addresses = instr_state["addresses"]
            # Calculate num cycles that will be required
            n_cycles = self.calculate_bank_cycles(addresses)
            success = self.add_to_queue(n_cycles, self.vector_data_queue, self.config.parameters["dataQueueDepth"])

            return success
                
        else:
            # Compute instructions
            pass


    def run(self):
        program = self.read_code_file()
        cycles = 0
        instr_idx = 0
        
        instr_state = None
        instr = program[instr_idx]
        while(True):
            
            # Execute Stage:
            # Decrement queues in parallel
            self.execute()
            
            # Dispatch to Queue
            # Place in proper queue with proper # cycles (as per calculations)
            success = self.dispatch(instr_state)    

            if success:         # If placed in queue
                # Decode next instr
                # print(instr)
                instr_state = self.decode(instr)
                
            
                # Fetch instr (1 cycle)
                if instr_state is not None:
                    instr_idx += 1  # If instr_state is None then stall fetch, so instr_idx is not updated                    
                instr = program[instr_idx]
        return cycles
            

    def decode(self, instr:str):
        result = {
            "is_scalar": None,
            "addresses": None,
        }
        scalar_instr = {"LS", "SS", "ADD", "SUB", "MUL", "DIV", "CVM", "POP", "MTCL", "MFCL",
                        "AND", "OR", "XOR", "SLL", "SRL", "SRA", "BEQ", "BNE", "BLT", "BLE", "BGT", "BGE"}
        # instr = instr.upper().split(" ")
        data_instr = {"LV", "SV", "LVWS", "SVWS", "LVI", "SVI"}
        result["is_scalar"] = (instr[0] in scalar_instr)

        result["is_data"] = (instr[0] in data_instr)
        if result["is_data"]:
            result["addresses"] = eval(instr[-1])
        # result[""]
        return result

    ################################# SUPPORT COMMENTS ####################################
    def read_code_file(self):
        line_counter = 0
        imem = self.IMEM
        program = list()
        while(line_counter < len(imem.instructions)):
            current_line = imem.Read(line_counter)
            if '#' in current_line:
                current_line = current_line[:current_line.index('#')]
            if current_line == "":
                line_counter = line_counter + 1
                continue
            current_line = current_line.strip().split(" ")
            line_counter = line_counter + 1
            program.append(current_line)
        return program

    def dumpregs(self, iodir):
        for rf in self.RFs.values():
            rf.dump(iodir)

def parse_config(config):
    for k in config.parameters.keys():
        config.parameters[k] = int(config.parameters[k])

if __name__ == "__main__":
    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='Vector Core Functional Simulator')
    parser.add_argument('--iodir', default="", type=str, help='Path to the folder containing the input files - instructions and data.')
    args = parser.parse_args()

    iodir = os.path.abspath(args.iodir)
    print("IO Directory:", iodir)

    # Parse Config
    config = Config(iodir)
    parse_config(config)
    # Parse IMEM
    imem = IMEM(iodir)  
    # Parse SMEM
    sdmem = DMEM("SDMEM", iodir, 13) # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
    # Parse VMEM
    vdmem = DMEM("VDMEM", iodir, 17) # 512 KB is 2^19 bytes = 2^17 K 32-bit words. 

    # Create Vector Core
    vcore = Core(imem, sdmem, vdmem, config)

    # addrs = [i for i in range(64)]
    # print()
    # print(vcore.calculate_bank_cycles(addrs))
    # print()
    # Run Core
    vcore.run()   
    vcore.dumpregs(iodir)

    sdmem.dump()
    vdmem.dump()
    # THE END