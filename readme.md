# Snowshot-Map

## What it is

### Build a photo map by e-mail

Send photos to an e-mail address on your AppEngine instance

* The e-mail subject ("Fwd: Boston, MA") is geocoded to a latitude and longitude

* Any photos in the message body or attachments are uploaded as a blob or sent to Imgur.

* The resulting map can be viewed on AppEngine, embedded using Google Maps, and downloaded to Google Earth.

<img src="http://i.imgur.com/lo8cQRA.png"/>

## The Origin Story

In February 2010, a dusting of snow in Florida and the upper slopes of the big island of
Hawai'i put meteorology into the news. For the first time in memory, there was
<a href="http://www.npr.org/templates/story/story.php?storyId=123659376">snow in all
50 states</a>.

Patrick Marsh decided to collect snow photos from all of the states. He got thousands.

I wrote to Patrick about making a Google Maps mash-up / Google Earth KML of all of these
photos.

In 2013, I'm updating all of my apps (including snowshot-map) from Google
AppEngine to Python 2.7 and the High-Replication Datastore. I also updated to Google Maps
API v3.

I decided to open-source snowshot-map because it's a unique process to make a crowdsourced
map.

## Install

* Install Google AppEngine on your local machine, and create an account.

* Change picasa_settings and imgur_key at the top of snowshot.py

* Run appcfg.py update APP_NAME

* E-mail photos to your app

## License

MIT license
