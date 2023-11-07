from datasets import Dataset
from datasets import load_from_disk
import requests
import csv
import os
import re
from PIL import Image
from io import BytesIO
import base64
import IPython.display as display

def remove_links(text):
    # Remove links starting with 'https' or 'http'
    text_without_links = re.sub(r'https?\S+', '', text)
    return text_without_links

def image_base64(im):
    with BytesIO() as buffer:
        im.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()

def decode_base64_image(base64_string):
    image_data = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_data))

def extract_urls_from_csv(csv_file):
    urls = []  # Create an empty list to store URLs
    ids = []  # Create an empty list to store tweet IDs
    with open(csv_file, 'r', encoding='utf-8-sig') as file:  # Open the CSV file in read mode
        reader = csv.DictReader(file)  # Create a CSV reader object
        for row in reader:  # Iterate through each row in the CSV file
            url = row['url']  # Get the value of the 'url' column in the current row
            id = row['tweet_id']  # Get the value of the 'tweet_id' column in the current row
            if url != '':  # Check if the URL is not empty
                trimmed_url = url[1:]  # Remove the first character from the URL
                if "\t" in trimmed_url:  # Check if a tab character is present in the trimmed URL
                    split_url = trimmed_url.split("\t")  # Split the trimmed URL into multiple URLs at each tab character
                    urls.extend(split_url)  # Add the split URLs to the 'urls' list
                    for _ in range(len(split_url)):  # Repeat the following code for the number of split URLs
                        ids.append(id)  # Add the tweet ID to the 'ids' list
                else:
                    urls.append(trimmed_url)  # Add the trimmed URL to the 'urls' list
                    ids.append(id)  # Add the tweet ID to the 'ids' list
    return urls, ids  # Return the 'urls' list and the 'ids' list as a tuple

def create_database(csv_file):
    data = {'text': [], 'image': []}  # Create dictionaries to hold text and image data
    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        # line_count = 0
        urlctr = 1
        for row in reader:
            # if line_count >= 35:
            #     break  # Exit the loop after processing 35 lines
            # line_count += 1
            id = row['tweet_id']
            text = row['text']
            url_data = row['url']
            urls = []
            ids = []
            if text != '':
                text = remove_links(text)
                if url_data != '':
                    trimmed_url = url_data[1:]  # Remove the first character from the URL
                    if "\t" in trimmed_url:  # Check if a tab character is present in the trimmed URL
                        split_url = trimmed_url.split("\t")  # Split the trimmed URL into multiple URLs at each tab character
                        urls.extend(split_url)
                        for _ in range(len(split_url)):  # Repeat the following code for the number of split URLs
                            ids.append(id)  # Add the tweet ID to the 'ids' list
                    else:
                        urls.append(trimmed_url)
                        ids.append(id)
            for i in range(len(urls)):
                response = requests.get(urls[i])
                if response.status_code == 200:
                    image_data = BytesIO(response.content)
                    image = Image.open(image_data)
                    data['text'].append(text)
                    data['image'].append(image_base64(image))  # Encode image as base64 and append to the dictionary
                    print(str(urlctr) + "/" + str(len(URLS)))
                    urlctr += 1
                else:
                    print(f"Failed to download: {i}/{len(urls)-1} {urls[i]}")
    new_dataset = Dataset.from_dict(data)  # Create a new Dataset from the dictionary
    print("Text + image pairs created: " + str(len(new_dataset)))
    return new_dataset

URLS, IDS = extract_urls_from_csv('testing_5,478.csv')

# Create and save database
new_dataset = create_database('testing_5,478.csv')
new_dataset.save_to_disk('new_dataset')

# # Load database from save and view the nth element
# loaded_dataset = load_from_disk('new_dataset')
# first_element = loaded_dataset[0]
# text = first_element['text']
# image_base64 = first_element['image']
# image = decode_base64_image(image_base64)
# display.display(image)
# print(text)

# # Load database from save and view everything
# loaded_dataset = load_from_disk('new_dataset')
# display_width = 100
# display_height = 100
# for element in loaded_dataset:
#     text = element['text']
#     image_base64 = element['image']
#     image = decode_base64_image(image_base64)
#     image = image.resize((display_width, display_height))
#     print("------------------------------------------")
#     display.display(image)
#     print(text)