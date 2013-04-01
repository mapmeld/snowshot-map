import cgi, logging, email, sys, StringIO, urllib, base64
import webapp2
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext import db
from google.appengine.api.urlfetch import fetch, GET, POST
import json
from google.appengine.api import images, memcache

import json
import photo_service
#from photo_service import * as gdataphotos.service.*
import gdata_media
import gdata_geo

picasa_settings = {
  "email": "YOU@example.com",
  "password": "PASSWORD",
  "source": "http://appid.appspot.com"
}
imgur_key = ""

#import geotypes, geomath
class MainPage(webapp2.RequestHandler):
  def get(self):
	# apikey = "ABQIAAAAxkKtrWN5q-vPTLRVmO_r6RQZOg9yfWRQlOix4bVr4QZuCc-wbRTRkb3UdZVhgGDMeYXzIhZAMwVTMg"
	self.response.out.write('''<!DOCTYPE html> 
<html> 
	<head>
		<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
		<title>Sample Snowshot Map</title>
		<script type="text/javascript" src="https://maps.googleapis.com/maps/api/js?v=3.exp&sensor=false"></script>
		<script type='text/javascript'>
			var main_map;

			function init(){
				var lat=37.0625;
				var lng=-95.677068;
				var zoom=4;
				main_map = new google.maps.Map(document.getElementById("map_canvas"), {
				  zoom: zoom,
				  center: new google.maps.LatLng( lat, lng ),
				  mapTypeId: google.maps.MapTypeId.ROADMAP
				});

				var kml = new google.maps.KmlLayer("http://snowshot-map.appspot.com/snowshot-kml-edit.kml", { map: main_map, preserveViewport: true });
			}
		</script>
		<style type="text/css">
html, body{
  font-family: verdana, sans-serif;
  padding: 20px;
}
		</style>
	</head>
	<body onload="init()">
		<div id="map_canvas" style="width:850px;height:550px;">
			Map didn't load
		</div>
		<a href="http://snowshot-map.appspot.com/snowshot-kml.kml" type="application/vnd.google-earth.kml+xml">Map for Google Earth</a><br/>
		Geocoding from <a href="http://worldkit.org">Worldkit</a> and <a href="http://geoapi.com">GeoAPI</a>.
	</body>
</html>''')

class KMLout(webapp2.RequestHandler):
  def get(self):
	self.response.headers['Content-Type'] = "application/vnd.google-earth.kml+xml"
	kml = memcache.get("kml")
	if kml is not None:
		self.response.out.write(kml)
		return
	outKML = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
	<Document>
		<name>SnowShot of America</name>
		<Style id="snowflake">
			<IconStyle>
				<Icon>
					<href>http://maps.google.com/mapfiles/kml/shapes/snowflake_simple.png</href>
				</Icon>
			</IconStyle>
		</Style>\n'''
	points = SnowShot.gql('ORDER BY uploaded LIMIT 1000')
	for p in points:
		outKML = outKML + '		<Placemark>\n'
		imgEntry = ""
		for photo in p.photos:
			if(photo != ""):
				if(photo.find('.') == -1):
					# stored on App Engine, from attachments
					imgEntry = imgEntry + "<br/><img src=\"http://snowshot-map.appspot.com/snowshot-pic?id=" + photo + "\" style=\"max-width:400px;max-height:250px;height:240px;\"/>"
				else:
					# on other site (such as Picasa, Flickr)
					imgEntry = imgEntry + "<br/><img src=\"" + photo + "\" style=\"max-width:400px;max-height:250px;height:240px;\"/>"
		if(imgEntry.find('img') == -1):
			#if(self.request.get('edit') == 'true'):
			#latlng = str(p.latlng).split(',')
			#imgEntry = '''<form action="MAILTO:snowshotofamerica.snowshot@picasaweb.com" method="post">
			#	<input name="text" value="''' + latlng[1]+","+latlng[0] + '''"/>
			#	<input type="file" name="attachPhoto"/>
			#	<input type="submit" value="Send"/>
			#</form>'''
			#else:
			imgEntry = "No Image"
		latlng = str(p.latlng).split(',')
		outKML = outKML + '''
			<styleUrl>#snowflake</styleUrl>
			<description>
				''' + cgi.escape("<div style=\"width:450px;height:300px;\">" + (p.content + imgEntry).replace("\n","<br/>") + "</div>") + '''
			</description>
			<Point>
				<coordinates>''' + latlng[1]+","+latlng[0] + ''',0</coordinates>
			</Point>
		</Placemark>\n'''
	outKML = outKML + '	</Document>\n</kml>'
	self.response.out.write(outKML)
	memcache.add("kml", outKML, 24000)  # 6+ hour cache
	memcache.add("kml", outKML, 600)  # 10 minute cache

