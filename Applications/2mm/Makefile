CXX := clang++
CFLAGS := -Wall -Wextra
NUM_THREADS ?= $(shell nproc)

all: common

common:
	$(CXX) $(CFLAGS) 2mm.cpp -o 2mm.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp -DNUM_THREADS=$(NUM_THREADS) 2mm.cpp -o 2mm_omp.a 

clean:
	@rm -rf *.a *.csv