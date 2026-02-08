CXX=clang++
CFLAGS:=-Wall -Wextra -O3
OMPFLAGS:=-fopenmp
NUM_THREADS?=$(shell nproc)
DROP?=0.5

all: common

common:
	$(CXX) $(CFLAGS) jacobi2d.cpp -o jacobi2d

omp:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DNUM_THREADS=$(NUM_THREADS) jacobi2d.cpp -o jacobi2d

clean:
	@rm -rf jacobi2d *.csv
