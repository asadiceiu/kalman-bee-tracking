import math
import os
import time
from utils import get_date_from_filename as get_date, get_time_from_filename as get_time
import pandas as pd
import numpy as np
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment


class KalmanFilterCLI:
    """
    Command Line Interface for Kalman Filter Tracking
    """
    def __init__(self, csv_folder:str, output_folder:str, ellipses_file:str) -> None:
        """
        Initialize the Kalman Filter CLI
        :param csv_folder: str - Path to the folder containing the CSV files
        :param output_folder: str - Path to the folder where the output files will be stored
        :param ellipses_file: str - Path to the file containing the ellipses data
        """
        self.all_tracks = []
        self.current_track_id = None
        self.df = None
        self.start_frame = 1
        self.end_frame = 1
        self.process_noise = 1e-4
        self.measurement_noise = 0.1
        self.distance_threshold = 50
        self.max_frames_before_death = 20
        self.date = None
        self.counter = {
            'inside': 0,
            'enter': 0,
            'exit': 0,
            'outside': 0
        }
        self.output_folder = output_folder
        self.ellipses_file = ellipses_file
        os.makedirs(self.output_folder, exist_ok=True)
        self.ellipses = None
        self.load_ellipses()
        self.csv_folder = csv_folder
        self.load_csv_folder()
    
    def load_csv_folder(self):
        """
        Load the CSV folder and get the list of CSV files
        """
        folder_path = self.csv_folder
        print(f"Checking CSV Folder: {folder_path}")
        if os.path.isdir(folder_path):
            self.folder_path = folder_path
            files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
            self.csv_files = [os.path.join(folder_path, f) for f in files]
            self.csv_files = sorted(self.csv_files, key=lambda x: get_time(x), reverse=True)
            self.csv_files = sorted(self.csv_files, key=lambda x: get_date(x), reverse=True)
            # inverse sort 

            print(f"CSV Folder: {folder_path}. Total CSV Files: {len(self.csv_files)}")
    
    def load_ellipses(self):
        """
        Load the ellipses data from the file
        """
        if not os.path.exists(self.ellipses_file):
            print(f"Fatal: Ellipses file not found: {self.ellipses_file}")
            exit(1)
        with open(self.ellipses_file, 'r') as f:
            lines = f.readlines()
            # print(lines)
            self.ellipses = eval(lines[0])
    
    def reset_variables(self):
        """
        Reset the variables to default values
        """
        self.all_tracks = []
        self.current_track_id = None
        self.df = None
        self.start_frame = 1
        self.end_frame = 1
        self.process_noise = 1e-4
        self.measurement_noise = 0.1
        self.date = None
        self.counter = {
            'inside': 0,
            'enter': 0,
            'exit': 0,
            'outside': 0
        }
    
    def load_csv(self, file_path)->bool:
        """
        Load the CSV file and check if it is valid
        :param file_path: str - Path to the CSV file
        :return: bool - True if the CSV file is valid, False otherwise
        """
        self.df = pd.read_csv(file_path)
        self.df.columns = self.df.columns.str.strip()
        if 'center_x' not in self.df.columns or 'center_y' not in self.df.columns or 'video_frame_id' not in self.df.columns:
            self.reset_variables()
            return False
        record_count = len(self.df)
        if record_count < 5:
            self.reset_variables()
            return False
        min_frame = self.df['video_frame_id'].min()
        max_frame = self.df['video_frame_id'].max()
        print(f"Min Frame: {min_frame}. Max Frame: {max_frame}")
        if abs(max_frame - min_frame) < 5:
            self.reset_variables()
            return False
        self.start_frame = min_frame
        self.end_frame = max_frame
        # get the date from the file name
        self.date = get_date(file_path) # datetime.datetime.strptime(file_path.split("_")[2], '%Y%m%d')
        self.ellipse = self.ellipses[self.date] if self.date in self.ellipses else None
        self.file_path = file_path
        return True
    
    def check_already_processed(self, file_path:str)->bool:
        """
        Check if the CSV file has already been processed
        :param file_path: str - Path to the CSV file
        :return: bool - True if the file has already been processed, False otherwise
        """
        with open(os.path.join(self.output_folder,'track-stats.csv'),'a+') as f:
            f.seek(0)
            lines = f.readlines()
            for line in lines:
                if os.path.basename(file_path) in line:
                    return True
        return False
    
    def write_stats_to_csv_file(self, file_path=None, no_data=False)->None:
        """
        Write the tracking statistics to the CSV file
        :param file_path: str - Path to the CSV file
        :param no_data: bool - True if no data was found in the CSV file, False otherwise
        """
        if no_data:
            with open(os.path.join(self.output_folder,'track-stats.txt'),'a+') as f:
                f.write("-------------------------------------------------\n")
                f.write(f"CSV File: {os.path.basename(file_path)}. No Data Found\n")
                f.write("-------------------------------------------------\n")
            
            with open(os.path.join(self.output_folder,'track-stats.csv'),'a+') as f:
                f.write(f"{os.path.basename(file_path)},0,0,0,0,0,0\n")
            return
        enter, exit, inside, outside = self.counter['enter'], self.counter['exit'], self.counter['inside'], self.counter['outside']
        with open(os.path.join(self.output_folder,'track-stats.txt'),'a+') as f:
            f.write("-------------------------------------------------\n")
            f.write(f"CSV File: {os.path.basename(self.file_path)}. Total Records: {len(self.df)}. Date: {self.date}\n")
            f.write(f"Start Frame: {self.start_frame}. End Frame: {self.end_frame}\n")
            f.write(f"Distance Threshold: {self.distance_threshold}. Max Frames Before Death: {self.max_frames_before_death}\n")
            f.write(f"Total Tracks: {len(self.all_tracks)}\n")
            f.write(f"Enter: {enter}. Exit: {exit}. Inside: {inside}. Outside: {outside}\n")
            f.write("-------------------------------------------------\n")

        with open(os.path.join(self.output_folder,'track-stats.csv'),'a+') as f:
            f.write(f"{os.path.basename(self.file_path)},{len(self.df)},{len(self.all_tracks)},{enter},{exit},{inside},{outside}\n")
            

    def track_insects(self):
        """
        Track the insects in the CSV files
        """
        files = self.csv_files
        if not files:
            print("No CSV files found in the folder.")
            return
        total_files = len(files)
        print(f"Total CSV Files found on {self.csv_folder}: {total_files}")
        current_file = 0

        for file in files:
            current_file += 1

            file_date = get_date(file)
            if file_date not in self.ellipses:
                print(f"Skipping file {os.path.basename(file)}. Ellipse not found for date {file_date}")
                continue

            t1 = time.time()
            self.reset_variables()
            
            if self.check_already_processed(file):
                continue
            csv_loaded = self.load_csv(file)
            if csv_loaded:    
                self.track_insects_one_file()
                self.write_stats_to_csv_file()
            else:
                if os.path.exists(file):
                    self.write_stats_to_csv_file(file, no_data=True)
            t2 = time.time()
            print(f"Processing File: {os.path.basename(file)}. {current_file}/{total_files} files processed ({current_file/total_files*100:0.2f}%). Time taken: {t2-t1:0.2f} seconds.")

    def track_insects_one_file(self):
        """
        Track the insects in one CSV file
        """
        self.all_tracks = []
        process_noise = self.process_noise
        measurement_noise = self.measurement_noise
        distance_threshold = float(self.distance_threshold)
        max_frames_before_death = int(self.max_frames_before_death)
        kf = KalmanFilter(dim_x=4, dim_z=2)
        kf.F = np.array([[1, 0, 1, 0],
                        [0, 1, 0, 1],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
        kf.H = np.array([[1, 0, 0, 0],
                        [0, 1, 0, 0]])
        kf.P *= 1000
        kf.R = measurement_noise * np.eye(2)
        kf.Q = process_noise * np.array([[1, 0, 0, 0],
                                        [0, 1, 0, 0],
                                        [0, 0, 1, 0],
                                        [0, 0, 0, 1]])

        tracks = []
        all_tracks = []
        track_id = 0
        for frame in range(self.start_frame, self.end_frame + 1):
            observations = self.df[self.df['video_frame_id'] == frame][['center_x', 'center_y']].values

            # Predict step for all tracks
            for track in tracks:
                track['kf'].predict()
                track['last_seen'] += 1

            # Create cost matrix for assignment
            cost_matrix = np.zeros((len(tracks), len(observations)))
            for i, track in enumerate(tracks):
                for j, obs in enumerate(observations):
                    cost_matrix[i, j] = np.linalg.norm(track['kf'].x[:2] - obs)

            # Solve assignment problem using Hungarian algorithm
            track_indices, observation_indices = linear_sum_assignment(cost_matrix)

            # Update tracks with assigned observations
            assigned_tracks = set()
            assigned_observations = set()
            for i, j in zip(track_indices, observation_indices):
                if cost_matrix[i, j] < distance_threshold:
                    tracks[i]['kf'].update(observations[j])
                    tracks[i]['last_seen'] = 0
                    tracks[i]['positions'].append(observations[j])
                    tracks[i]['distance'] += cost_matrix[i, j]
                    tracks[i]['frame_ids'].append(frame)
                    assigned_tracks.add(i)
                    assigned_observations.add(j)

            # Create new tracks for unassigned observations
            for j in range(len(observations)):
                if j not in assigned_observations:
                    kf_new = KalmanFilter(dim_x=4, dim_z=2)
                    kf_new.F = kf.F
                    kf_new.H = kf.H
                    kf_new.P = kf.P
                    kf_new.R = kf.R
                    kf_new.Q = kf.Q
                    kf_new.x = np.array([observations[j][0], observations[j][1], 0, 0])
                    tracks.append({'kf': kf_new, 'id': track_id, 'last_seen': 0, 'positions': [observations[j]], 'distance': 0, 'frame_ids': [frame]})
                    track_id += 1

            # Remove tracks that have not been seen for a while
            tracks = [track for track in tracks if track['last_seen'] <= max_frames_before_death]

            for track in tracks:
                # check if the track is already in all_tracks. If not, add it
                if track['id'] not in [t['id'] for t in all_tracks]:
                    all_tracks.append(track)
        # remove tracks with less than 5 positions or distance less than 100
        all_tracks = [track for track in all_tracks if len(track['positions']) > 5 and track['distance'] > 100]
        # sort tracks based on the number of positions
        all_tracks = sorted(all_tracks, key=lambda x: len(x['positions']), reverse=True)
        self.all_tracks = all_tracks
        counter = {
            'inside': 0,
            'enter': 0,
            'exit': 0,
            'outside': 0
        }
        for track in all_tracks:
            track_direction = self.check_direction(track['positions'][0], track['positions'][-1], self.ellipse)
            counter[track_direction] += 1
        print(f"Inside: {counter['inside']}, Enter: {counter['enter']}, Exit: {counter['exit']}, Outside: {counter['outside']}")
        self.counter = counter

    def ellipse_quad(self, pos:tuple, ellipse:tuple) -> str:
        """
        Determine the quadrant of a point relative to an ellipse.
        :param pos: (x, y) coordinates of the point
        :param ellipse: ((h, k), (a, b), theta) ellipse parameters
        :return: Quadrant of the point relative to the ellipse. Options are "upper-left", "upper-right", "lower-left",
                    "lower-right", or "outside".
        """
        # Convert theta from degrees to radians
        x, y = pos
        h, k = ellipse[0]
        a, b = ellipse[1][0] / 2.0, ellipse[1][1] / 2.0  # semi-axes lengths
        theta = math.radians(ellipse[2])  # Convert rotation to radians for math functions

        # Translate point to origin based on ellipse center
        xp = x - h
        yp = y - k
        
        # Rotate point coordinates counter-clockwise to align with axis-aligned ellipse
        x_rot = xp * math.cos(-theta) - yp * math.sin(-theta)
        y_rot = xp * math.sin(-theta) + yp * math.cos(-theta)
        
        # Check using the standard ellipse equation
        inside_ellipse = (x_rot**2 / a**2) + (y_rot**2 / b**2) <= 1

        if inside_ellipse:
            if y_rot <= 0 and x_rot <= 0:
                return "upper-right"
            elif y_rot <= 0 and x_rot >= 0:
                return "lower-right"
            elif y_rot >= 0 and x_rot <= 0:
                return "upper-left"
            elif y_rot >= 0 and x_rot >= 0:
                return "lower-left"
        else:
            return "outside"

    def check_direction(self, start:tuple, end:tuple, ellipse:tuple) -> str:
        # Check if the start and end points are inside the ellipse top half
        start_quad = self.ellipse_quad(start, ellipse)
        end_quad = self.ellipse_quad(end, ellipse)

        def is_inside(quad):
            return quad == "upper-left" or quad == "upper-right"
        def is_outside(quad):
            return quad == "outside" or quad == "lower-left" or quad == "lower-right"

        start_inside = is_inside(start_quad)
        end_inside = is_inside(end_quad)
        
        if start_inside and end_inside:
            return 'inside'
        elif start_inside and not end_inside:
            return 'exit'
        elif not start_inside and end_inside:
            return 'enter'
        else:
            return 'outside'



if __name__ == "__main__":
    csv_folder='detected-bees'
    output_folder='tracking-results'
    ellipse_file='config/ellipses.txt'
    if not os.path.exists(csv_folder) or not os.path.isdir(csv_folder) or os.path.exists(ellipse_file):
        print("Error: detected bee csv folder or the ellipses text file not found. Exiting")
        exit(1)

    kf = KalmanFilterCLI(csv_folder=csv_folder, output_folder=output_folder, ellipse_file=ellipse_file)
    kf.track_insects()