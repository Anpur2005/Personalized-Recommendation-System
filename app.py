from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import time
import urllib


app = Flask(__name__)


HEADERS = ({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0', 'Accept-Language':'en-US, en;q=0.5'})

# Function to extract Product Title
def get_title(soup):

    try:
        # Outer Tag Object
        title = soup.find("span", attrs={"id":'productTitle'})
        
        # Inner NavigatableString Object
        title_value = title.text

        # Title as a string value
        title_string = title_value.strip()

    except AttributeError:
        title_string = ""

    return title_string

# Function to extract Product Price
def get_price(soup):

    try:
        price = soup.find("span", attrs={'class':'a-price-whole'}).text.strip()

    except AttributeError:

        try:
            # If there is some deal price
            price = soup.find("span", attrs={'id':'priceblock_ourprice'}).string.strip()

        except:
            price = ""

    return "Rs."+price

# Function to extract Product Rating
def get_rating(soup):

    try:
        rating = soup.find("span", attrs={'class':'a-icon-alt'}).string.strip()
    
    except AttributeError:
        try:
            rating = soup.find("i", attrs={'class':'a-icon a-icon-star a-star-4-5'}).string.strip()
        except:
            rating = ""	

    return rating

# Function to extract Number of User Reviews
def get_review_count(soup):
    try:
        review_count = soup.find("span", attrs={'id':'acrCustomerReviewText'}).string.strip()

    except AttributeError:
        review_count = ""	

    return review_count

# Function to extract Availability Status
def get_availability(soup):
    try:
        available = soup.find("div", attrs={'id':'availability'})
        available = available.find("span").string.strip()

    except AttributeError:
        available = "Not Available"	

    return available

def get_image(soup):
    try:
        image = soup.find("img", attrs={'id':'landingImage'}).get('src')

    except AttributeError:
        image = ""

    return image

# Function to scrape Amazon search results 
def scrape_amazon(search_query):
    base_url = "https://www.amazon.in/s?k={}"
    formatted_query = urllib.parse.quote_plus(search_query)  # Encode the query
    formatted_url = base_url.format(formatted_query)
    
    
    # HTTP Request
    webpage = requests.get(formatted_url, headers=HEADERS)

    if webpage.status_code != 200:
            print(f"Blocked or bad response (Status code: {webpage.status_code}). Retrying in 60 seconds...")
            time.sleep(60)  # Wait 60 seconds before retrying
            return "error loading main page"
    # Soup Object containing all data
    soup = BeautifulSoup(webpage.content, "html.parser")
    
    # links = ["https://www.amazon.in"+product.get('href') for product in soup.find_all("a", attrs={'class':'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})]
    links = ["https://www.amazon.in" + product.get('href') if product.get('href').startswith("/") else "https://www.amazon.in/" + product.get('href') for product in soup.find_all("a", attrs={'class':'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})]
    product_list = []

    for link in links:
        print("Scraping URL:", link)
        if not link.startswith("https://www.amazon.in/"):
            print(f"Skipping invalid link: {link}")
            continue  # Skip invalid links
        new_webpage = requests.get(link,headers=HEADERS)

        if new_webpage.status_code == 404:
            print(f"Page not found: {link}. Skipping...")
            continue

        if new_webpage.status_code != 200:
            print(f"Blocked or bad response (Status code: {new_webpage.status_code}). Retrying in 10 seconds...")
            time.sleep(10)  # Wait 60 seconds before retrying
            continue

        new_soup = BeautifulSoup(new_webpage.content, "html.parser")

        product_title = get_title(new_soup)
        if product_title != "":
            product_link = link
            product_image = get_image(new_soup)
            product_rating = get_rating(new_soup)
            product_review_count = get_review_count(new_soup)
            product_price = get_price(new_soup)
            product_availability = get_availability(new_soup)

            # Append the data to the list
            product_data = {
                'title': product_title,
                'link': product_link,
                'image': product_image,
                'rating': product_rating,
                'review_count':product_review_count,
                'price': product_price,
                'availability':product_availability
            }
            product_list.append(product_data)
    
    return product_list

@app.route('/scrape', methods=['POST'])
def scrape():
    # Get the JSON data from the request
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({"error": "No search query provided"}), 400


    # Scrape Amazon (automatically handles all pages)
    products = scrape_amazon(query)

    # Return the scraped data as JSON
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)
