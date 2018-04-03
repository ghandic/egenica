import telegram
from geopy.geocoders import Nominatim

# Add the Egencia trawler
from selenium_egencia import Egencia, make_pretty_message
# Add our credentials
import settings 


bot = telegram.Bot(token=settings.API_TOKEN)
chat_id = settings.CHAT_ID

geolocator = Nominatim()

options = {
	"checkin": "2018-04-16",
	"checkout": "2018-04-20",
	"brand": "Hilton",
	"city": "Croydon",
	"maxspend": 85
}

location = geolocator.geocode(options["city"])

options['lon'] = location.raw['lon']
options['lat'] = location.raw['lat']

if __name__ == "__main__":
	eg = Egencia(settings.CREDENTIALS)
	offers = eg.get_double_points_offers(options["checkin"], 
										 options["checkout"],
										 options["brand"], 
										 options["lat"], 
										 options["lon"],
										 options["maxspend"])
	
	if len(offers) > 0:
		output = make_pretty_message(offers)
		bot.send_message(chat_id, output, parse_mode=telegram.ParseMode.MARKDOWN)

	eg.close()