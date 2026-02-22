CXX=/home/nessuno/llvm-project/build/bin/clang++
CFLAGS:=-Wall -Wextra -O3 -march=native -fopenmp -I/home/nessuno/llvm-project/build/lib/clang/21/include -L/home/nessuno/llvm-project/build/runtimes/runtimes-bins/openmp/runtime/src
OMPFLAGS:=-fopenmp -Wl,-rpath,/home/nessuno/llvm-project/build/runtimes/runtimes-bins/openmp/runtime/src -lomp
NUM_THREADS?=$(shell nproc)
DROP?=5

all: common

common:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DNUM_THREADS=1 jacobi2d.cpp -o jacobi2d

omp:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DOMP -DNUM_THREADS=$(NUM_THREADS) jacobi2d.cpp -o jacobi2d

perfo_large:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO_LARGE -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) jacobi2d.cpp -o jacobi2d

perfo_init:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO_INIT -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) jacobi2d.cpp -o jacobi2d

perfo_fini:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DPERFO_FINI -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) jacobi2d.cpp -o jacobi2d

fastmath:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DOMP -DFASTMATH -DNUM_THREADS=$(NUM_THREADS) jacobi2d.cpp -o jacobi2d

memo:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DOMP -DMEMO -DDROP=$(DROP) -DNUM_THREADS=$(NUM_THREADS) jacobi2d.cpp -o jacobi2d

clean:
	@rm -f jacobi2d *.csv
