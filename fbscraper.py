from facebook_scraper import get_posts
from datetime import datetime, timedelta

# Hashtag and date range variables
hashtag = "wildfire"
start_date = datetime(2023, 1, 1)  # Replace with your desired start date
end_date = datetime(2023, 5, 5)  # Replace with your desired end date
pages_limit = 20  # Set the number of pages to scrape

# Iterate over the posts matching the hashtag and within the date range
for post in get_posts(hashtag, pages=pages_limit):
    if post['time'] < start_date:
        break

    if post['time'] <= end_date:
        print(f"Post ID: {post['post_id']}")
        print(f"Text: {post['text']}")
        print(f"Date: {post['time']}\n")
    else:
        continue
