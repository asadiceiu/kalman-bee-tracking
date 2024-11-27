import re


def get_ellipse(date:str):
    date = get_date_from_filename(date)
    file_path = 'config/date_ellipse.txt'
    with open(file_path, 'r') as f:
        lines = f.readlines()
        # print(lines)
        ellipses = eval(lines[0])
        return ellipses[date] if date in ellipses else None
    
    return None

def get_date_from_filename(filename:str)->str: 
    dates = re.findall(r'\d{8}', filename)
    if len(dates) == 0:
        print("Date not found in the file name.")
        return None
    return dates[0]

def get_time_from_filename(filename:str)->str: 
    times = re.findall(r'\d{6}', filename)
    if len(times) == 0:
        print("Time not found in the file name.")
        return None
    return times[0]