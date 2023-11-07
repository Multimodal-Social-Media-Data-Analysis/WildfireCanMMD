import csv
import requests
import os

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

def download_images(urls, ids, output_folder):
    downloaded_filepaths = []  # Initialize an empty list to store the file paths
    for i in range(len(urls)):  
        response = requests.get(urls[i])  # Send a GET request to the URL at index 'i'
        if response.status_code == 200:  # Check if the response status code is 200 (indicating a successful request)
            # Files will be named "(tweet id)_(unique url id).(jpg or png)"
            filename = ids[i] + '_' + urls[i].split('/')[-1]
            # Create the complete path for the image by joining the output folder path and the filename
            image_path = os.path.join(output_folder, filename)
            # Open the image file in binary write mode
            with open(image_path, 'wb') as file:
                file.write(response.content)  # Write the content of the response (image data) to the file
            # Append the downloaded image path to the list
            downloaded_filepaths.append(image_path)
            # Print the progress and the downloaded filename
            print(f"Downloaded and saved: {i}/{len(urls)-1} {filename}")
        else:
            # Print the progress and the URL that failed to download
            print(f"Failed to download: {i}/{len(urls)-1} {urls[i]}")
    return downloaded_filepaths  # Return the list of downloaded file paths

def main():
    csv_file = 'NS_wildfire_2023~10,017.csv'
    output_folder = 'NS_wildfire_2023~10,017(images)'

    urls, ids = extract_urls_from_csv(csv_file)
    download_images(urls, ids, output_folder)

if __name__ == "__main__":
    main()