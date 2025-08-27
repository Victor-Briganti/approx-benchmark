#include <algorithm>
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#include <cstdint>
#include <iostream>

//===------------------------------------------------------------------------===
// Helper Functions
//===------------------------------------------------------------------------===

float *grayscale(const uint8_t *image, int width, int height, int channels) {
  constexpr float RED_WEIGHT = 0.299f;
  constexpr float GREEN_WEIGHT = 0.587f;
  constexpr float BLUE_WEIGHT = 0.114f;

  float *grayImage = new float[width * height];

  for (int i = 0; i < height; i++) {
    for (int j = 0; j < width; j++) {
      int index = (i * width + j) * channels;
      float red = image[index];
      float green = (channels > 1) ? image[index + 1] : red;
      float blue = (channels > 2) ? image[index + 2] : red;

      grayImage[i * width + j] =
          red * RED_WEIGHT + green * GREEN_WEIGHT + blue * BLUE_WEIGHT;
    }
  }

  return grayImage;
}

unsigned char *convert(const float *image, int width, int height) {
  unsigned char *outputImage = new unsigned char[width * height];

  for (int i = 0; i < height; i++) {
    for (int j = 0; j < width; j++) {
      outputImage[i * width + j] = static_cast<unsigned char>(
          std::clamp(image[i * width + j], 0.0f, 255.0f));
    }
  }

  return outputImage;
}

//===------------------------------------------------------------------------===
// Deriche
//===------------------------------------------------------------------------===

//===------------------------------------------------------------------------===
// Main
//===------------------------------------------------------------------------===

int main(int argc, char **argv) {
  if (argc < 3) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0] << " <input_image> <output_image>\n";
    return -1;
  }

  int width, height, channels;
  uint8_t *image = stbi_load(argv[1], &width, &height, &channels, 0);
  if (!image) {
    std::cerr << "Could not load the image " << argv[1] << "\n";
    return -1;
  }

  float *grayImage = grayscale(image, width, height, channels);
  stbi_image_free(image);

  unsigned char *output = convert(grayImage, width, height);

  stbi_write_jpg(argv[2], width, height, 1, output, 100);

  return 0;
}