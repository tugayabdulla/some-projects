import json
import time

import praw
from pymongo import MongoClient


class RedditScraper:
    def __init__(self, subreddit: str = 'all', time_filter: str = 'hour', n_posts: int = 100,
                 refresh_rate: int = 60 * 30) -> None:
        """
        Initialize the scraper.

        :param subreddit: The subreddit to scrape.
        :param time_filter: The time filter to use. One of: "day", "hour", "month", "week", "year".
        :param n_posts: The number of posts to fetch.
        :param refresh_rate: The number of seconds to wait between fetching posts.
        """
        try:
            with open('credentials.json') as f:
                creds = json.load(f)
                self.reddit = praw.Reddit(client_id=creds['client_id'],
                                          client_secret=creds['client_secret'],
                                          user_agent='bot by ' + creds['username'],
                                          username=creds['username'],
                                          password=creds['password'])
                self.client = MongoClient(creds['mongo_string'])
                print(self.client.server_info())

        except Exception as e:
            print(e)
            raise Exception(
                'Credentials file not found. Please create a file called credentials.json with the following '
                'contents:\nclient_id, client_secret, username, password')

        self.refresh_rate = refresh_rate
        self.subreddit = subreddit
        self.time_filter = time_filter
        self.n_posts = n_posts
        self.new = True

    def _fetch_last_insert_time(self) -> int:
        """
        Fetch the last time the data was inserted or 0 if it is the first time.

        :return: The last time the data was inserted.
        """
        time_db = self.client['time']
        res = time_db.posts.find_one({'platform': 'reddit'})
        if res is None: return 0
        return res['time']

    def update_time(self) -> None:
        """
        Updates the insert time in the database.
        """

        time_db = self.client['time']
        new_values = {'$set': {'time': int(time.time())}}
        time_db.posts.update_one({'platform': 'reddit'}, new_values, upsert=True)

    def _get_top_posts(self) -> praw.models.ListingGenerator:
        """
        :return: A generator of top posts from the subreddit.
        """

        subreddit = self.reddit.subreddit(self.subreddit)
        return subreddit.top(limit=self.n_posts, time_filter=self.time_filter)

    def save_posts(self, posts) -> None:
        """
        Inserts the posts into the database.

        :param posts: A generator of posts.
        """
        posts_db = self.client['reddit']
        data = []
        scrape_time = int(time.time())

        for post in posts:
            post_dict = {'title': post.title,
                         'subreddit': post.subreddit.display_name,
                         'author': post.author.name,
                         'num_comments': post.num_comments,
                         'scrape_time': scrape_time,
                         'ups': post.ups,
                         'downs': post.downs,
                         'score': post.score,
                         'post_id': post.id,
                         'permalink': post.permalink
                         }
            data.append(post_dict)

        posts_db.posts.insert_many(data)

    def close_connection(self) -> None:
        """Closes connection"""
        self.client.close()

    def do_process(self) -> None:
        """
        Main logic happens here. Basically, it fetches the posts, updates the time and saves them.
        """
        if self.new:
            last_time = self._fetch_last_insert_time()
            diff = time.time() - last_time
            if diff < self.refresh_rate:
                time.sleep(self.refresh_rate - diff)
            self.new = False

        while True:
            start_time = time.time()

            top_posts = self._get_top_posts()
            self.save_posts(top_posts)
            self.update_time()

            time.sleep(self.refresh_rate - (time.time() - start_time))


scraper = RedditScraper(time_filter='week')

while True:
    try:
        scraper.do_process()
    except Exception as e:
        print(e)
        scraper.close_connection()
        scraper = RedditScraper()
