CXX=clang++
CFLAGS:=-Wall -Wextra -O3
OMPFLAGS:=-fopenmp
NUM_THREADS?=$(shell nproc)
DROP?=0.5

all: common

common:
	$(CXX) $(CFLAGS) kmeans.cpp -o kmeans

omp:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DNUM_THREADS=$(NUM_THREADS) kmeans.cpp -o kmeans

clean:
	@rm -rf kmeans *.csv
