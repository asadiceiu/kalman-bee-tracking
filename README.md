# Kalman Bee Tracking

This project implements a Kalman Filter-based tracking system for monitoring bee movements at hive entrances. 
It utilises detection results from a trained YOLOv8 model for bee detection and applies the Kalman Filter to 
track individual bees across video frames. A graphical user interface (GUI) is provided to facilitate interaction with the tracking results.

## Features

- **Bee Detection**: Assumes bees are already detected and the detection results are provided in CSV files.
- **Bee Tracking**: Utilizes a Kalman Filter to track bees over time, maintaining their identities across frames.
- **Graphical User Interface (GUI)**: Offers a user-friendly interface for exploring bee tracking results.

## Project Structure

- `kalman-filter-tracking.py`: Implements the Kalman filter and tracking logic.
- `tracking-gui.py`: Provides a graphical user interface for interacting with the tracking results.
- `utils.py`: Contains utility functions used throughout the project.
- `requirements.txt`: Lists all dependencies required to run the project.

## Installation

To set up the project locally, follow these steps:

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/asadiceiu/kalman-bee-tracking.git
   ```

2. **Navigate to the Project Directory**:

   ```bash
   cd kalman-bee-tracking
   ```

3. **Install Dependencies**:

   Ensure you have Python 3.8 or higher installed. Then, install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

   The required dependencies are:
   - numpy
   - matplotlib
   - pandas
   - scikit-learn
   - filterpy

## Usage

After installation, you can start the tracking system by running the following command:

```bash
python kalman-filter-tracking.py
```

This will launch the tracking system in command line interface, allowing you to track bees. 

If you already have tracking data available, you can explore the tracking results by-

```bash
python tracking-gui.py
```

This will launch the GUI, allowing you to load tracking results from the kalman filter and explore daily results.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

Special thanks to the developers of the YOLOv8 model and the open-source community for their invaluable tools and resources.

