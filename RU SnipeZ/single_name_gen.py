import csv
from bs4 import BeautifulSoup

# Function to extract class information from HTML
def extract_class_info(class_soup):
    course_name = class_soup.find('span', class_='courseTitle').text.strip()
    course_code = class_soup.find('span', id=lambda x: x and x.startswith("courseId")).text.strip()
    course_section = class_soup.find('span', class_='sectionDataNumber').text.strip()
    course_index = class_soup.find('span', class_='sectionIndexNumber').text.strip()
    return [course_name, course_code, course_section, course_index]

# Function to parse the HTML file and write to CSV
def parse_html_to_csv(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    class_elements = soup.find_all('div', class_='courseItem')

    with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Course Name', 'Index', 'Section'])

        for class_element in class_elements:
            class_info = extract_class_info(class_element)
            csv_writer.writerow(class_info)

# Input and output file paths
input_html_file = 'School_of_nursing_courses.html'  # Replace with your input HTML file
output_csv_file = 'School_of_nursing_courses_single.csv'  # Replace with the desired output CSV file

# Parse HTML and write to CSV
parse_html_to_csv(input_html_file, output_csv_file)
