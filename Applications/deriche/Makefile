CXX := clang++
CFLAGS := -Wall -Wextra

all: common

common:
	$(CXX) $(CFLAGS) deriche.cpp -o deriche.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp deriche.cpp -o deriche_omp.a 

clean:
	@rm -rf *.a