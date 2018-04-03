import requests
from geopy.geocoders import Nominatim
import telegram
import pandas as pd
from datetime import datetime, timedelta
import itertools

import settings 
from requests_egencia import Egencia


# Function to parse their response payload to get what we actually want
def find_double_points_offers(lon, lat, check_in, check_out, brand, max_amount, max_distance):
    out = e.get_all_rooms(lon, lat, check_in, check_out, brand)
    offers = []
    for hotel in out["hotels"]:
        if hotel.get("rooms") and float(hotel["location"]["distance_from_search"]["value"]) < max_distance:
            for room in hotel["rooms"]:
                if '2 X Points' in room["description"] and room["price"]["user_currency"]["amount"] <= max_amount:
                    offers.append({
                        "hotel_name": hotel["hotel_name"],
                        "description" : room["description"], 
                        "rate" : room["price"]["user_currency"]["amount"],
                        "check in": check_in,
                        "check out": check_out
                    })
    return offers


# Helper function to convert the csv into checkin dates for each of the citys
def get_check_in_out_dates(path):
    data = pd.read_csv(path)
    data['Date'] = pd.to_datetime(data['Date'], format="%d/%m/%Y")
    data.sort_values(by="Date", inplace=True)
    data = data.where(data.notnull(), None)
    data.dropna(axis=0, how='all', inplace=True)
    out=[]
    tmp = {}
    for i in data.index[:-1]:
        if not tmp.get("check in") and data.iloc[i]["City"] is not None:
            if data.iloc[i]["City"] is None:
                print(data.iloc[i]["City"])
            tmp["check in"] = data.iloc[i]["Date"].strftime('%Y-%m-%d')
        if (data.iloc[i]["City"] != data.iloc[i+1]["City"] or i == max(data.index)-1) and tmp.get("check in"):
            tmp["check out"] = (data.iloc[i]["Date"] + timedelta(days=1)).strftime('%Y-%m-%d')
            tmp["city"] = data.iloc[i]["City"]
            tmp["max amount"] = data.iloc[i]["Max cost"]
            out.append(tmp); tmp = {}
    return out


# Helper function to produce markdown to send to Telegram 
def make_pretty_message(offers):
    md = ""
    for offer in offers:
        md += "*{}*\n".format(offer['hotel_name'])
        md += "_{} - {}\n".format(datetime.strptime(offer["check in"], "%Y-%m-%d").strftime('%d/%m/%Y'), 
                                datetime.strptime(offer["check out"], "%Y-%m-%d").strftime('%d/%m/%Y'))
        md += "{}\n".format(offer["description"])
        md += "£{0:.2f}_\n".format(offer["rate"])
        md += "\n"
    return md


# Helper function to remove any duplicates incase they happen
def remove_duplicate_results(results):
    return [dict(y) for y in set(tuple(x.items()) for x in results)]


# Helper function to return all permutations of dates ordered by length
def get_date_perms(check_in, check_out):
    delta = datetime.strptime(check_out, "%Y-%m-%d")-datetime.strptime(check_in, "%Y-%m-%d")
    all_dates = [datetime.strptime(check_out, "%Y-%m-%d") + timedelta(days=i) for i in range(delta.days + 1)]
    l = list(itertools.permutations(all_dates, 2))
    date_perms = [(x[0].strftime('%Y-%m-%d'), x[1].strftime('%Y-%m-%d')) for x in l if x[0] < x[1]]
    return sorted(date_perms, key=lambda tup: datetime.strptime(tup[1], "%Y-%m-%d")-datetime.strptime(tup[0], "%Y-%m-%d"), reverse=True)


# Helper function to sort the message in order of checkin date
def sort_results(results):
    return sorted(results, key=lambda d: (datetime.strptime(d["check in"], "%Y-%m-%d"), 
                                          datetime.strptime(d["check out"], "%Y-%m-%d")-datetime.strptime(d["check in"], "%Y-%m-%d")), 
                  reverse=False)


if __name__ == "__main__":
    bot = telegram.Bot(token=settings.API_TOKEN)
    chat_id = settings.CHAT_ID

    geolocator = Nominatim()

    brand = "hilton"
    max_distance = 3

    results = []
    my_searches = get_check_in_out_dates("data.csv")

    e = Egencia(settings.CREDENTIALS["email"], settings.CREDENTIALS["password"])
    
    for my_search in my_searches:
        max_amount = my_search["max amount"]
        location = geolocator.geocode(my_search["city"])
        all_dates = get_date_perms(my_search["check in"], my_search["check out"])
        
        for dates in all_dates:
            check_in = dates[0]
            check_out = dates[1]
            print("Searching Egencia for: [brand: {}, max_amount: {}, location: {}, check_in: {}, check_out: {}]".format(brand,max_amount, location, check_in, check_out))
        
            offers = find_double_points_offers(location.raw['lon'], location.raw['lat'], check_in, check_out, brand, max_amount, max_distance)
            if len(offers) > 0:
                print("I found some offers!\033[1;36m")
                print(offers);print("\033[0;0m")
                results += offers
                #break

    if len(results) > 0:
        dd_results = remove_duplicate_results(results)
        sorted_results = sort_results(dd_results)
        output = make_pretty_message(sorted_results)
        bot.send_message(chat_id, output, parse_mode=telegram.ParseMode.MARKDOWN)



