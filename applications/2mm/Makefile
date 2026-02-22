CXX=/home/nessuno/llvm-project/build/bin/clang++
CFLAGS:=-Wall -Wextra -O3 -march=native -fopenmp -I/home/nessuno/llvm-project/build/lib/clang/21/include -L/home/nessuno/llvm-project/build/runtimes/runtimes-bins/openmp/runtime/src
OMPFLAGS:=-fopenmp -Wl,-rpath,/home/nessuno/llvm-project/build/runtimes/runtimes-bins/openmp/runtime/src -lomp
NUM_THREADS?=$(shell nproc)
DROP?=5

all: common

common:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DNUM_THREADS=1 2mm.cpp -o 2mm

omp:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DOMP -DNUM_THREADS=$(NUM_THREADS) 2mm.cpp -o 2mm

perfo_large:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO_LARGE -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) 2mm.cpp -o 2mm

perfo_init:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO_INIT -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) 2mm.cpp -o 2mm

perfo_fini:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO_FINI -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) 2mm.cpp -o 2mm

fastmath:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DOMP -DFASTMATH -DNUM_THREADS=$(NUM_THREADS) 2mm.cpp -o 2mm

memo:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DOMP -DDROP=$(DROP) -DMEMO -DNUM_THREADS=$(NUM_THREADS) 2mm.cpp -o 2mm

clean:
	@rm -f 2mm *.csv
