from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pdfplumber

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
                return render_template('index.html', error="No tables found on this page.", url=url, data_type='table')

        elif url and data_type == 'image':
            image_format = request.form.get('image_format', 'all')
            num_images = request.form.get('num_images')
            images = scrape_images(url, image_format)
            if images:
                if num_images:
                    try:
                        num_images = int(num_images)
                        images = images[:num_images]
                    except ValueError:
                        pass
                return render_template('index.html', images=images, url=url, 
                                     data_type='image', image_format=image_format,
                                     num_images=num_images or len(images))
            else:
                return render_template('index.html', error="No images found on this page.", url=url, data_type='image')

        elif url and data_type == 'movie':
            movie_data = scrape_movie_details(url)
            if "error" in movie_data:
                return render_template('index.html', error=movie_data["error"], data_type='movie')
            else:
                return render_template('index.html', movie_data=movie_data, data_type='movie')
            
        elif url and data_type == 'video':
            video_format = request.form.get('video_format', 'all')
            num_videos = request.form.get('num_videos')
            video_data = scrape_videos(url, video_format)
            if video_data:
                if num_videos:
                    try:
                        num_videos = int(num_videos)
                        video_data = video_data[:num_videos]
                    except ValueError:
                        pass
                return render_template('index.html', video_data=video_data, url=url, 
                                     data_type='video', video_format=video_format,
                                     num_videos=num_videos or len(video_data))
            else:
                return render_template('index.html', error="No videos found on this page.", url=url, data_type='video')

        elif url and data_type == 'news':
            num_headlines = request.form.get('num_headlines')
            headlines = scrape_news_headlines(url)
            if headlines:
                if num_headlines:
                    try:
                        num_headlines = int(num_headlines)
                        headlines = headlines[:num_headlines]
                    except ValueError:
                        pass
                return render_template('index.html', headlines=headlines, url=url, 
                                     data_type='news', num_headlines=num_headlines or len(headlines))
            else:
                return render_template('index.html', error="No verified headlines found on this page.", url=url, data_type='news')

        elif url and data_type == 'pdf':
            pdf_links = scrape_pdf_links(url)
            if pdf_links:
                return render_template('index.html', pdf_links=pdf_links, url=url, data_type='pdf')
            else:
                return render_template('index.html', error="No PDF files found on this page.", url=url, data_type='pdf')

    return render_template('index.html', tables=None, images=None, movie_data=None, video_data=None, headlines=None, pdf_links=None, error=None)

