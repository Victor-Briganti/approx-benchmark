#!/bin/bash

set -e

# Path for applications
APPLICATION_PATH=Applications
OUTPUT_PATH=Output
PERFORMANCE_PATH=Performance

# Number of executions
NUM_EXEC=1

# Number of executions to measure variation
NUM_VAR_EXEC=10

# Number of threads for execution
threads=(1 2 4 8)

applications=(2mm correlation deriche jacobi2d kmeans mandelbrot pi)

run_2mm () {
    $app_bin 512 > $output_path &
}

run_correlation () {
    $app_bin $input_path > $output_path &
}

run_deriche () {
    $app_bin 1 $input_path $output_path &
}

run_jacobi2d () {
    $app_bin 4096 5 > $output_path &
}

run_mandelbrot () {
    $app_bin 1024 > $output_path &
}

run_kmeans () {
    $app_bin 5 1000 15 $input_path > $output_path &
}

run_pi () {
    $app_bin 512 > $output_path &
}

run_perf () {
    perf stat -e cycles,instructions -t $pid -o $performance_path &
}

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
        case $app in
            2mm)
                run_2mm
                ;;
            correlation)
                input_path=$APPLICATION_PATH/$app/input.csv
                run_correlation
                ;;
            deriche)
                output_path=$OUTPUT_PATH/$app/common/$app\_$i.jpg
                input_path=$APPLICATION_PATH/$app/input/sunflower.jpg
                run_deriche
                ;;
            jacobi2d)
                run_jacobi2d
                ;;
            mandelbrot)
                output_path=$OUTPUT_PATH/$app/common/$app\_$i.bmp
                run_mandelbrot
                ;;
            kmeans)
                input_path=$APPLICATION_PATH/$app/input/kdd_cup.csv
                run_kmeans
                ;;
            pi)
                run_pi
                ;;
            *)
                echo "$app not reconized"
                exit -1
                ;;
        esac
        pid=$!

        # In theroy I shouldn't need this, but PI is proving me wrong
        kill -SIGSTOP $pid
        
        # This is a busy loop that is here only to avoid some problem with the scheduler
        while [ "$(ps -o state= -p $pid)" != "T" ]; do
            sleep 0.1
        done

        # Run perf to get the performance and wait for the application to finish
        run_perf
        ppid=$!

        # This is another busy loop to guarantee that the process continue
        while [ "$(ps -o state= -p $pid)" == "T" ]; do
            kill -SIGCONT $pid
            sleep 0.1
        done
        
        wait $ppid
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
            case $app in
                2mm)
                    run_2mm
                    ;;
                correlation)
                    input_path=$APPLICATION_PATH/$app/input.csv
                    run_correlation
                    ;;
                deriche)
                    output_path=$OUTPUT_PATH/$app/omp/$app$thread\_$i.jpg
                    input_path=$APPLICATION_PATH/$app/input/sunflower.jpg
                    run_deriche
                    ;;
                jacobi2d)
                    run_jacobi2d
                    ;;
                mandelbrot)
                    output_path=$OUTPUT_PATH/$app/omp/$app$thread\_$i.bmp
                    run_mandelbrot
                    ;;
                kmeans)
                    input_path=$APPLICATION_PATH/$app/input/kdd_cup.csv
                    run_kmeans
                    ;;
                pi)
                    run_pi
                    ;;
                *)
                    echo "$app not reconized"
                    exit -1
                    ;;
            esac
            pid=$!
    
            # In theroy I shouldn't need this, but PI is proving me wrong
            kill -SIGSTOP $pid
            
            # This is a busy loop that is here only to avoid some problem with the scheduler
            while [ "$(ps -o state= -p $pid)" != "T" ]; do
                sleep 0.1
            done
    
            # Run perf to get the performance and wait for the application to finish
            run_perf
            ppid=$!
    
            # This is another busy loop to guarantee that the process continue
            while [ "$(ps -o state= -p $pid)" == "T" ]; do
                kill -SIGCONT $pid
                sleep 0.1
            done
            
            wait $ppid
            wait $pid
        done
    done
done
