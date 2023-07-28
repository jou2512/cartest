import json
import re
from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup

app = FastAPI()


def format_name(name):
    # Remove special characters like "&" and connect words with hyphens
    name = re.sub(r"[^a-zA-Z0-9- ]", "", name)
    return "-".join(format_engine(name).lower().split())


def format_engine(engine):
    # Remove "hp" from the end of the engine string
    engine = engine.replace("hp", "").strip()
    return engine


@app.get("/manufacturers/")
async def get_manufacturers(types: str = None):
    url = "https://www.olsx.lu/en/chiptuning"
    response = requests.get(url)
    if response.status_code != 200:
        return {"success": False, "message": "Failed to fetch data from the website."}

    soup = BeautifulSoup(response.content, "html.parser")

    # Define the available types
    available_types = ["type-car", "type-moto", "type-agri",
                       "type-trucks", "type-jetski", "type-others"]

    # Split the types parameter into a list of individual types
    selected_types = types.split(",") if types else []

    # Check if the provided types are valid
    invalid_types = [
        selected_type for selected_type in selected_types if selected_type not in available_types]
    if invalid_types:
        return {"success": False, "message": f"Invalid types: {', '.join(invalid_types)}"}

    # Filter the elements based on the specified types or select all if types is not provided
    manufacturers = []
    for selected_type in selected_types:
        manufacturers.extend([format_name(brand.find("small", class_="manufacturer").text)
                             for brand in soup.select(f"ul.row.manufacturers.{selected_type} li")])

    return {"success": True, "manufacturers": manufacturers}


@app.get("/models/")
async def get_models(brand: str):
    formatted_brand = format_name(brand)
    url = f"https://www.olsx.lu/en/chiptuning/{formatted_brand}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"success": False, "message": "Failed to fetch data from the website."}

    soup = BeautifulSoup(response.content, "html.parser")
    models = [format_name(model.find("span", class_="model").text)
              for model in soup.select("ul.row.models li")]
    return {"success": True, "models": models}


@app.get("/buildyears/")
async def get_build_years(brand: str, model: str):
    formatted_brand = format_name(brand)
    formatted_model = format_name(model)
    url = f"https://www.olsx.lu/en/chiptuning/{formatted_brand}/{formatted_model}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"success": False, "message": "Failed to fetch data from the website."}

    soup = BeautifulSoup(response.content, "html.parser")
    build_years = [format_name(year.find("span", class_="version").text)
                   for year in soup.select("ul.row.models.versions li")]
    return {"success": True, "build_years": build_years}


@app.get("/engines/")
async def get_engines(brand: str, model: str, build_year: str):
    formatted_brand = format_name(brand)
    formatted_model = format_name(model)
    formatted_build_year = format_name(build_year)
    url = f"https://www.olsx.lu/en/chiptuning/{formatted_brand}/{formatted_model}/{formatted_build_year}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"success": False, "message": "Failed to fetch data from the website."}

    soup = BeautifulSoup(response.content, "html.parser")
    engines = [f"{engine.find('span', class_='engine').text} {engine.find('span', class_='power').text}" for engine in soup.select(
        "ul.row.models li")]
    return {"success": True, "engines": engines}


@app.get("/scrape/")
def scrape_data(brand: str, model: str, build_year: int, engine_hp: str):

    print(brand, model, build_year, engine_hp)

    # Create the URL with the encoded variables
    url = f"https://www.olsx.lu/en/chiptuning/{format_name(brand)}/{format_name(model)}/{format_name(build_year)}/{formate_name(engine_hp)}"

    # Send a GET request to the URL and parse the HTML content
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table with class "results"
    table = soup.find("table", class_="results")

    # Find all rows (tr) in the table body
    rows = table.find_all("tr")

    # Extract the required information from the table
    power_stock = rows[1].find_all("td")[1].text
    power_stage1 = rows[1].find_all("td")[2].text
    power_gain = rows[1].find_all("td")[3].text

    torque_stock = rows[2].find_all("td")[1].text
    torque_stage1 = rows[2].find_all("td")[2].text
    torque_gain = rows[2].find_all("td")[3].text
    return {
        "Power": {
            "Stock": power_stock,
            "Stage 1": power_stage1,
            "Gain": power_gain,
        },
        "Torque": {
            "Stock": torque_stock,
            "Stage 1": torque_stage1,
            "Gain": torque_gain,
        },
    }

@app.get("/createjson/")
def scrape_data():
    url = "https://www.olsx.lu/en/chiptuning"
    response = requests.get(url)

    if response.status_code != 200:
        return {"success": False, "message": "Failed to fetch data from the website."}

    soup = BeautifulSoup(response.content, "html.parser")
    data = {}

    # ["type-car", "type-moto", "type-agri","type-trucks", "type-jetski", "type-others"]
    selected_types = ["type-car"]
    # Filter the elements based on the specified types or select all if types is not provided
    manufacturers = []
    for selected_type in selected_types:
        manufacturers.extend(soup.select(
            f"ul.row.manufacturers.{selected_type} li"))

    for brand_element in manufacturers:
        brand_url = brand_element.find("a")["href"]
        brand_name = brand_element.find("small", class_="manufacturer").text

        brand_models = []
        for model_element in BeautifulSoup(requests.get(brand_url).content, "html.parser").select("ul.row.models li"):
            model_name = model_element.find("span", class_="model").text

            model_build_years = []
            for build_year_element in BeautifulSoup(requests.get(model_element.find("a")["href"]).content, "html.parser").select("ul.row.models.versions li"):
                build_year = build_year_element.find(
                    "span", class_="version").text

                model_engines = []
                for engine in BeautifulSoup(requests.get(build_year_element.find("a")["href"]).content, "html.parser").select("ul.row.models li"):
                    engine_text = engine.find("span", class_="engine").text
                    power_text = engine.find("span", class_="power").text
                    model_engines.append(engine_text + " " + power_text)

                model_build_years.append(
                    {"build_year": build_year, "engines": model_engines})

            brand_models.append(
                {"model_name": model_name, "build_years": model_build_years})

        data[brand_name] = brand_models

    with open("scraped_data.json", "w") as f:
        json.dump(data, f)

    return {"success": True, "message": "Scraping completed and data saved as scraped_data.json."}
