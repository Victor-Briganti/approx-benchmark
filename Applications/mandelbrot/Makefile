CXX := clang++
CFLAGS := -Wall -Wextra

all: common

common:
	$(CXX) $(CFLAGS) mandelbrot.cpp -o mandelbrot.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp mandelbrot.cpp -o mandelbrot_omp.a 

clean:
	rm -rf *.a *.bm