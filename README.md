
# Rooftop Solar Potential Estimation

This project is designed to estimate the rooftop solar energy potential in a given region using satellite imagery and machine learning techniques. The goal is to help identify optimal rooftops for solar panel installation, contributing to sustainable energy initiatives.

## Features

- **Satellite Imagery Processing**: Use of geospatial data for extracting building rooftop images.
- **Machine Learning for Solar Potential**: Trained models to estimate potential solar energy generation.
- **Data Visualization**: Visual representation of results using heatmaps and other graphical tools.
- **Automation**: Scripts to automate the process of rooftop analysis and solar potential estimation.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Model Details](#model-details)
- [Results](#results)
- [Contributing](#contributing)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/sd2879/rooftop_solar_potential.git
   ```

2. Navigate into the project directory:

   ```bash
   cd rooftop_solar_potential
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Preprocess the satellite imagery data:

   ```bash
   python preprocess.py --data <path_to_data>
   ```

## Model Details

- **Model Architecture**: Using Yolov8.
- **Training Data**: Processed from custom satellite imagery datasets.

## Results

The model provides a comprehensive analysis of rooftops in the target region, estimating the solar power generation capacity based on various factors like area, orientation, and sunlight exposure.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/your-feature-name`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature-name`).
5. Create a pull request.
