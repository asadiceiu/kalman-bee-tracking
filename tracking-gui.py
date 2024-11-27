import os
import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import re
import pprint

def format_time(time:str|None)->str|None:
    """
    Format time from 24-hour format to 12-hour format with 10-minute interval and AM/PM suffix (e.g. 06:00 AM).
    param time: str - Time in 24-hour format (e.g. 060300 for 6:00 AM)
    return: str - Time in 12-hour format with 10-minute interval (e.g. 6:00 AM)
    """
    if time is None:
        return None
    hour = int(time[:2])
    minute = int(time[2:4])
    minute_10_interval = round(minute/10)*10 # Round down to nearest 10. E.g. 13 -> 10, 17 -> 20
    ampm = 'AM' if hour < 12 else 'PM'
    hour = hour % 12 if hour % 12 != 0 else 12 # Convert 24-hour to 12-hour format and set 0 to 12 for 12-hour format
    return f"{hour}:{minute_10_interval:02d} {ampm}"

# Function to parse the text file and extract tracking data
def parse_tracking_data(filepath:str)->dict:
    """
    Parse the tracking data from the text file and return a dictionary with date and time as keys and tracking data as values.
    param filepath: str - Path to the text file containing tracking data
    return: dict - Dictionary with date and time as keys and tracking data as values
    """
    tracking_data = {}
    with open(filepath, 'r') as file:
        lines = file.readlines()
        current_date = None
        current_time = None
        current_data = {}

        for line in lines:
            # Identify CSV file lines with date and time
            if "CSV File" in line:
                filename_match = re.search(r'CSV File: (\d{8})_(\d{6})\.csv', line)
                if filename_match:
                    if "No Data Found" not in line:
                        current_date, current_time = filename_match.group(1), filename_match.group(2)
                        current_data = {
                            'Total Tracks': None,
                            'Enter': None,
                            'Exit': None,
                            'Inside': None,
                            'Outside': None
                        }
                    else:
                        current_date = None
                        current_time = None

            # Extract Total Tracks
            if "Total Tracks:" in line and current_date and current_time:
                match = re.search(r'Total Tracks: (\d+)', line)
                if match:
                    current_data['Total Tracks'] = int(match.group(1))

            # Extract Enter, Exit, Inside, Outside values
            if all(value is None for value in current_data.values()) == False:
                enter_match = re.search(r'Enter: (\d+)', line)
                exit_match = re.search(r'Exit: (\d+)', line)
                inside_match = re.search(r'Inside: (\d+)', line)
                outside_match = re.search(r'Outside: (\d+)', line)

                if enter_match:
                    current_data['Enter'] = int(enter_match.group(1))
                if exit_match:
                    current_data['Exit'] = int(exit_match.group(1))
                if inside_match:
                    current_data['Inside'] = int(inside_match.group(1))
                if outside_match:
                    current_data['Outside'] = int(outside_match.group(1))

            # Add to tracking data when all fields are filled
            if all(value is not None for value in current_data.values()):
                if current_date not in tracking_data:
                    tracking_data[current_date] = {}
                tracking_data[current_date][format_time(current_time)] = current_data.copy()

    return tracking_data

# GUI for selecting date and displaying the graph
class TrackingDataGUI:
    """
    GUI for selecting date and displaying the graph for tracking data.
    param root: tk.Tk - Root window for the GUI
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Tracking Data Viewer")

        self.data = {}

        # Load File Button
        self.load_button = ttk.Button(root, text="Load Data File", command=self.load_data)
        self.load_button.pack(pady=10)

        # Date Selection
        self.date_label = ttk.Label(root, text="Select Date:")
        self.date_label.pack()
        self.date_combobox = ttk.Combobox(root, state="readonly")
        self.date_combobox.pack(pady=5)
        self.date_combobox.bind("<<ComboboxSelected>>", self.date_selected)

        # Plot Button
        self.plot_button = ttk.Button(root, text="Plot Data", command=self.plot_data)
        self.plot_button.pack(pady=10)

        # Figure for plotting
        self.figure = plt.Figure(figsize=(10, 6))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas.get_tk_widget().pack(pady=10)

        # Status Bar
        self.status_bar = ttk.Label(root, text="Status: Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    def load_data(self):
        """
        Load tracking data from a text file and populate the date combobox.
        """
        filepath = filedialog.askopenfilename(title="Select Tracking Data File", filetypes=[("Text Files", "*.txt")])
        if filepath:
            self.data = parse_tracking_data(filepath)
            self.date_combobox["values"] = list(self.data.keys())
            self.status_bar.config(text="Status: Data file loaded")

    def date_selected(self, event):
        """
        Event handler for date selection from the combobox.
        param event: tk.Event - Event object
        """
        selected_date = self.date_combobox.get()
        if selected_date:
            self.status_bar.config(text=f"Status: Date selected - {selected_date}")

    def plot_data(self):
        """
        Plot the tracking data for the selected date.
        """
        selected_date = self.date_combobox.get()
        if selected_date:
            if selected_date not in self.data:
                self.status_bar.config(text=f"Status: No data found for date {selected_date}")
                return

            # Define time range from 6 AM to 8 PM with 10-minute intervals
            all_times = [format_time(f"{hour:02d}{minute:02d}00") for hour in range(6, 21) for minute in range(0, 60, 10)]

            # Prepare data with default values as 0
            total_tracks = []
            enters = []
            exits = []
            inside = []
            outside = []

            plot_times = []
            start_time = format_time("060000")
            end_time = format_time("200000")
            for time in all_times:
                if time in self.data[selected_date]:
                    total_tracks.append(self.data[selected_date][time]['Total Tracks'])
                    enters.append(self.data[selected_date][time]['Enter'])
                    exits.append(self.data[selected_date][time]['Exit'])
                    inside.append(self.data[selected_date][time]['Inside'])
                    outside.append(self.data[selected_date][time]['Outside'])
                    plot_times.append(time)
                
            if start_time not in plot_times: # Add start time data if not present for showing 0 tracks at the start
                plot_times.insert(0, start_time)
                total_tracks.insert(0, 0)
                enters.insert(0, 0)
                exits.insert(0, 0)
                inside.insert(0, 0)
                outside.insert(0, 0)
            
            if end_time not in plot_times: # Add end time data if not present for showing 0 tracks at the end
                plot_times.append(end_time)
                total_tracks.append(0)
                enters.append(0)
                exits.append(0)
                inside.append(0)
                outside.append(0)


            # Clear previous plot
            self.ax.clear()

            # Plot new data
            self.ax.plot(plot_times, enters, label='Enter')
            self.ax.plot(plot_times, exits, label='Exit')
            # you can add more lines here for other data like 'Inside', 'Outside', etc.

            #TODO: Add temperature data to the plot here

            self.ax.set_xlabel('Time (6AM - 8PM)')
            self.ax.set_ylabel('Number of Tracks')
            self.ax.set_title(f'Tracking Data for {selected_date}')
            self.ax.legend()
            self.ax.tick_params(axis='x', rotation=45)

            # Draw the updated plot
            self.canvas.draw()
            self.status_bar.config(text=f"Status: Data plotted for {selected_date}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TrackingDataGUI(root)
    root.mainloop()