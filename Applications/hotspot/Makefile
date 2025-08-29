CXX := clang++
CFLAGS := -Wall -Wextra -O3

all: common

common:
	$(CXX) $(CFLAGS) hotspot.cpp -o hotspot.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp hotspot.cpp -o hotspot_omp.a 

clean:
	@rm -rf *.a