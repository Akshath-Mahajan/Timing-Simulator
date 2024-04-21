CVM             # Clear Vector Mask
LS SR1 SR0 1    # Load value 1
LS SR2 SR0 2    # Load value 2
LS SR3 SR0 3    # Load value 0 (vector base address, do not use elsewhere)
LS SR4 SR0 4    # Load kernel base address, do not use elsewhere
LS SR5 SR0 5    # Load value 128
LS SR6 SR0 6    # Load value ~ 80000 (output base address)

# loop1:
    # For every 3x256 chunk: 
    LS SR4 SR0 4        # Load kernel base address
    ADD SR6 SR2 SR1     # 3 (counter for inner loop)
    # loop2:
        # For every 1x256 row in this chunk:
        # Calculate conv for each kernel element
        # LS SR3 SR0 3    # Vector base
        # Kernel Element 0
        LS SR7 SR4 0        # Kernel element 0
        LVWS VR1 SR3 SR2    # 0, 2, 4 ..., 126
        ADD SR3 SR3 SR5     # New base 128
        LVWS VR2 SR3 SR2    # 128, ......., 254
        #
        MULVS VR1 VR1 SR7   # Conv operation
        MULVS VR2 VR2 SR7   # Conv operation
        ADDVV VR6 VR6 VR1   # Cumulate
        ADDVV VR7 VR7 VR2   # Cumulate
        #
        ADD SR3 SR3 SR1     # Add 1 to vector base
        ADD SR4 SR4 SR1     # Add 1 to kernel base
        #
        # Kernel Element 1
        LS SR7 SR4 0        # Kernel element 1  
        LVWS VR2 SR3 SR2    # 129, ......., 255
        SUB SR3 SR3 SR5     # Set SR3 to 1
        LVWS VR1 SR3 SR2    # 1, 3, ..... , 127
        #
        MULVS VR1 VR1 SR7   # Conv operation
        MULVS VR2 VR2 SR7   # Conv operation
        ADDVV VR6 VR6 VR1   # Cumulate
        ADDVV VR7 VR7 VR2   # Cumulate
        #
        ADD SR3 SR3 SR1     # Add 1 to vector base
        ADD SR4 SR4 SR1     # Add 1 to kernel base
        #
        # Kernel Element 2
        LS SR7 SR4 0        # Kernel element 2
        LVWS VR1 SR3 SR2    # 2, 4, ..... , 128
        ADD SR3 SR3 SR5     # Set SR3 to 12
        LVWS VR2 SR3 SR2    # 130, ......., 256
        #
        MULVS VR1 VR1 SR7   # Conv operation
        MULVS VR2 VR2 SR7   # Conv operation
        ADDVV VR6 VR6 VR1   # Cumulate
        #
        # Handle Padding (SR7 becomes free here)
        MFCL SR7
        SUB SR7 SR7 SR1 
        MTCL SR7            # SET VECTOR LENGTH TO 63 HERE
        ADDVV VR5 VR0 VR2   # Store 1-63 in temp regs
        ADD SR7 SR7 SR1
        MTCL SR7            # SET VECTOR LENGTH TO 64
        #
        ADDVV VR7 VR7 VR5   # Cumulate
        #
        # ADD SR3 SR3 SR1     # Add 1 to vector base
        ADD SR4 SR4 SR1     # Add 1 to kernel base
        #
        # Calculate new vector base address (for next row) !!!!!
        # SUB SR3 SR3 SR2     # SR3 = SR3 - 2 (don't do this to cover padding bits)
        ADD SR3 SR3 SR5     # SR3 = SR3 + 128 (SR3 = Base + 128 ALREADY)
        #
        SUB SR6 SR6 SR1     # SR6 = SR6 - 1    
        SUB SR3 SR3 SR2
        # SUB SR3 SR3 SR1
        BNE SR6 SR0 -38      # Loop back to next 1x256 row
        
    # STORE BELOW
    # Here, SR4, SR6, SR7 are available to update since we will load them back at beginning of loops.
    LS SR6 SR0 6        # Load value ~ 80000 (output base address)
    SV VR6 SR6          # Store 0-63
    MFCL SR7            # SR7 = 64
    ADD SR6 SR6 SR7     # SR6 = SR6 + 64
    SV VR7 SR6          # Store 64-127 (total 128 elements)
    ADD SR6 SR6 SR7     # SR6 = SR6 + 64
    #
    SS SR6 SR0 6        # Store value of new output base address
    #
    # Calculate new 3x256 chunk address in SR3
    #
    LS SR3 SR0 3
    ADD SR7 SR5 SR5     # SR7 = 256
    ADD SR7 SR7 SR7     # SR7 = 512
    ADD SR3 SR3 SR7     # SR3 = SR3 + 512 (2 rows)
    SS SR3 SR0 3
    #
    LS SR7 SR0 7        # Num iterations left
    SUB SR7 SR7 SR1     # SR7 --
    SS SR7 SR0 7        # Store result
    # Reset vectors
    ADDVV VR1 VR0 VR0
    ADDVV VR2 VR0 VR0
    ADDVV VR6 VR0 VR0
    ADDVV VR7 VR0 VR0
    BNE SR7 SR0 -60     # Loop back
HALT