class Picout(webapp2.RequestHandler):
  def get(self):
	self.response.headers['Content-Type'] = "image/jpeg"
	upload = SnowPic.get_by_id(long(self.request.get('id')))
	self.response.out.write(upload.photo)

class SnowReport(InboundMailHandler):
  def receive(self, message):
#   try:
	location = cgi.escape(message.subject.replace('Fwd:','').replace('[','').replace(' ','').replace(']',''))
	#logging.info("Received a SnowReport in: " + message.subject)
	if(location.lower().find("latlon:") != -1):
		# get lat,lng directly from subject
		latlng = location.lower().replace("ll:","").split(",")
		lat = latlng[0]
		lng = latlng[1]
	elif(location.lower().find("lonlat:") != -1):
		# get lat,lng directly from subject
		latlng = location.lower().replace("lonlat:","").split(",")
		lat = latlng[1]
		lng = latlng[0]
	else:
		geocode = fetch("http://worldkit.org/geocoder/rest/?city=" + location + ",US", payload=None, method=GET, headers={}, allow_truncated=False, follow_redirects=True).content.split('\n')
		if((geocode[0].find('<!DOCTYPE') != -1) or (geocode[0].find('Please specify') != -1)):
			# worldkit geocode failed, try geoapi
			geocode = fetch("http://api.geoapi.com/v1/keyword-search?apikey=qrIpdnriYy&q=" + location + "&limit=1", payload=None, method=GET, headers={}, allow_truncated=False, follow_redirects=True).content
			if(geocode.find('"num-results": 0') != -1):
				# geoapi geocode failed
				logging.info('Could not find: ' + location)
				return
			else:
				# use json reader from http://code.google.com/p/pygeoapi/
				ioObject = json.read(geocode)
				try:
					lng = str(ioObject['result'][0]['meta']['geom']['coordinates'][0][0][0][0])
					lat = str(ioObject['result'][0]['meta']['geom']['coordinates'][0][0][0][1])
				except:
					# some have a slightly different format
					lng = str(ioObject['result'][0]['meta']['geom']['coordinates'][0][0][0])
					lat = str(ioObject['result'][0]['meta']['geom']['coordinates'][0][0][1])
		else:
			# worldkit geocode success
			lng = geocode[2]
			lng = lng[lng.find('<geo:long>')+10:lng.find('</geo:long>')]
			lat = geocode[3]
			lat = lat[lat.find('<geo:lat>')+9:lat.find('</geo:lat>')]

	#logging.info("position at " + lat + "," + lng)
	email_bodies = message.bodies('text/plain')
	if(message.body.encoding == '8bit'):
		message.body.encoding = '7bit'
	msgContent = message.body.decode()
	fallbackLink = ""
	if((msgContent.lower().find('.png') > 1) and (msgContent.lower().find('.png') < msgContent.find('\n'))):
		fallbackLink = msgContent[0:msgContent.find('\n')]
	if((msgContent.lower().find('.jpg') > 1) and (msgContent.lower().find('.jpg') < msgContent.find('\n'))):
		fallbackLink = msgContent[0:msgContent.find('\n')]
	#for content_type, body in email_bodies:
		#if(content_type == 'text/html'):
		#msgContent = body.decode()
	#	msgContent = body
		#else:
		#	msgContent = body
	attachments = []
	newpt = ""
	try:
		if(len(message.attachments) > 0):
			#logging.info('has attachments')
			if isinstance(message.attachments[0], basestring):
				attachments = [message.attachments]
			else:
				attachments = message.attachments
			newpt = SnowShot(latlng=db.GeoPt(lat,lng),
				content=msgContent,
				photos=[])
			# sign into Google / Picasa
			gd_client = photo_service.PhotosService()
			gd_client.email = picasa_settings["email"]
			gd_client.password = picasa_settings["password"]
			gd_client.source = picasa_settings["source"]
			gd_client.ProgrammaticLogin()
			
			# add each attachment
			for filename, content in attachments:
				if((filename.lower().find('.png') != -1) or (filename.lower().find('.jpg') != -1)):
					# store and attach this photo
					if(filename.lower().find('.jpg') != -1):
						photo_type = 'image/jpeg'
					else:
						photo_type = 'image/png'
					if(content.encoding == '8bit'):
						content.encoding = '7bit'
					imgData = str(content.decode())
					try:
						try:
							# shrink photo 0.7 x 0.7 size
							img = images.Image(image_data=imgData)
							img.resize(width=int(0.7*img.width),height=int(0.7*img.height))
							imgData = img.execute_transforms(output_encoding=images.JPEG)						
							# upload the photo to Picasa
							picasaPhoto = gd_client.InsertPhotoSimple('/data/feed/api/user/default/albumid/default',"Snowshot from " + location,'Uploaded using the API', StringIO.StringIO(imgData), content_type=photo_type)
							picasaPhotoLink = picasaPhoto.content.src
							newpt.photos.append(picasaPhotoLink)
						except Exception, e:
							# could not sign into Picasa, or this photo wouldn't upload
							# store it locally, for now
							pic = SnowPic(photo=db.Blob(imgData))
							pic.put()
							newpt.photos.append(str(pic.key().id()))
							# try imgur API
							#uploadResult = self.upload(str(content.decode()))
							#newpt.photos.append("http://imgur.com/" + uploadResult.image_hash + ".jpg")

					except Exception, e:
						logging.info(e)
						logging.info("pic from " + location + " failed to store locally")
						
			newpt.put()
			return
		else:
			# no attachments, force exception, making this a text marker
			alphabet = x
	except Exception, e:
		# there are no attachments
		# essentially this marker has no photos to put on it, unless the first line was a link (fallbackLink)
		# log any errors, then put a text marker
		logging.info(e)
		logging.info("Photo from " + location + " failed")
		newpt = SnowShot()
		newpt.latlng=db.GeoPt(lat,lng)
		newpt.photos=[fallbackLink]
		if(fallbackLink != ""):
			# first line is the photo to embed
			msgContent = msgContent[msgContent.find('\n'):len(msgContent)]
		newpt.content=msgContent
		newpt.put()

  def upload(self, imgdata):
	payload_data=urllib.urlencode({"key":imgur_key, "image":base64.b64encode(imgdata)})
	s = fetch("http://imgur.com/api/upload.json", method=POST, payload=payload_data)
	data = json.loads(s.content)
	return data

class SnowShot(db.Model):
	latlng = db.GeoPtProperty()
	content = db.TextProperty()
	photos = db.StringListProperty()
	uploaded = db.DateTimeProperty(auto_now_add=True)

class SnowPic(db.Model):
	photo = db.BlobProperty()

app = webapp2.WSGIApplication([('/snowshot-kml.*',KMLout),
									('/snowshot-pic.*',Picout),
									SnowReport.mapping(),
									('/.*',MainPage)],
                                     debug=True)