CXX := clang++
CFLAGS := -Wall -Wextra

all: common

common:
	$(CXX) $(CFLAGS) -O3 deriche.cpp -o deriche.a 

omp:
	$(CXX) $(CFLAGS) -O3 -fopenmp deriche.cpp -o deriche_omp.a 

clean:
	@rm -rf *.a *.csv