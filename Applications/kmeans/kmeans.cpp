#include <fstream>
#include <iostream>
#include <utility>

//===------------------------------------------------------------------------===
// Kmeans
//===------------------------------------------------------------------------===

void kmeans_clustering(float *features, int numFeatures, int numPoints,
                       int numClusters, float threshold, int *membership) {
  float *clusters = new float[numClusters * numFeatures];

  for (int i = 0; i < numClusters; i++) {
    int n = rand() % numPoints;
    for (int j = 0; j < numFeatures; j++) {
      clusters[i * numFeatures + j] = features[n * numFeatures + j];
    }
  }
}

//===------------------------------------------------------------------------===
// Helper Function
//===------------------------------------------------------------------------===

std::pair<int, int> readDatasetInfo(std::ifstream &file) {
  std::string line;
  getline(file, line);

  int numObjects = std::stoi(line.substr(0, line.find(' ')));
  int numAttributes = std::stoi(line.substr(line.find(' '), line.size()));

  return {numObjects, numAttributes};
}

float *readDataset(std::ifstream &file, int numObjects, int numAttributes) {
  float *attributes = new float[numObjects * numAttributes];

  int object = 0;
  std::string line;
  while (getline(file, line)) {
    int pos = 0;

    for (int att = 0; att < numAttributes; att++) {
      if (att + 1 == numAttributes) {
        attributes[object * numAttributes + att] =
            std::stod(line.substr(pos, line.size()));
      } else {
        attributes[object * numAttributes + att] =
            std::stod(line.substr(pos, line.find(',', pos) - pos));
        pos = line.find(',', pos) + 1;
      }
    }

    object++;
  }

  return attributes;
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

  auto [numObjects, numAttributes] = readDatasetInfo(file);
  float *data = readDataset(file, numObjects, numAttributes);

  srand(1);
}
