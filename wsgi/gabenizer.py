import time
import praw
import unirest
import urllib, cStringIO
from urlparse import urlparse
from pprint import pprint
from PIL import Image
from config import SUBREDDIT, SKYBIO_ID, SKYBIO_SECRET

r = praw.Reddit('gabenizer bot')
#r.login()
already_done = []

#while True:

submissions = r.get_subreddit(SUBREDDIT).get_hot(limit=10)

for pic in submissions:
	#get only
	url = ''
	parsed_url = urlparse(vars(pic)['url'])
	if parsed_url.netloc == 'imgur.com':
		#is album or framed page
		if parsed_url.path.split('/')[1]=='a':
			#is album, skip
			continue
		else:
			url = parsed_url.geturl()+'.jpg'
	elif parsed_url.netloc == 'i.imgur.com':
		#is image file
		url = parsed_url.geturl()
	print url
	
	if url in already_done:
		continue
	already_done.append(url)
	
	if url == '':
		continue

	#detect face, get x,y
	response = unirest.get('http://api.skybiometry.com/fc/faces/detect.json'
			+'?api_key='+SKYBIO_ID
			+'&api_secret='+SKYBIO_SECRET
			+'&detector=aggressive'
			+'&attributes=none'
			+'&urls='+url)
	pprint(vars(response))

	photos = response.body['photos']
	for photo in photos:
		try:
			original = Image.open(cStringIO.StringIO(urllib.urlopen(url).read()))
			gabenized = original.copy()
			if not photo['tags']:
				continue
			for face in photo['tags']:
				#get image values
				original_roll = face['roll']
				original_center_x = face['center']['x']
				original_center_y = face['center']['y']
				original_size = face['width']
				original_height = photo['height']
				original_width = photo['width']

				#hardcoded values for gaben
				#gaben_roll = -1
				#gaben_center_x = 47.02
				#gaben_center_y = 59.28
				#gaben_size = 51.76
				#gaben_height = 663
				#gaben_width = 655

				#hardcoded values for gabenface
				gaben_roll = -1
				gaben_center_x = 51.24
				gaben_center_y = 47.53
				gaben_size = 67.15
				gaben_height = 465
				gaben_width = 484

				#calculate values for scale and position
				scale = (original_size * original_width) / (gaben_size * gaben_width)
				scale_height = gaben_height * scale
				scale_width = gaben_width * scale
				place_x = (0.01 * original_center_x * original_width) - (0.01 * gaben_center_x * scale_width)
				place_y = (0.01 * original_center_y * original_height) - (0.01 * gaben_center_y * scale_height)

				print scale
				print scale_height
				print scale_width
				print place_x
				print place_y

				#open image
				gaben = Image.open('gabenface.png')

				#rotate gaben to match roll
				gaben = gaben.rotate(int(-1*original_roll))

				#resize gaben
				gaben = gaben.resize((int(scale_width), int(scale_height)))

				gabenized.paste(gaben, (int(place_x), int(place_y)), gaben)

			final = Image.new("RGB", (original_width * 2, original_height))
			final.paste(original, (0,0))
			final.paste(gabenized, (original_width, 0))

			final.save(str(time.time())+'gabenized.png')
		except:
			continue

