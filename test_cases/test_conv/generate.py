vdmem = ""
b = False

for _ in range(20000):
    vdmem+= "0\n"
    
for _ in range(256):
    b = not b
    for __ in range(256):
        b = not b
        if b:
            vdmem += "1\n"
        else:
            vdmem += "-1\n"
    # vdmem+="0\n0\n"

# for _ in range(1):
#     for __ in range(256):
#         vdmem+="0\n"
#     vdmem+="0\n0\n"

with open('VDMEM.txt', 'w') as file:
    file.write(vdmem)
    

# with open('expected.txt', 'w') as file:
#     file.write(vdmem)