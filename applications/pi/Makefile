CXX=/home/nessuno/Documents/workspace/IC/LLVM/llvm-project.approx/build/bin/clang++
CFLAGS:=-Wall -Wextra -O3 -march=native -fopenmp -I/home/nessuno/Documents/workspace/IC/LLVM/llvm-project.approx/build/lib/clang/21/include -L/home/nessuno/Documents/workspace/IC/LLVM/llvm-project.approx/build/runtimes/runtimes-bins/openmp/runtime/src
OMPFLAGS:=-fopenmp -Wl,-rpath,/home/nessuno/Documents/workspace/IC/LLVM/llvm-project.approx/build/runtimes/runtimes-bins/openmp/runtime/src -lomp
NUM_THREADS?=$(shell nproc)
DROP?=5

all: common

common:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DNUM_THREADS=1 pi.cpp -o pi

omp:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DOMP -DNUM_THREADS=$(NUM_THREADS) pi.cpp -o pi

perfo_large:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO_LARGE -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) pi.cpp -o pi

perfo_init:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO_INIT -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) pi.cpp -o pi

perfo_fini:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO_FINI -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) pi.cpp -o pi

fastmath:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DOMP -DFASTMATH -DNUM_THREADS=$(NUM_THREADS) pi.cpp -o pi

clean:
	@rm -f pi *.csv
