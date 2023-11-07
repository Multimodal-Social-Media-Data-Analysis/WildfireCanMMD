import os
import csv
import re
from datasets import Dataset
from datasets import load_from_disk
import IPython.display as display

def remove_links(text):
    # Remove links starting with 'https' or 'http'
    text_without_links = re.sub(r'https?\S+', '', text)
    return text_without_links

def get_filepaths(folder_path):
    filepaths = []
    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            filepath = os.path.join(folder_path, filename)
            filepath = filepath.replace('\\','/')
            filepaths.append(filepath)
    return filepaths

def create_database2(filepaths):
    data = {'text': [], 'image': []}
    matchctr = 1
    for filepath in filepaths:
        img_id = filepath.split('/')[1]
        img_id = int(img_id.split('_')[0])
        with open(csv_file, 'r', encoding='utf-8-sig') as file:  # Open the CSV file in read mode
            reader = csv.DictReader(file)  # Create a CSV reader object
            for row in reader:
                txt_id = int(row['tweet_id'])
                if img_id == txt_id:
                    print('match found' + ' : ' + str(img_id))
                    text = row['text']
                    text = remove_links(text)
                    data['text'].append(text)
                    data['image'].append(filepath)
                    print(matchctr)
                    matchctr += 1

    new_dataset = Dataset.from_dict(data)
    return new_dataset

csv_file = 'twitter_BC_AB_wildfires_apr-jun2023_5,478.csv'
folder_path = 'twitter_BC_AB_wildfires_apr-jun2023_5,478(images)'

# Create and save database
filepaths = get_filepaths(folder_path)
new_dataset = create_database2(filepaths)
new_dataset.save_to_disk('twitter_BC_AB_wildfires_apr-jun2023_5,478(dataset)')

# Load database from save and view the nth element
# loaded_dataset = load_from_disk('new_dataset')
# first_element = loaded_dataset[3]
# text = first_element['text']
# image = first_element['image']
# display.display(image)
# print(text)

# loaded_dataset = load_from_disk('new_dataset')
# text = loaded_dataset['text']
# image = loaded_dataset['image']
# yop = image[0]
# top = 0