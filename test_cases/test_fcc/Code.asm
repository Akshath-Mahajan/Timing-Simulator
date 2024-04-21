CVM                     # clear vector mask
MFCL SR2                # SR2 = VLR = 64
LS SR1 SR0 6            # SR1 = memory[SR0 + 6] = 256 <- This is the starting address of 'a' vector
LS SR3 SR0 0            # SR3 = memory[SR0 + 0] = 1
LS SR4 SR0 1            # SR4 = memory[SR0 + 1] = 512 <- This is the starting address of W matrix
LS SR5 SR0 2            # SR5 = memory[SR0 + 2] = 256 <- This is the number of rows in matrix 
LS SR6 SR0 3            # SR6 = memory[SR0 + 3] = 256 <- This is the number of columns in matrix (we are using this as stride for LV)
ADD SR7 SR4 SR6         # SR7 = SR4 + SR6 = 512 + 256 = 768 <- Last element of first row (JUMP #4 here...)
SS SR7 SR0 16           # memory[SR0 + 16] = SR7 = 768 <- Storing this in memory
LV VR1 SR1              # VR1 = memory[SR1] = memory[256] = [0, 1, 2 ... 63]
LVWS VR2 SR4 SR6        # VR2 = memory[SR4] with stride SR6 = memory[512] with stride 256 = first 64 elements of first column of W = [-1, 1, -1 ... 1] (JUMP #2 here...)
MULVV VR2 VR1 VR2       # VR2 = VR1 * VR2 = [0, 1, 2 ... 63] * [-1, 1, -1 ... 1]
PACKLO VR3 VR2 VR0      # VR3 = VR2[even elements] (JUMP #1 here...)
PACKHI VR4 VR2 VR0      # VR3 = VR2[odd elements]
ADDVV VR2 VR3 VR4       # VR2 = VR3 + VR4
SRA SR2 SR2 SR3         # SR2 = 64 >> 1 = 32
MTCL SR2                # VL = SR2 = 32
BNE SR2 SR3 -5          # IF SR2 != SR3 i.e SR2 != 1, THEN JUMP -5 (JUMP #1)
LS SR7 SR0 4            # SR7 = memory[SR0 + 4] = 0
LV VR5 SR7              # VR5 = memory[SR7]
ADDVV VR2 VR2 VR5       # VR2 = VR2 + VR5
SV VR2 SR7              # memory[SR7] = VR2[VL] = memory[0] = VR2[here VL = 1] = first element of VR2
ADD SR7 SR7 SR3         # SR7 = SR7 + SR3 = 0 + 1 = 1
SS SR7 SR0 4            # memory[SR0 + 4] = SR7 = 1
CVM                     # clear vector mask
POP SR2                 # SR2 = 64
MTCL SR2                # VL = SR2 = 64
ADD SR4 SR4 SR3         # SR4 = SR4 + SR3 = 256 + 1 = 513 <- This is the starting address of the second column of matrix
LS SR7 SR0 16           # SR7 = memory[SR0 + 16] = 768
BNE SR4 SR7 -19         # IF SR4 != SR7 i.e SR4 != 768, THEN JUMP -19 (JUMP #2)
LS SR4 SR0 1            # SR4 = memory[SR0 + 1] = 256
ADD SR4 SR4 SR6         # SR4 = SR4 + SR6 (JUMP #3 here...)
SUB SR2 SR2 SR3         # SR2 = SR2 - SR3 = 64 - 1 = 63
BGT SR2 SR0 -2          # IF SR2 > SR0 i.e SR2 > 0, THEN JUMP -2 (JUMP #3)
SS SR4 SR0 1            # memory[SR0 + 1] = SR4 <- Updated starting address 
CVM                     # clear vector mask
POP SR2                 # SR2 = 64
MTCL SR2                # VL = SR2 = 64
LS SR7 SR0 4            # SR7 = memory[SR0 + 4] = 66560
SUB SR7 SR7 SR6         # SR7 = SR7 - SR6 = 256 - 256 = 0
SS SR7 SR0 4            # memory[SR0 + 4] = SR7 = 0
ADD SR1 SR1 SR2         # SR1 = SR1 + SR2 = 256 + 64 = 320
SUB SR5 SR5 SR2         # SR5 = SR5 - SR2 = 256 - 64 = 192
BGT SR5 SR0 -36         # IF SR5 > SR0 i.e SR5 > 0, THEN JUMP -35 (JUMP #4)
LS SR4 SR0 5            # SR4 = memory[SR0 + 5] = 66048 <- This is the starting address of 'b'
LS SR5 SR0 2            # SR5 = memory[SR0 + 2] = 256 <- This is the length of the vector
LV VR1 SR4              # VR1 = memory[SR4] = memory[66048] = [128, 256, 128 ... 256] (JUMP #5 here...)
LV VR2 SR7              # VR2 = memory[SR7] = memory[0] = result of matrix multiplication
ADDVV VR2 VR1 VR2       # VR2 = VR1 + VR2
SV VR2 SR7              # memory[SR7] = memory[0] = VR2
ADD SR4 SR4 SR2         # SR4 = SR4 + SR2 = 66048 + 64 = 66112
ADD SR7 SR7 SR2         # SR7 = SR7 + SR2 = 0 + 64 = 64
SUB SR5 SR5 SR2         # SR5 = SR5 - SR2 = 256 - 64 = 192
BGT SR5 SR0 -7          # IF SR5 > SR0 i.e SR5 > 0, THEN JUMP -7 (JUMP #5)
HALT