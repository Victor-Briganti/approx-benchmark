CXX := clang++
CFLAGS := -Wall -Wextra
NUM_THREADS ?= $(shell nproc)

all: common

common:
	$(CXX) $(CFLAGS) deriche.cpp -o deriche.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp -DNUM_THREADS=$(NUM_THREADS) deriche.cpp -o deriche_omp.a 

clean:
	@rm -rf *.a