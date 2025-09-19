#!/bin/bash

set -e

# Path for applications
APPLICATION_PATH=Applications
OUTPUT_PATH=Output
PERFORMANCE_PATH=Performance

# Number of executions
NUM_EXEC=3

# Number of executions to measure variation
NUM_VAR_EXEC=10

# Number of threads for execution
threads=(1 2 4 8)

# applications=(2mm correlation deriche jacobi-2d kmeans mandelbrot pi)
applications=(2mm)

run_2mm () {
    $app_bin 1024 > $output_path &
}

run_perf () {
    perf stat -t $pid -o $performance_path &
}

# Base test to verify cycle variation
for thread in "${threads[@]}"; do
    for app in "${applications[@]}"; do
        # Compile the application
        make NUM_THREADS=$thread omp -C $APPLICATION_PATH/$app
        
        # Mount the binary path
        app_bin=$APPLICATION_PATH/$app/$app\_omp.a

        for i in $(seq 1 $NUM_VAR_EXEC); do
            # Build the paths that are going to be used
            output_path=/dev/null
            performance_path=$PERFORMANCE_PATH/$app/base/$app$thread\_$i
            
            # Execute the program and save the PID of the background process
            run_2mm $i
            pid=$!

            # This is a busy loop that is here only to avoid some problem with the scheduler
            while [ "$(ps -o state= -p $pid)" != T ]; do
                sleep 0.1
            done

            # Run perf to get the performance and wait for the application to finish
            run_perf $i
            kill -SIGCONT $pid
            wait $pid
        done
    done
done

# Common execution
for app in "${applications[@]}"; do
    # Compile the application
    make -C $APPLICATION_PATH/$app
    
    # Mount the binary path
    app_bin=$APPLICATION_PATH/$app/$app.a

    for i in $(seq 1 $NUM_EXEC); do
        # Build the paths that are going to be used
        output_path=$OUTPUT_PATH/$app/common/$app\_$i.csv
        performance_path=$PERFORMANCE_PATH/$app/common/$app\_$i
        
        # Execute the program and save the PID of the background process
        run_2mm $i
        pid=$!

        # This is a busy loop that is here only to avoid some problem with the scheduler
        while [ "$(ps -o state= -p $pid)" != T ]; do
            sleep 0.1
        done

        # Run perf to get the performance and wait for the application to finish
        run_perf $i
        kill -SIGCONT $pid
        wait $pid
    done
done

# OpenMP execution
for thread in "${threads[@]}"; do
    for app in "${applications[@]}"; do
        # Compile the application
        make NUM_THREADS=$thread omp -C $APPLICATION_PATH/$app
        
        # Mount the binary path
        app_bin=$APPLICATION_PATH/$app/$app\_omp.a

        for i in $(seq 1 $NUM_EXEC); do
            # Build the paths that are going to be used
            output_path=$OUTPUT_PATH/$app/omp/$app$thread\_$i.csv
            performance_path=$PERFORMANCE_PATH/$app/omp/$app$thread\_$i
            
            # Execute the program and save the PID of the background process
            run_2mm $i
            pid=$!

            # This is a busy loop that is here only to avoid some problem with the scheduler
            while [ "$(ps -o state= -p $pid)" != T ]; do
                sleep 0.1
            done

            # Run perf to get the performance and wait for the application to finish
            run_perf $i
            kill -SIGCONT $pid
            wait $pid
        done
    done
done

