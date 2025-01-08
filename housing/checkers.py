import requests
from bs4 import BeautifulSoup
from housing.constants import FAC_HAB_RES,ARPEJ_RES
def check_studefi(url="https://www.studefi.fr/main.php#listRes", keyword="images/map/marker-residence_logements_disponibles.png", div_id="listRes"):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        div = soup.find('div', id=div_id)
        housing_info = []
        found=False
        if div:
            for img in div.find_all('img', class_="dispoRes"): # Iterate over images in the div
                if keyword in img['src']:  # Check for any keyword match
                    residency_div = img.find_parent('div', class_="list-res-elem")  # Get parent div
                    residency_link = residency_div.find('a')  # Find the link inside the parent div
                    
                    if residency_link:
                        residency_name = residency_link.text.strip() # Extract text from the link tag
                    found=True
                    
                    housing_info.append({"name":residency_name,"address":"","source":"Studefi"})
        return housing_info
    except requests.exceptions.RequestException as e:
        #logging.error(f"Error While checking in Studefi : {e}")
        print(f"Error fetching {url}: {e}")
        return []
def check_crous_housing(url="https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.113475940758818_49.35643927612489_2.4973107796260052_48.80505453139158"):
    """Fetches the CROUS page, parses the HTML, and checks for available housing."""

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.content, 'html.parser')

        # Check for "Aucun logement trouvé" (No housing found)
        if soup.find('h2', class_="SearchResults-mobile") and \
           "Aucun logement trouvé" in soup.find('h2', class_="SearchResults-mobile").text:
            return []

        # If not found, it means housing is available!
        housing_info = []
        housing_items = soup.find_all('li', class_='fr-col-12 fr-col-sm-6 fr-col-md-4 svelte-11sc5my fr-col-lg-4') 
        for item in housing_items:
            # Extract residence name
            name = item.find('h3', class_='fr-card__title').text.strip()
            # Extract address
            address = item.find('p', class_='fr-card__desc').text.strip()
            housing_info.append({"name": name, "address": address,"source":"Crous"})

        return housing_info

    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        #logging.error(f"Error While checking in Crous : {e}")
        return []

def check_fac_habitat_housing():
    """
    Fetches the Fac-Habitat page, parses the HTML, 
    checks for available housing, and returns a list 
    of dictionaries with housing info (name, address, state).
    """
    residences_to_check = FAC_HAB_RES
    
    housing_info = []
    try:
        

        for i in range(len(residences_to_check)):
            api_response = requests.get(residences_to_check[i]["api"])
            api_response.raise_for_status()
            soup = BeautifulSoup(api_response.content, 'html.parser')
            
            
            immediate_availability_element = soup.find('span', class_="dispo green")
            if immediate_availability_element:
                housing_info.append({
                    "name": residences_to_check[i]["name"],
                    "address": residences_to_check[i]["address"],
                    "source": "Fac-Habitat",
                    "URL":residences_to_check[i]["url"],
                    "state":"available"
                })
                continue
            
            
            future_availability_element = soup.find('span', class_="dispo orange")
            if future_availability_element:
                housing_info.append({
                    "name": residences_to_check[i]["name"],
                    "address": residences_to_check[i]["address"],
                    "source": "Fac-Habitat",
                    "URL":residences_to_check[i]["url"],
                    "state":"future"
                })
                continue
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        #logging.error(f"Error While checking in Fac Habitat : {e}")
        return housing_info

    except AttributeError as e:
        print(f"Error parsing page: {e}")  # Catch potential errors in parsing
        #logging.error(f"Error While parsing page in Fac Habitat : {e}")
        return housing_info
    
    
    return housing_info

def check_arpej(api_url="https://www.arpej.fr/wp-json/sn/residences?lang=fr&display=map&related_city[]=52524&price_from=0&price_to=1000&show_if_full=false&show_if_colocations=false"): # for full enable true
    try:
        response = requests.get(api_url)
        response.raise_for_status()
    except Exception as e:
        #logging.error(f"Error While checking in ARPEJ : {e}")
        print("Error fetchign ARPEJ")
        return []
    pre_list = ARPEJ_RES
    data = response.json() 
    housing_info = []
    for residence in data['residences']:
        if residence["title"] in pre_list:
            if residence["extra_data"]['available_rooms'] > 0:  # Check for available rooms
                try:
                    housing_info.append({
                        "name": residence['title'],
                        "address": residence['extra_data']['address'] +" "+residence['extra_data']['city']+" "+residence['extra_data']['zip_code'],
                        "source": "Arpej",
                        "URL": residence['link'],
                        "price":residence["extra_data"]["price_from"],
                        "image":residence["extra_data"]["images"][0]["url"]
                    })
                except: #no images
                    housing_info.append({
                        "name": residence['title'],
                        "address": residence['extra_data']['address'] +" "+residence['extra_data']['city']+" "+residence['extra_data']['zip_code'],
                        "source": "Arpej",
                        "URL": residence['link'],
                        "price":residence["extra_data"]["price_from"]
                    })
    return housing_info


def check_all_res():
    housing_info = check_studefi()
    housing_info_crous = check_crous_housing()
    housing_info_arpej= check_arpej()
    housing_info_fac = check_fac_habitat_housing()
    housing_info.extend(housing_info_crous.copy())
    housing_info.extend(housing_info_arpej.copy())
    housing_info.extend(housing_info_fac.copy())
    return housing_info