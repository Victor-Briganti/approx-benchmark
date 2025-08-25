#include <cmath>
#include <fstream>
#include <iostream>
#include <string>

//===------------------------------------------------------------------------===
// Correlation
//===------------------------------------------------------------------------===

double correlation(double *x, double *y, int rows) {
  double sumX = 0;
  double sumY = 0;
  double sumXY = 0;
  double sumX2 = 0;
  double sumY2 = 0;

  for (size_t i = 0; i < rows; i++) {
    sumX += x[i];
    sumY += y[i];
    sumXY += x[i] * y[i];
    sumX2 += x[i] * x[i];
    sumY2 += y[i] * y[i];
  }

  double numerador = rows * sumXY - sumX * sumY;
  double denominador = std::sqrt((rows * sumX2 - (sumX * sumX)) *
                                 (rows * sumY2 - (sumY * sumY)));
  return numerador / denominador;
}

double *correlationMatrix(double **&data, int columns, int rows) {
  double *matrix = new double[columns * rows]();

#pragma omp parallel for collapse(2) shared(matrix)
  for (int i = 0; i < columns; i++) {
    for (int j = i; j < columns; j++) {
      double r = (j == i) ? 1.0 : correlation(data[i], data[j], rows);
      matrix[i * columns + j] = r;
      matrix[j * columns + i] = r;
    }
  }

  return matrix;
}

//===------------------------------------------------------------------------===
// Helper Function
//===------------------------------------------------------------------------===

std::pair<int, int> readDimensions(std::ifstream &file) {
  std::string line;
  getline(file, line);

  int columnNum = std::stoi(line.substr(0, line.find(' ')));
  int rowNum = std::stoi(line.substr(line.find(' '), line.size()));

  return {columnNum, rowNum};
}

double **readData(std::ifstream &file, int columns, int rows) {
  double **data = new double *[columns];

  for (int i = 0; i < columns; i++) {
    data[i] = new double[rows];
  }

  int row = 0;
  std::string line;
  while (getline(file, line)) {
    int pos = 0;

    for (int column = 0; column < columns; column++) {
      if (column + 1 == columns) {
        data[column][row] = std::stod(line.substr(pos, line.size()));
      } else {
        data[column][row] = std::stod(line.substr(pos, line.find(',')));
        pos = line.find(',', pos) + 1;
      }
    }

    row++;
  }

  return data;
}

//===------------------------------------------------------------------------===
// Main
//===------------------------------------------------------------------------===

int main(int argc, char **argv) {
  if (argc < 2) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0] << " <input_file>\n";
    return -1;
  }

  std::ifstream file(argv[1]);
  if (!file) {
    std::cerr << "Could not open file " << argv[1] << "\n";
    return -1;
  }

  auto [columns, rows] = readDimensions(file);
  double **data = readData(file, columns, rows);

  double *matrix = correlationMatrix(data, columns, rows);

  for (int i = 0; i < columns; i++) {
    for (int j = 0; j < columns; j++) {
      std::cout << matrix[i * columns + j] << " ";
    }
    std::cout << "\n";
  }

  return 0;
}
