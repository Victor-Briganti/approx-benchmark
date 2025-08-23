CXX := clang++
CFLAGS := -Wall -Wextra

all: common

common:
	$(CXX) $(CFLAGS) 2mm.cpp -o 2mm.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp 2mm.cpp -o 2mm_omp.a 

clean:
	@rm -rf *.a *.csv