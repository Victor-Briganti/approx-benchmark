CXX := clang++
CFLAGS := -Wall -Wextra
NUM_THREADS ?= $(shell nproc)

all: common

common:
	$(CXX) $(CFLAGS) mandelbrot.cpp -o mandelbrot.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp -DNUM_THREADS=$(NUM_THREADS) mandelbrot.cpp -o mandelbrot_omp.a 

clean:
	rm -rf *.a *.bm