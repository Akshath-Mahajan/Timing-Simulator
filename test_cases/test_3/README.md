VR1 = [1,2,3... 64]
SR1 = 32
VR2 = [32, 32, 32...]
VR1 == VR2
VR3 += VR1 = [0,0,0,..., 32, 0, 0,0, ..]
CVM

VR1 > VR2
VR4 += VR1 = [0,0,0,..., 32, 33, 34 ...]

NOTE: We change VR0 since we ran out of available RFs to check everything in 1 go.
This is feasible since VR0 = 0 is not an ISA condition but rather a convention.