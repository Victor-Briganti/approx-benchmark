CXX := clang++
CFLAGS := -O3 -Wall -Wextra
NUM_THREADS ?= $(shell nproc)

all: common

common:
	$(CXX) $(CFLAGS)  pi.cpp -o pi.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp -DNUM_THREADS=$(NUM_THREADS) pi.cpp -o pi_omp.a 

clean:
	@rm -rf *.a *.csv