import numpy as np
braille_patterns_list = []
for i in range(int('2800', 16), int('2900', 16)):
    braille_patterns_list.append(chr(i))
# 1   8
# 2   16
# 4   32
# 64  128

dot_indexs = [1, 8, 2, 16, 4, 32, 64, 128]
arranged_braille_patterns = []
for i in range(256):
    chr_index = 0
    cnt = 0
    while i != 0:
        if i & 1:
            chr_index += dot_indexs[cnt]
        cnt += 1
        i >>= 1
    arranged_braille_patterns.append(braille_patterns_list[chr_index])

braille_patterns_list = np.array(arranged_braille_patterns)

