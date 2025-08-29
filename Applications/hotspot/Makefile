CXX := clang++
CFLAGS := -Wall -Wextra

all: common

common:
	$(CXX) $(CFLAGS) hotpost.cpp -o hotpost.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp hotpost.cpp -o hotpost_omp.a 

clean:
	@rm -rf *.a