CXX := clang++
CFLAGS := -Wall -Wextra

all: common

common:
	$(CXX) $(CFLAGS) jacobi2d.cpp -o jacobi2d.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp jacobi2d.cpp -o jacobi2d_omp.a 

clean:
	@rm -rf *.a *.csv