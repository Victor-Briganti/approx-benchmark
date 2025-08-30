CXX := clang++
CFLAGS := -Wall -Wextra

all: common

common:
	$(CXX) $(CFLAGS) kmeans.cpp -o kmeans.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp kmeans.cpp -o kmeans_omp.a 

clean:
	@rm -rf *.a *.csv