CXX=clang++
CFLAGS:=-Wall -Wextra -O3
OMPFLAGS:=-fopenmp
NUM_THREADS?=$(shell nproc)
DROP?=0.5

all: common

common:
	$(CXX) $(CFLAGS) 2mm.cpp -o 2mm

omp:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DNUM_THREADS=$(NUM_THREADS) 2mm.cpp -o 2mm

perfo_default:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO=1 -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) 2mm.cpp -o 2mm

clean:
	@rm -f 2mm *.csv
