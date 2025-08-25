#include <cmath>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

//===------------------------------------------------------------------------===
// Correlation
//===------------------------------------------------------------------------===

double correlation(std::vector<std::vector<double>> &values, int x, int y) {
  double sumX = 0;
  double sumY = 0;
  double sumXY = 0;
  double sumX2 = 0;
  double sumY2 = 0;

  for (size_t i = 0; i < values[x].size(); i++) {
    sumX += values[x][i];
    sumY += values[x][i];
    sumXY += values[x][i] * values[y][i];
    sumX2 += values[x][i] * values[x][i];
    sumY2 += values[y][i] * values[y][i];
  }

  double numerador = values[x].size() * sumXY - sumX * sumY;

  double denominador1 = values[x].size() * sumX2 - (sumX * sumX);
  double denominador2 = values[x].size() * sumY2 - (sumY * sumY);
  double denominador = std::sqrt(denominador1 * denominador2);

  return numerador / denominador;
}

std::vector<std::vector<double>>
correlationMatrix(std::vector<std::vector<double>> &values) {
  std::vector<std::vector<double>> matrix;

  for (size_t i = 0; i < values.size(); i++) {
    std::vector<double> row(values.size(), 0.0);
    matrix.push_back(row);
  }

  for (size_t i = 0; i < values.size(); i++) {
    for (size_t j = i; j < values.size(); j++) {
      if (j == i) {
        matrix[i][j] = 1.0;
      } else {
        double r = correlation(values, i, j);
        matrix[i][j] = r;
        matrix[j][i] = r;
      }
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

std::vector<std::vector<double>> readData(std::ifstream &file, int columns,
                                          int rows) {
  std::vector<std::vector<double>> values;
  values.reserve(columns);

  for (int i = 0; i < columns; i++) {
    std::vector<double> column;
    column.reserve(rows);
    values.push_back(column);
  }

  std::string line;
  while (getline(file, line)) {
    int pos = 0;

    for (int i = 0; i < columns; i++) {
      if (i + 1 == columns) {
        values[i].push_back(std::stod(line.substr(pos, line.size())));
      } else {
        values[i].push_back(std::stod(line.substr(pos, line.find(','))));
        pos = line.find(',', pos) + 1;
      }
    }
  }

  return values;
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

  auto [columnNum, rowNum] = readDimensions(file);
  auto values = readData(file, columnNum, rowNum);

  auto matrix = correlationMatrix(values);

  for (size_t i = 0; i < columnNum; i++) {
    for (size_t j = 0; j < columnNum; j++) {
      std::cout << matrix[i][j] << " ";
    }
    std::cout << "\n";
  }

  return 0;
}
