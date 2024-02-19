import csv

# Initialize lists to store data for each column
data_dict = {}

# Replace 'your_file.csv' with the path to your CSV file
with open('all_courses_combined.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    next(csv_reader)  # Skip the header row if it exists

    for row in csv_reader:
        title, course_code, section, index = row
        data_dict[index] = {
            'Title': title,
            'Course Code': course_code,
            'Section': section
        }

# Now, you have the data in separate lists
# You can print or manipulate them as needed