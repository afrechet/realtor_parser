from lxml import html
import requests
import logging
import realtor_parser

class Parser(object):

	@staticmethod
	def _parseName(tree):
		name = tree.xpath('//*[@id="listingContent"]/h1/text()')[-1]
		if not name:
			raise ValueError('Could not parse name.')		
		return name.strip()


	@staticmethod
	def _parseAddress(tree):
		address = tree.xpath('//*[@id="details"]/div[2]/p/strong/span[1]/text()')[0]
		if not address:
			raise ValueError('Could not parse address.')
		return address.strip()

	@staticmethod
	def _parseProperty(tree):
		keyvalues = {}
		for ul in range(10):
			for li in range(10):
				key = tree.xpath('//*[@id="details"]/div[2]/div[1]/ul[%d]/li[%d]/strong/text()' % (ul,li))
				value = tree.xpath('//*[@id="details"]/div[2]/div[1]/ul[%d]/li[%d]/text()' % (ul,li))
	
				if key and value:
					
					if len(key) > 1:
						raise ValueError('Unexpected property features key "%s".' % str(key))
					key = key[0]
					if len(value) > 1:
						raise ValueError('Unexpected property features value "%s".' % str(value))
					value = value[0]

					try:
						keyvalues[key] = value
					except Exception as e:
						logging.error('Could not parse property features key-value pair "%s" and "%s".' % (str(key),str(value)))
						raise e
		return keyvalues

	@staticmethod
	def _parseRooms(tree):
		keyvalues = {}
		header = {}
		for th in range(1,20):
			key = tree.xpath('//*[@id="dimensions"]/div[2]/table/tr[1]/th[%d]/text()' % th)
			if key:
				if len(key) > 1:
					raise ValueError('Unexpected room features header key "%s".' % str(key))
				key = key[0]
				header[th] = key

		for tr in range(20):
			key = tree.xpath('//*[@id="dimensions"]/div[2]/table/tr[%d]/td[%d]/strong/text()' % (tr,1))
			if key:
				if len(key) > 1:
					raise ValueError('Unexpected room features key "%s".' % str(key))
				key = key[0]
				keyvalues[key] = {}
				for td in range(1,20):
					value = tree.xpath('//*[@id="dimensions"]/div[2]/table/tr[%d]/td[%d]/text()' % (tr,td))
					if value:
						if len(value) > 1:
							raise ValueError('Unexpected room features value "%s".' % str(value))
						value = value[0]
						if td not in header:
							raise ValueError('No header name for %d-th column with value "%s".' % (td,value))
						try:
							keyvalues[key][header[td]] = value
						except Exception as e:
							logging.error('Could not parse room features key-value pair "%s" and "%s".' % (str(key),str(value)))
							raise e
		return keyvalues

	def __init__(self,url):
		logging.info('Getting DuProprio webpage at "%s" ...' % url)
		page = requests.get(url)
		tree = html.fromstring(page.text)

		logging.info('Parsing webpage for relevant information ...')

		self.url = url

		#Parse name and address
		self.name = Parser._parseName(tree)
		self.address = Parser._parseAddress(tree)

		#Parse property features.
		self.property = Parser._parseProperty(tree)
		
		#Parse room features
		self.rooms = Parser._parseRooms(tree)

		logging.info('...done!')

	def __str__(self):
		return '%s (%s) at %s\n%s\n%s' % (self.name,self.url,self.address,str(self.property),str(self.rooms))

	def toRE(self):
		address = realtor_parser.BuildingAddress(int(self.address.split(',')[0].strip()),self.address.split(',')[1].strip(),'Montreal')

		price = float(self.property['Asking Price :'].replace('$','').replace(',','').strip())
		
		if 'Total number of rooms :' in self.property:
			numrooms = int(self.property['Total number of rooms :'].strip())
		else:
			numrooms = int(self.property.get('Number of bedrooms :',0)) + int(self.property.get('Number of bathrooms :',0)) + int(self.property.get('Number of half baths :',0))

		storeys = int(self.property['Number of levels (basement excl.) :'].strip())
		real_estate = realtor_parser.RealEstate(self.url,price,address,numrooms,storeys)

		return real_estate








		
		




