import os
import random as rand

COLUMNS = 256
ROWS = 8192

CWD = os.getcwd() + "/Applications/correlation"

with open(f'{CWD}/input.csv', 'w') as file:
    file.write(f'{COLUMNS} {ROWS}\n')

    for j in range(ROWS):
        for i in range(0, COLUMNS):
            file.write(str(rand.random()))
            
            if i + 1 == COLUMNS:
                file.write('\n')
            else:
                file.write(',')