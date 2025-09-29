//===------------------------------------------------------------------------===
// IMPORTANT:  READ BEFORE DOWNLOADING, COPYING, INSTALLING OR USING.
// By downloading, copying, installing or using the software you agree
// to this license.  If you do not agree to this license, do not download,
// install, copy or use the software.
//
// Copyright (c) 2005 Northwestern University
// All rights reserved.
//
// Modified in 2025 by Victor Briganti.
//
// Redistribution of the software in source and binary forms,
// with or without modification, is permitted provided that the
// following conditions are met:
//
// 1       Redistributions of source code must retain the above copyright
//        notice, this list of conditions and the following disclaimer.
//
// 2       Redistributions in binary form must reproduce the above copyright
//        notice, this list of conditions and the following disclaimer in the
//        documentation and/or other materials provided with the distribution.
//
// 3       Neither the name of Northwestern University nor the names of its
//        contributors may be used to endorse or promote products derived
//        from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS
// IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
// TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, NON-INFRINGEMENT AND
// FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
// NORTHWESTERN UNIVERSITY OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
// INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
//(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
// HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
// STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
// ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//===------------------------------------------------------------------------===
// Kmeans
//
// Divides a dataset into a given number of clusters.
// The algorithm starts by randomly selecting initial cluster centers,
// then iteratively assigns each point to the nearest cluster center.
//
// Usage: ./kmeans <num_cluster> <iteration> <threshold> <input_file>
//
//===------------------------------------------------------------------------===

#include <cfloat>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <signal.h>
#include <unistd.h>
#include <utility>

//===------------------------------------------------------------------------===
// Kmeans
//===------------------------------------------------------------------------===

int find_nearest_point(float *centroids, int numClusters, float *features,
                       int point, int numFeatures) {
  int index = -1;
  float minDist = FLT_MAX;

  for (int i = 0; i < numClusters; i++) {
    float dist = 0.0f;

    for (int j = 0; j < numFeatures; j++) {
      int idxCentroid = i * numFeatures + j;
      int idxPoint = point * numFeatures + j;

      float diff = centroids[idxCentroid] - features[idxPoint];
      dist += diff * diff;
    }

    if (dist < minDist) {
      index = i;
      minDist = dist;
    }
  }

  return index;
}

float *kmeans_clustering(float *features, int numFeatures, int numPoints,
                         int numClusters, int iterations, float threshold) {
  float *centroids = new float[numClusters * numFeatures];
  float *newCentroids = new float[numClusters * numFeatures]();
  int *membership = new int[numPoints];
  int *newCentroidsLen = new int[numClusters]();

  for (int i = 0; i < numPoints; i++) {
    membership[i] = -1;
  }

  for (int i = 0; i < numClusters; i++) {
    int n = (rand() % numPoints);
    for (int j = 0; j < numFeatures; j++) {
      centroids[i * numFeatures + j] = features[n * numFeatures + j];
    }
  }

  for (int i = 0; i < iterations; i++) {
    double delta = 0.0f;
#pragma omp parallel shared(features, centroids, newCentroids, newCentroidsLen)
    {
#pragma omp for reduction(+ : delta)                                           \
    reduction(+ : newCentroids[ : numClusters * numFeatures]) schedule(static)
      for (int j = 0; j < numPoints; j++) {
        int index = find_nearest_point(centroids, numClusters, features, j,
                                       numFeatures);

        if (membership[j] != index) {
          delta += 1.0;
        }

        membership[j] = index;

        newCentroidsLen[index]++;
        for (int k = 0; k < numFeatures; k++) {
          newCentroids[index * numFeatures + k] +=
              features[j * numFeatures + k];
        }
      }

#pragma omp for collapse(2) schedule(static)
      for (int j = 0; j < numClusters; j++) {
        for (int k = 0; k < numFeatures; k++) {
          if (newCentroidsLen[j] > 0) {
            centroids[j * numFeatures + k] =
                newCentroids[j * numFeatures + k] / newCentroidsLen[j];
          }
        }
      }
    }

    std::memset(newCentroids, 0, numClusters * numFeatures * sizeof(float));
    std::memset(newCentroidsLen, 0, numClusters * sizeof(int));

    if (delta <= threshold) {
      break;
    }
  }

  delete[] newCentroids;
  delete[] membership;
  delete[] newCentroidsLen;
  return centroids;
}

//===------------------------------------------------------------------------===
// Helper Function
//===------------------------------------------------------------------------===

std::pair<int, int> readDatasetInfo(std::ifstream &file) {
  std::string line;
  getline(file, line);

  int numPoints = std::stoi(line.substr(0, line.find(' ')));
  int numFeatures = std::stoi(line.substr(line.find(' '), line.size()));

  return {numPoints, numFeatures};
}

float *readDataset(std::ifstream &file, int numPoints, int numFeatures) {
  float *attributes = new float[numPoints * numFeatures];

  int object = 0;
  std::string line;
  while (getline(file, line)) {
    int pos = 0;

    for (int att = 0; att < numFeatures; att++) {
      if (att + 1 == numFeatures) {
        attributes[object * numFeatures + att] =
            std::stod(line.substr(pos, line.size()));
      } else {
        attributes[object * numFeatures + att] =
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
  if (argc < 5) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0]
              << " <num_clusters> <iterations> <threshold> <input_file>\n";
    return -1;
  }

  int numClusters = std::stoi(argv[1]);
  if (numClusters <= 1) {
    std::cerr << "The number of clusters must be greater or equal to 2!\n";
    return -1;
  }

  int iterations = std::stoi(argv[2]);
  if (iterations < 1) {
    std::cerr << "The number of iterations at least 1!\n";
    return -1;
  }

  float threshold = std::stod(argv[3]);

  std::ifstream file(argv[4]);
  if (!file) {
    std::cerr << "Could not open file " << argv[4] << "\n";
    return -1;
  }

  auto [numPoints, numFeatures] = readDatasetInfo(file);
  float *features = readDataset(file, numPoints, numFeatures);

  srand(1);
  float *centroids = kmeans_clustering(features, numFeatures, numPoints,
                                       numClusters, iterations, threshold);

  for (int i = 0; i < numClusters; i++) {
    std::cout << i << ": ";
    for (int j = 0; j < numFeatures; j++) {
      std::cout << centroids[i * numFeatures + j]
                << (j + 1 == numFeatures ? "\n" : ",");
    }
  }

  return 0;
}
