CXX := clang++
CFLAGS := -Wall -Wextra

all: common

common:
	$(CXX) $(CFLAGS) correlation.cpp -o correlation.a 

omp:
	$(CXX) $(CFLAGS) -fopenmp correlation.cpp -o correlation.a 

csv:
	python generate_csv.py

clean:
	rm -rf *.a *.bm
