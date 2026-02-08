CXX=clang++
CFLAGS:=-Wall -Wextra -O3
OMPFLAGS:=-fopenmp
NUM_THREADS?=$(shell nproc)
DROP?=0.5

all: common

common:
	$(CXX) $(CFLAGS) pi.cpp -o pi

omp:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DNUM_THREADS=$(NUM_THREADS) pi.cpp -o pi

clean:
	@rm -rf pi *.csv
