CXX := clang++
CFLAGS := -Wall -Wextra -g3 -O3
NUM_THREADS ?= $(shell nproc)

all: common

common:
	$(CXX) $(CFLAGS) jacobi2d.cpp -o jacobi2d.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp -DNUM_THREADS=$(NUM_THREADS) jacobi2d.cpp -o jacobi2d_omp.a 

clean:
	@rm -rf *.a *.csv
