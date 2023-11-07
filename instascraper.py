import instaloader
import pandas as pd

# List of hashtags to scrape
hashtags = ['BCwildfire', 'ABwildfire', 'NSwildfire']

# Create an instance of Instaloader
loader = instaloader.Instaloader()

# Create an empty list to store post data
post_data = []

# Iterate over each hashtag
for hashtag in hashtags:
    try:
        # Iterate over each post in the hashtag
        i = 0
        for post in loader.get_hashtag_posts(hashtag):
            # Access post information and append to post_data list
            post_data.append({
                'Post Shortcode': post.shortcode,
                'Post URL': post.url,
                'Post Caption': post.caption,
                'Post Date': post.date
                #'Post Location': post.location
            })
            if i == 500:
                break
            print(i)
            i+=1
    except:
        print(f"The hashtag '{hashtag}' was not found.")

# Create a pandas DataFrame from the post_data list
df = pd.DataFrame(post_data)

# Save DataFrame to a CSV file
df.to_csv('instagram_posts.csv', index=False)
