import requests
import tkinter as tk
import csv
from PIL import ImageTk, Image
from io import BytesIO
import os
from bs4 import BeautifulSoup
import tempfile

# Twitter:
CSV_PATH = 'twitter_BC_AB_wildfires_apr-jun2023_5,478.csv'
LABELED_PATH = '.labeled_twitter/'

# Instagram:
# CSV_PATH = 'instagram_wildfire_1153.csv'
# LABELED_PATH = '.labeled_instagram/'

INDEX_PATH = LABELED_PATH + 'index.txt'

def scrape_instagram_image(shortcode):
    # Construct the URL using the provided shortcode
    url = f"https://www.instagram.com/p/{shortcode}/"
    # Send an HTTP GET request to the URL
    response = requests.get(url)
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    # Find the image URL within the parsed HTML
    image_element = soup.find("meta", property="og:image")
    if image_element:
        image_url = image_element["content"]
        return image_url
    return None

def get_current_index():
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, 'r') as index_file:
            return int(index_file.read())
    else:
        return 0

def save_current_index(index):
    with open(INDEX_PATH, 'w') as index_file:
        index_file.write(str(index))

def loadIndex():
    current_index = get_current_index()
    for _ in range(current_index):
        next_row = next(csv_reader, None)  # Read the next row
    return next_row

def populate_data(row):
    global csv_reader, image_labels, text_label
    try:
        clear_images()
        urls = []

        # For Twitter:
        url_data = row['url']
        text = row['text']
        if url_data != '':  # Check if the URL is not empty
            trimmed_url = url_data[1:]  # Remove the first character from the URL
            if "\t" in trimmed_url:  # Check if a tab character is present in the trimmed URL
                split_url = trimmed_url.split("\t")  # Split the trimmed URL into multiple URLs at each tab character
                urls.extend(split_url)
            else:
                urls.append(trimmed_url)

        # For Instagram:
        # url_data = row['Post Shortcode']
        # text = row['Post Caption']
        # img_url = scrape_instagram_image(url_data)
        # urls.append(img_url)
        
        for i in range(len(image_labels)):
            if i < len(urls):
                response = requests.get(urls[i])
                image = Image.open(BytesIO(response.content))
                image = image.resize((300, 300))  # Adjust the size as needed
                photo = ImageTk.PhotoImage(image)
                image_labels[i].config(image=photo)
                image_labels[i].image = photo
            else:
                # Hide the image label if there are no more URLs
                image_labels[i].config(image=None)
        
        text_label.config(text=text)
    except StopIteration:
        print("End of CSV file")
        clear_images()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving image: {str(e)}")

def next_line():
    global next_row
    selected_action = selected_action_var.get()
    
    if selected_action == 1:
        # Perform action for radio button 1
        print("Informative")
        with open(LABELED_PATH+'informative.csv', 'a', newline='', encoding='utf-8-sig') as csv_file:
            writer = csv.writer(csv_file)
            if next_row is not None:
                writer.writerow([next_row[field] for field in csv_reader.fieldnames])
            new_index = get_current_index() + 1
            save_current_index(new_index)
            next_row = next(csv_reader, None)  # Read the next row
            if next_row is not None:
                populate_data(next_row)
            else:
                clear_images()
    elif selected_action == 2:
        # Perform action for radio button 2
        print("Non-Informative")
        with open(LABELED_PATH+'non-informative.csv', 'a', newline='', encoding='utf-8-sig') as csv_file:
            writer = csv.writer(csv_file)
            if next_row is not None:
                writer.writerow([next_row[field] for field in csv_reader.fieldnames])
            new_index = get_current_index() + 1
            save_current_index(new_index)
            next_row = next(csv_reader, None)  # Read the next row
            if next_row is not None:
                populate_data(next_row)
            else:
                clear_images()

def clear_images():
    for image_label in image_labels:
        image_label.config(image=None)
        image_label.image = None

# Create tkinter window
window = tk.Tk()
image_frame = tk.Frame(window)
image_frame.pack()

# Create image labels
image_labels = []
for i in range(4):  
    image_label = tk.Label(image_frame)
    image_label.grid(row=0, column=i, padx=10)  # Use grid layout manager
    image_labels.append(image_label)

# Create text space
text_label = tk.Label(window, wraplength=300) 
text_label.pack()

# Create radio buttons
selected_action_var = tk.IntVar()
radio_button1 = tk.Radiobutton(window, text="Informative", variable=selected_action_var, value=1)
radio_button1.pack()
radio_button2 = tk.Radiobutton(window, text="Non-Informative", variable=selected_action_var, value=2)
radio_button2.pack()

# Create 'Next' button
next_button = tk.Button(window, text="Next", command=next_line)
next_button.pack()

# # Start reading from the csv
csv_file = open(CSV_PATH, 'r', encoding='utf-8-sig')
csv_reader = csv.DictReader(csv_file)
# Start reading from the csv
# csv_file = open(CSV_PATH, 'r', encoding='utf-8-sig')
# csv_reader = csv.DictReader(csv_file)
# # Create a temporary file to store the modified CSV data
# temp_csv_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
# # Check if the 'newcolumn' header already exists
# if 'newcolumn' not in csv_reader.fieldnames:
#     # Create a new header row with 'newcolumn'
#     header = csv_reader.fieldnames + ['newcolumn']
#     writer = csv.DictWriter(temp_csv_file, fieldnames=header)
#     writer.writeheader()
# else:
#     # Copy the existing header row to the temporary file
#     temp_csv_file.write(','.join(csv_reader.fieldnames) + '\n')
# # Copy the remaining rows from the original CSV to the temporary file
# for row in csv_reader:
#     temp_csv_file.write(','.join(row.values()) + '\n')
# # Close the original CSV file
# csv_file.close()
# # Close the temporary file and rename it to the original CSV file path
# temp_csv_file.close()
# os.replace(temp_csv_file.name, CSV_PATH)
# # Reopen the modified CSV file for reading
# csv_file = open(CSV_PATH, 'r', encoding='utf-8-sig')
# csv_reader = csv.DictReader(csv_file)

# Populate the initial data
next_row = loadIndex()
if next_row is not None:
    populate_data(next_row)
else:
    clear_images()

# Start the tkinter event loop
window.mainloop()
