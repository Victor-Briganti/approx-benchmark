INSERT INTO Server(hostname,cpu_description,hertz,cores,threads,ram_memory,operating_system)
VALUES ('Armagedon', 'i7-4790 Intel Core', 3.60, 4, 8, 32, 'Ubuntu 22.04.4 LTS');

INSERT INTO Benchmark(name,version,description)
VALUES ('2mm', 0, 'Multiply two matrixes with this result multiply with another matrix and output the result as a csv like structure (without the header).'),
       ('correlation', 0, 'Calculate the correlation between all columns of a csv file.'),
       ('deriche', 0, 'Deriche is a edge detector algorithm based on the canny edge detector algorithm.'),
       ('jacobi2d', 0, 'Performs a 2D Jacobi relaxation method on a square grid. Iteratively updates each cell in the grid to the average of its four neighbors. Used for solving partial differential equations such as Laplace''s equation.'),
       ('kmeans', 0, 'Divides a dataset into a given number of clusters. The algorithm starts by randomly selecting initial cluster centers, then iteratively assigns each point to the nearest cluster center.'),
       ('mandelbrot', 0, 'Calculates the mandelbrot set and ouputs it as a 1-bit P4 portable bitmap image.'),
       ('pi', 0, 'Calculates the PI number based on the Monte Carlo distribution.');

INSERT INTO BenchmarkInput(name,version,input)
VALUES ('2mm', 0, '{ "matrix_size": 4096 }'),
       ('correlation', 0, '{ "csv_file":  "./applications/correlation/input/input.csv" }'),
       ('deriche', 0, '{ "alpha": 1, "input_image": "./applications/deriche/input/sunflower.jpg", "output_image": "./applications/deriche/output/output.jpg" }'),
       ('jacobi2d', 0, '{ "matrix_size": 2048, "number_steps": 2 }'),
       ('kmeans', 0, '{ "num_clusters": 5, "iteration": 10, "threshold": 2, "input_file": "./applications/kmeans/input/kdd_cup.csv" }'),
       ('mandelbrot', 0, '{ "image_size": 1024 }'),
       ('pi', 0, '{ "num_iterations": 100000 }');
