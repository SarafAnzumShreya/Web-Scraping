from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        data_type = request.form.get('data_type')

        if url and data_type == 'table':
            tables = scrape_tables(url)
            if tables:
                if 'table_number' in request.form:
                    selected_tables = request.form.getlist('table_number')
                    selected_tables = [int(i) for i in selected_tables]
                    return render_template('index.html', tables=tables, url=url, 
                                        selected_tables=selected_tables, data_type='table')
                return render_template('index.html', tables=tables, url=url, data_type='table')
            else:
                return render_template('index.html', error="No tables found on this page.", url=url)

        elif url and data_type == 'image':
            image_format = request.form.get('image_format', 'all')
            num_images = request.form.get('num_images')
            images = scrape_images(url, image_format)
            if images:
                # Apply num_images filter if provided
                if num_images:
                    try:
                        num_images = int(num_images)
                        images = images[:num_images]
                    except ValueError:
                        pass  # Use all images if invalid number
                return render_template('index.html', images=images, url=url, 
                                     data_type='image', image_format=image_format,
                                     num_images=num_images or len(images))
            else:
                return render_template('index.html', error="No images found on this page.", url=url)

        elif url and data_type == 'movie':
            movie_data = scrape_movie_details(url)
            if "error" in movie_data:
                return render_template('index.html', error=movie_data["error"], data_type='movie')
            else:
                return render_template('index.html', movie_data=movie_data, data_type='movie')

    return render_template('index.html', tables=None, images=None, movie_data=None, error=None)

def scrape_tables(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table')
    table_data = []
    for table in tables:
        rows = table.find_all('tr')
        table_rows = []
        for row in rows:
            columns = row.find_all('td')
            columns = [col.text.strip() for col in columns]
            if columns:
                table_rows.append(columns)
        if table_rows:
            table_data.append(table_rows)
    return table_data

def scrape_images(url, image_format):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    images = soup.find_all('img')

    allowed_formats = {
        'png': ['.png'],
        'jpg': ['.jpg', '.jpeg'],
        'all': ['.png', '.jpg', '.jpeg']
    }

    image_urls = []
    for img in images:
        img_url = img.get('src')
        if img_url:
            # Filter by file extension
            if any(img_url.endswith(ext) for ext in allowed_formats[image_format]):
                if img_url.startswith('http'):
                    image_urls.append(img_url)
                else:
                    base_url = url.rsplit('/', 1)[0]
                    full_url = os.path.join(base_url, img_url)
                    image_urls.append(full_url)

    return image_urls

def scrape_movie_details(movie_name):
    options = Options()
    options.add_experimental_option('prefs', {
        "download.default_directory": r"D:\Scapping",
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    URL = "https://www.imdb.com/"
    driver.get(URL)
    driver.maximize_window()

    try:
        # Find search bar and search for movie
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "suggestion-search"))
        )
        search_box.send_keys(movie_name)
        search_box.send_keys(Keys.RETURN)

        # Wait for and click the first result
        first_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ipc-metadata-list-summary-item a.ipc-metadata-list-summary-item__t"))
        )
        first_result.click()

        # Wait for the movie page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Stars')]"))
        )

        # Extract movie name
        title_element = driver.find_element(By.TAG_NAME, "h1")
        name = title_element.text.strip()

        # Check if the extracted name matches the search movie
        if name.lower() != movie_name.lower():
            return {"error": "Movie not found"}

        # Extract poster URL
        poster_element = driver.find_element(By.CSS_SELECTOR, "img.ipc-image")
        poster_url = poster_element.get_attribute("src")

        # Extract year
        year_element = driver.find_element(By.XPATH, "//ul[contains(@class, 'ipc-inline-list--show-dividers')]//a[contains(@href, 'releaseinfo')]")
        year = year_element.text.strip()

        # Extract rating
        rating_container = driver.find_element(By.CSS_SELECTOR, "div[data-testid='hero-rating-bar__aggregate-rating__score']")
        rating_elements = rating_container.find_elements(By.TAG_NAME, "span")
        rating = rating_elements[0].text + "/10"

        # Extract plot
        plot_element = driver.find_element(By.CSS_SELECTOR, "[data-testid='plot']")
        plot = plot_element.text.strip()

        # Extract one genre
        genre_element = driver.find_elements(By.CSS_SELECTOR, ".ipc-chip.ipc-chip--on-baseAlt .ipc-chip__text")[0]
        genre = genre_element.text.strip()

        return {
            "name": name,
            "poster_url": poster_url,
            "year": year,
            "rating": rating,
            "plot": plot,
            "genre": genre
        }

    except Exception as e:
        return {"error": f"An error occurred: {e}"}

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True)