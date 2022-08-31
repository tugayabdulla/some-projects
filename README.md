# some-projects

Here is collection of my selected projects. All of them are related to web-scraping/automation. Below is brief information about each one of them.

### dexscreen-ath

In this project I used selenium to get prices of tokens on ethereum blockchain. Dexscreener did not have public API and their private API was not suitable for large-scale scraping, so I had to use selenium. After scraping the bot checks the prices with past prices and if there is an increase, it shares it to Telegram channel.

### dextools

The purpose of this project was to trend tokens dextools in order to increase their popularity which would increase their price. I used selenium to replicate human behaviour: clicking different buttons, adding to favourites, sharing and many other things. In addition, I used proxies to fool the system and I used multithreading to have more interactions with the given token. And finally, we had 20 VPSs to even increase chances more. At the end we failed. Not because the script was not working, but because it was not possible to trend tokens this way.

### dextracker

This project is a telegram bot that uses dextools, graphql APIs and web3. It gets information about all past trades of a token, fetches price data, generates candlestick chart and does many other things. 

### generated-photos

https://generated.photos/faces - this website contains 2.7 million generated photos and I had to download them, then upload to pcloud. I used requests-html to parallelize the script and project took around 2 weeks to fully finish.

### reddit-scraper

Scraping information from reddit with PRAW and pushing to MongoDb database.

### routenote

Routenote is a platform for sharing music which have access to many other music sharing platforms. My client wanted to automate process of uploading music, adding metadata etc. I had to use selenium for all these things. Main highlights of this project are authentication, passing captcha, uploading files.
