import requests
from bs4 import BeautifulSoup
import json

class Egencia(object):
    
    
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.session = requests.session()
        self.__login()
    
    
    def __login(self):
        login_screen = self.session.get("https://www.egencia.co.uk/app?service=external&page=Login&mode=form&market=GB&lang=en")
        # Find the POST form
        b = BeautifulSoup(login_screen.text, "lxml")                  
        action = b.find_all("form")[0]["action"].replace("./accessToken", "")
        # Make a payload with all the default values for the form
        data = {}
        for input_node in b.find_all("form")[0].find_all("input"):
            data[input_node["name"]] = input_node["value"]
        # Override the username and password fields (default is "")
        data["userName"] = self.user
        data["password"] = self.password
        # Use this payload to login
        new_url = "https://www.egencia.com/auth/v1/accessToken" + action
        r = self.session.post(new_url, data=data)
    
    
    def get_all_rooms(self, lon, lat, check_in, check_out, brand):
        user_id = json.loads(self.session.get("https://www.egencia.co.uk/user-service/v2/users/"+self.user).text)["additional_information"]["user_id"]
        company_id = json.loads(self.session.get("https://www.egencia.co.uk/user-service/v2/users/{}?include=roles&include=info".format(user_id)).text)["company_ids"][0]
        # Create the request URL
        hotels_url="".join(["https://www.egencia.co.uk/hotel-search-service/v1/hotels?",
                             "radius_unit=km&adults_per_room=1&search_type=ADDRESS&start=0&source=HOTEL_WEBAPP&source_version=1.0&search_page=SEARCH_RESULTS&rate_amenity=&hotel_amenity=&want_in_policy_rates_only=false&want_central_bill_eligible_rates_only=false&want_prepaid_rates_only=false&want_free_cancellation_rates_only=false&chain_id=&neighborhood_filter_id=&minimum_stars=0&minimum_price=&maximum_price=&apply_prefilters=true",
                             "&count=9999",
                             "&longitude=", str(lon),
                             "&latitude=", str(lat),
                             "&check_in_date=", check_in,
                             "&check_out_date=", check_out,
                             "&hotel_name=", brand,
                             "&main_traveler=", str(user_id),
                             "&traveler=", str(user_id),
                             "&company_id=", str(company_id)])
        search = self.session.get(hotels_url)
        resp = json.loads(search.text)
        return resp

