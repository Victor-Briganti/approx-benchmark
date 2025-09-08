CXX := clang++
CFLAGS := -O3 -Wall -Wextra

all: common

common:
	$(CXX) $(CFLAGS)  pi.cpp -o pi.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp pi.cpp -o pi_omp.a 

clean:
	@rm -rf *.a *.csv