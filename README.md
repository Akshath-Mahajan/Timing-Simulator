# Vector Processor - Timing Simulator

## VMIPS ISA Specifications

- Vector Length - 64
- Vector Data Memory - 512KB, word addressable
- Scalar Data Memory  - 32KB, word addressable
- Scalar Register File - 8 registers, 32-bit elements
- Vector Register File - 8 registers, 64 32-bit elements
- Vector Lenth Register - 1 register, 32-bit
- Vector Mask Register - 1 register, 64 1-bit elements

## VMIPS Architecture

![Vector Processor Block Diagram](https://github.com/rugvedmhatre/Vector-Timing-Simulator/blob/main/images/Vector-Block-Diagram.svg?raw=true)

- 1 Scalar Functional Unit
- 1 Vector Load/Store Functional Unit
- 1 Vector Add/Subtract Functional Unit
- 1 Vector Multiply Functional Unit
- 1 Vector Divide Functional Unit
- 1 Vector Shuffle Functional Unit

### Base Configuration
- Dispatch Queue Configuration:
    - Vector Data Queue Depth - 4
    - Vector Compute Queue Depth - 4
    - Scalar Compute Queue Depth - 4
- Vector Data Memory Configuration:
    - Vector Data Memory Banks - 16
    - Vector Data Memory Bank Busy Time - 2
    - Vector Load/Store Pipeline Depth - 11
- Vector Compute Configuration:
    - Vector Lanes - 4
    - Vector Add/Sub Pipeline Depth - 2
    - Vector Multiply Pipeline Depth - 12
    - Vector Divide Pipeline Depth - 8
    - Vector Shuffle Pipeline Depth - 5

Furthermore, the VRFs have only 1 read and 1 write port. Hence, simulatneous reading of vector registers is not supported.

### Example 1

We show an example of the timings of a simple load vector program.

```
LV VR1 SR0
HALT
```

__Execution Flow:__

- In the $1^{st}$ cycle, `LV VR1 SR0` is fetched. 
- In the $2^{nd}$ cycle, `HALT` is fetched, and `LV VR1 SR0` is decoded, checked for strucutral hazards, and since there are no hazards, it is sent to the dispatch queue.
- In the $3^{rd}$ cycle, `HALT` is decoded, and is stalled, as it will wait for all the current instructions to be completed. `LV VR1 SR0` instruction is popped off the queue and starts executing. The pipeline depth for vector load instruction is 11 cycles.
- In the $13^{th}$ cycle, `LV VR1 SR0` instruction triggers the Vector Data Memory Bank for the $1^{st}$ element address. The bank busy time is 2 cycles, so 1 cycle completes in this cycle, and now in next cycle the $1^{st}$ element is populated in the `VR1` register.
- In the $14^{th}$ cycle, we have populated the $1^{st}$ element in the `VR1` register, and triggered the Vector Data Memory Bank for the $2^{nd}$ element address.
- In the $77^{th}$ cycle, we have populated the $64^{th}$ element in the `VR1` register, and it is cleared off the busy board. `HALT` instruction stall is removed, and is moved to the dispatch queue.
- In the $78^{th}$ cycle, the `HALT` instruction is executed and the program stops.

![Example 1 Timing Diagram](https://github.com/rugvedmhatre/Vector-Timing-Simulator/blob/main/images/Example1_Timing_Diagram.png?raw=true)