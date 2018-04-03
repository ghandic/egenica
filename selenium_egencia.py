from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time


class Egencia(object):
    
    
    def __init__(self, credentials):
        self.driver = webdriver.Remote('http://localhost:4444/wd/hub', webdriver.DesiredCapabilities.CHROME)
        self.__login(credentials)
        self.standard_wait_time = 10
    
    
    def close(self):
        self.driver.quit()
    

    def __login(self, credentials):
        # Go to the home page to log in
        self.driver.get("https://www.egencia.com/public/uk/")
        self.driver.find_element_by_id("login").click()
        self.driver.find_element_by_id("userName").send_keys(credentials["email"])
        self.driver.find_element_by_id("password").send_keys(credentials["password"])
        self.driver.find_element_by_id("authLoginSubmit").click()
    
    
    def get_double_points_offers(self, checkin, checkout, brand, lat, lon, maxspend):
        
        double_points_offers = []

        self.driver.get("https://www.egencia.co.uk/hotels/search?" + \
               "lon=" + lon + "&lat=" + lat + \
               "&start_date=" + checkin + \
               "&end_date=" + checkout + \
               "&hotel_name=" + brand)

        time.sleep(self.standard_wait_time)
        try:
            self.driver.find_elements_by_class_name("modal-close")[0].click()
        except:
            pass

        time.sleep(self.standard_wait_time)
        available_hotels = self.driver.find_elements_by_class_name("hotel-available")


        for hotel in available_hotels:
            # Find the hotel name and make an empty entry 
            hotel_name = hotel.find_elements_by_class_name("hotel-name-for-coworker-bookings")[0].get_attribute('innerHTML')
            #print("Hotel: {}".format(hotel_name))
            hotels_dp_offers = {"name": hotel_name, "offers":[]}

            # Click on the hotel
            hotel.click()
            time.sleep(self.standard_wait_time)

            # Show all of the rates
            self.driver.find_element_by_id("hotel-details-view-all-rates-toggle").click()
            time.sleep(self.standard_wait_time)
            
            # Look through all the rates for a double points offer within budget
            for rate in self.driver.find_elements_by_class_name("rate-tile"):
                dp_offers = rate.find_elements_by_xpath('.//span[contains(text(), "2 X Points")]')
                dp_rate = float(rate.find_elements_by_class_name('price-details')[0].get_attribute('innerHTML').replace('£', ''))
                
                if len(dp_offers) > 0 and dp_rate <= maxspend:
                    description = dp_offers[0].get_attribute('innerHTML')
                    hotels_dp_offers["offers"].append({"description": description, "rate": dp_rate})

            # If there are offers then add to the payload
            if len(hotels_dp_offers["offers"]) > 0:
                double_points_offers.append(hotels_dp_offers)

            # Return to view all the hotels
            self.driver.find_element_by_id("hotel-details-close-button").click()

        return double_points_offers


def make_pretty_message(offers):
    html = ""
    for hotel in offers:
        html += "*{}*\n".format(hotel['name'])
        for offer in hotel["offers"]:
            html += "_{}\n".format(offer["description"])
            html += "£{0:.2f}_\n".format(offer["rate"])
        html += "\n"
    return html