@app.route('/extract_pdf_info', methods=['POST'])
def extract_pdf_info():
    """Extract text and metadata from a PDF URL."""
    pdf_url = request.form.get('pdf_url')
    try:
        # Download the PDF
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()
        
        # Save PDF temporarily
        temp_file = 'temp.pdf'
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        # Extract text and metadata using pdfplumber
        with pdfplumber.open(temp_file) as pdf:
            # Extract text
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Extract metadata (if available)
            metadata = pdf.metadata if pdf.metadata else {}
            title = metadata.get('Title', 'N/A')
            author = metadata.get('Author', 'N/A')
            page_count = len(pdf.pages)
        
        # Clean up
        os.remove(temp_file)
        
        return jsonify({
            'success': True,
            'text': text,  # Return full text
            'title': title,
            'author': author,
            'page_count': page_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def scrape_tables(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
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
    except requests.exceptions.RequestException:
        return None

def scrape_images(url, image_format):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        images = soup.find_all('img')
        allowed_formats = {'png': ['.png'], 'jpg': ['.jpg', '.jpeg'], 'all': ['.png', '.jpg', '.jpeg']}
        image_urls = []
        for img in images:
            img_url = img.get('src')
            if img_url and any(img_url.endswith(ext) for ext in allowed_formats[image_format]):
                if img_url.startswith('http'):
                    image_urls.append(img_url)
                else:
                    base_url = url.rsplit('/', 1)[0]
                    full_url = os.path.join(base_url, img_url)
                    image_urls.append(full_url)
        return image_urls
    except requests.exceptions.RequestException:
        return None

def scrape_movie_details(movie_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        search_url = f"https://www.imdb.com/find?q={movie_name.replace(' ', '+')}&ref_=nv_sr_sm"
        search_response = requests.get(search_url, headers=headers, timeout=10)
        search_response.raise_for_status()
        search_soup = BeautifulSoup(search_response.content, 'html.parser')
        first_result = search_soup.select_one('.ipc-metadata-list-summary-item a.ipc-metadata-list-summary-item__t')
        if not first_result:
            return {"error": "No movie found with that name."}
        movie_url = "https://www.imdb.com" + first_result['href']
        movie_response = requests.get(movie_url, headers=headers, timeout=10)
        movie_response.raise_for_status()
        soup = BeautifulSoup(movie_response.content, 'html.parser')
        title = soup.select_one('h1').text.strip()
        poster = soup.select_one('img.ipc-image')
        poster_url = poster['src'] if poster else "N/A"
        year_elem = soup.select_one('a[href*="/releaseinfo"]')
        year = year_elem.text.strip() if year_elem else "N/A"
        rating_elem = soup.select_one('div[data-testid="hero-rating-bar__aggregate-rating__score"] span')
        rating = rating_elem.text.strip() + "/10" if rating_elem else "N/A"
        plot_elem = soup.select_one('[data-testid="plot"]')
        plot = plot_elem.text.strip() if plot_elem else "N/A"
        genre_elem = soup.select_one('.ipc-chip.ipc-chip--on-baseAlt .ipc-chip__text')
        genre = genre_elem.text.strip() if genre_elem else "N/A"
        return {
            "name": title,
            "poster_url": poster_url,
            "year": year,
            "rating": rating,
            "plot": plot,
            "genre": genre
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error occurred: {e}"}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}

def scrape_videos(url, video_format):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        videos = soup.find_all('video')
        video_urls = []
        for video in videos:
            video_sources = video.find_all('source')
            for source in video_sources:
                video_url = source.get('src')
                if video_url:
                    if video_format != 'all' and not video_url.endswith(video_format):
                        continue
                    if video_url.startswith('http'):
                        video_urls.append(video_url)
                    else:
                        base_url = url.rsplit('/', 1)[0]
                        full_url = os.path.join(base_url, video_url)
                        video_urls.append(full_url)
        return video_urls
    except requests.exceptions.RequestException:
        return None

def scrape_news_headlines(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = soup.find_all(['h1', 'h2', 'h3'])
        if not headlines:
            headlines = soup.find_all('a', class_=lambda x: x and ('excerpt' in x.lower() or 'title' in x.lower() or 'headline' in x.lower()))
        if not headlines:
            headlines = soup.find_all('a')
        def is_valid_headline(text):
            if len(text) < 15:
                return False
            non_headline_phrases = [
                'home', 'about', 'contact', 'login', 'register', "today's gallery"
            ]
            if any(phrase.lower() in text.lower() for phrase in non_headline_phrases):
                return False
            if re.search(r'\d', text) or re.search(r'[A-Z][a-z]+', text):
                return True
            return True
        headline_texts = []
        for headline in headlines:
            text = headline.get_text().strip()
            if text and is_valid_headline(text) and text not in headline_texts:
                headline_texts.append(text)
        return headline_texts if headline_texts else None
    except requests.exceptions.RequestException:
        return None

def scrape_pdf_links(url):
    """Scrape a webpage for PDF links, first with BS4, then with Selenium if no PDFs are found."""
    # First, try with BeautifulSoup (faster for static content)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        pdf_links = []
        
        # Check <a> tags
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf') and href.startswith(('http://', 'https://')):
                pdf_name = href.split('/')[-1].split('?')[0]  # Extract the PDF name, remove query params
                pdf_links.append({'url': href, 'name': pdf_name})
        
        # Check <source> tags
        for source in soup.find_all('source', src=True):
            src = source['src']
            if src.lower().endswith('.pdf') and src.startswith(('http://', 'https://')):
                pdf_name = src.split('/')[-1].split('?')[0]  # Extract the PDF name, remove query params
                pdf_links.append({'url': src, 'name': pdf_name})
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_pdf_links = []
        for link in pdf_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_pdf_links.append(link)
        
        if unique_pdf_links:
            print("Found PDFs with BeautifulSoup")
            return unique_pdf_links
    
    except requests.exceptions.RequestException as e:
        print(f"BS4 request failed: {e}")
        return None

    # If no PDFs found with BS4, fall back to Selenium
    print("No PDFs found with BS4, falling back to Selenium")
    
    options = Options()
    options.headless = True  # Ensure headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url)
        # Wait for the "Documents" button and click it (if present)
        try:
            documents_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Documents')]"))
            )
            documents_button.click()
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "a.pdf-link"))
            )  # Wait for PDF links to load
        except Exception as e:
            print(f"Warning: Could not click 'Documents' button or wait for PDFs: {e}")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        pdf_links = []
        
        # Check <a> tags with class 'a.pdf-link' (specific to Microchip)
        for link in soup.find_all('a', class_='a.pdf-link', href=True):
            href = link['href']
            if href.lower().endswith('.pdf') and href.startswith(('http://', 'https://')):
                pdf_name = href.split('/')[-1].split('?')[0]  # Extract the PDF name, remove query params
                pdf_links.append({'url': href, 'name': pdf_name})
        
        # Check other <a> tags as fallback
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf') and href.startswith(('http://', 'https://')):
                pdf_name = href.split('/')[-1].split('?')[0]  # Extract the PDF name, remove query params
                pdf_links.append({'url': href, 'name': pdf_name})
        
        # Check <source> tags
        for source in soup.find_all('source', src=True):
            src = source['src']
            if src.lower().endswith('.pdf') and src.startswith(('http://', 'https://')):
                pdf_name = src.split('/')[-1].split('?')[0]  # Extract the PDF name, remove query params
                pdf_links.append({'url': src, 'name': pdf_name})
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_pdf_links = []
        for link in pdf_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_pdf_links.append(link)
        
        return unique_pdf_links if unique_pdf_links else None
    
    except Exception as e:
        print(f"Error scraping PDFs with Selenium: {e}")
        return None
    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True)