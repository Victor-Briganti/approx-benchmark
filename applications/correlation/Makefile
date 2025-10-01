CXX=/home/aJoaoBriganti/bin/clang++ --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/12
CFLAGS:=-Wall -Wextra -O3 -stdlib=libstdc++
OMPFLAGS:=-fopenmp -I/home/aJoaoBriganti/approx-llvm/build/projects/openmp/runtime/src/ -lomp -L/home/aJoaoBriganti/approx-llvm/build/lib -Wl,-rpath,/home/aJoaoBriganti/approx-llvm/build/lib
NUM_THREADS?=$(shell nproc)

all: common

common:
	$(CXX) $(CFLAGS) correlation.cpp -o correlation.a 

omp:
	$(CXX) $(CFLAGS) $(OMPFLAGS) -DNUM_THREADS=$(NUM_THREADS) correlation.cpp -o correlation_omp.a 

clean:
	@rm -rf *.a *.csv