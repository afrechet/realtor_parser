import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("googlemaps").setLevel(logging.WARNING)
import argparse
import csv

import googlemaps
GOOGLE_API_KEY = 'AIzaSyCFrPMdjROw0IeWBkldEgH_JGkjWjAknRI'
GMAPS_CLIENT = googlemaps.Client(key=GOOGLE_API_KEY)

import locale
locale.setlocale(locale.LC_ALL, '')

import duproprio_parser

class BuildingAddress(object):
	def __init__(self,number,street,city):
		self.number = number
		self.street = street
		self.city = city

	def __str__(self):
		return '%d %s, %s' % (self.number,self.street,self.city)

class RealEstate(object):
	def __init__(self,source,price,address,numrooms,storeys):
		self.source = source
		self.price = price
		self.address = address
		self.numrooms = numrooms
		self.storeys = storeys

	def __str__(self):
		return '%s at %s for %s (%d rooms, %d storeys)' % (self.source,str(self.address),locale.currency(self.price,grouping=True),self.numrooms,self.storeys)


METROS = {
		'Angrignon' : 'Angrignon Station, Montreal',
		'Monk':'Monk Station, Montreal',
		'Verdun': 'Verdun Station, Montreal',
		'Jolicoeur' : 'Jolicoeur Station, Montreal',
		"De l'Eglise" : "De l'Eglise Station, Montreal",
		'Lasalle' : 'Lasalle Station, Montreal',
		'Charlevoix' : 'Charlevoix Station, Montreal'
		 }
def getMetroDistances(real_estate):
	'''
	Return a dictionary taking (static) metro stations to the walking (distance,duration) pair in (km,min) from the given real estate.
	'''
	
	distances = {}
	for metro in METROS:
		directions = googlemaps.directions.directions(GMAPS_CLIENT,str(real_estate.address),METROS[metro],mode='walking',alternatives=False)
		legs = directions[0]['legs']
		distance = float(min([legs[i]['distance']['value'] for i in range(len(legs))]))/1000.0
		duration = min([legs[i]['duration']['value'] for i in range(len(legs))])/60
		distances[metro] = (distance,duration)

	return distances

def getBestMetroDistance(real_estate):
	distances = getMetroDistances(real_estate)
	best_metro = min(distances,key=lambda m: distances[m][0])
	return (best_metro,distances[best_metro][0],distances[best_metro][1])	

def main():

	parser = argparse.ArgumentParser(
		description=
		"""Real estate aggregator that gathers real estate information from a list of URL postings.""",
		epilog=
		"""by Alexandre Frechette (frechette.alex@gmail.com)"""
		)

	parser.add_argument('urls',help='the name of a file containing one real estate posting URL per row.')

	#Log level
	def parseLogLevel(loglevel):
		numeric_level = getattr(logging, loglevel.upper(), None)
		if not isinstance(numeric_level, int):
			raise ValueError('Invalid log level: %s' % loglevel)
		return numeric_level
	parser.add_argument('--log-level',
						dest = 'loglevel',
						type=parseLogLevel,
						default=logging.INFO,
						help='the level of logging to display (default: %(default)s)'
						)

	#Parse arguments
	args = parser.parse_args()

	logging.basicConfig(format='[%(levelname)s] %(message)s',level=args.loglevel)

	urls_filename =  args.urls

	logging.info('Gathering real estates ...')
	real_estates = []
	#Read the real estates.
	with open(urls_filename,'rb') as urls_file:
		for url in urls_file.readlines():
			url = url.strip()
			logging.info('Getting real estate at URL "%s" ...' % url)
			if 'duproprio' in url:
				real_estate = duproprio_parser.Parser(url).toRE()
			else:
				raise ValueError('Unrecognized realtor for URL "%s".' % url)

			real_estates.append(real_estate)

	logging.info('Calculating additional metrics ...')

	#Calculate the closest metro station for each real estate.
	metro_distances = {real_estate : getBestMetroDistance(real_estate) for real_estate in real_estates}
	
	#Write report
	report_filename = 'report.csv'
	logging.info('Writing report to "%s" ...' % report_filename)
	with open(report_filename,'wb') as report_file:
		writer = csv.writer(report_file)
		header = ['Source', 'Address', 'Price ($)', 'Rooms', 'Storeys', 'Closest Metro', 'Metro Distance (min)']
		writer.writerow(header)
		for real_estate in real_estates:
			row = [real_estate.source,str(real_estate.address),real_estate.price,real_estate.numrooms,real_estate.storeys,metro_distances[real_estate][0],metro_distances[real_estate][2]]
			writer.writerow(row)

	logging.info('...done!')

if __name__ == '__main__':
	main()		
		




