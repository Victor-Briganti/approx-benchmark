CXX := clang++
CFLAGS := -Wall -Wextra
NUM_THREADS ?= $(shell nproc)

all: common

common:
	$(CXX) $(CFLAGS) kmeans.cpp -o kmeans.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp -DNUM_THREADS=$(NUM_THREADS) kmeans.cpp -o kmeans_omp.a 

clean:
	@rm -rf *.a *.csv