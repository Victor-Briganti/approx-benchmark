CXX := clang++
CFLAGS := -Wall -Wextra
NUM_THREADS ?= $(shell nproc)

all: common

common:
	$(CXX) $(CFLAGS) correlation.cpp -o correlation.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp -DNUM_THREADS=$(NUM_THREADS) correlation.cpp -o correlation.a 

csv:
	python generate_csv.py

clean:
	rm -rf *.a *.bm
