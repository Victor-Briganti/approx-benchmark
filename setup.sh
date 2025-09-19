#!/bin/bash

applications=(2mm correlation deriche jacobi-2d kmeans mandelbrot pi)
threads=(1 2 4 8 12 16)

# Create the directory for the outputs and the performance for each application
# Directory with the outputs of the applications
mkdir -p Output
mkdir -p Performance
for app in "${applications[@]}"; do
    mkdir -p Output/$app/common
    mkdir -p Output/$app/omp
    mkdir -p Output/$app/approx

    if [ $app = "2mm" ]; then
        mkdir -p Performance/$app/base
    fi

    mkdir -p Performance/$app/common
    mkdir -p Performance/$app/omp
    mkdir -p Performance/$app/approx
done

