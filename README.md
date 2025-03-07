# Web Scraper Application

A Flask-based web scraping application that extracts tables, images, and movie details from websites. This project uses BeautifulSoup for static content scraping and Selenium for dynamic content scraping (e.g., IMDb movie details).

## Features
- **Table Scraping**: Extract and display tables from any webpage.
- **Image Scraping**: Fetch images with filtering by format (PNG, JPG) and limit the number of images displayed.
- **Movie Details Scraping**: Retrieve movie information (title, poster, year, rating, plot, genre) from IMDb using Selenium.
- **Video Scraping**: Fetch and display videos from a webpage with the option to filter by format (MP4, WEBM, OGG) and limit the number of videos displayed.
- **News Headline Scraping**: Extract and display headlines from news websites. Filters out non-headline content by checking text length and specific phrases.
- **eBay Product Scraping**: Retrieve product details (title, link, image, price, rating) from eBay by searching for a product.
- **PDF Link Scraping**: Scrape a webpage for PDF links, first using BeautifulSoup for static content, then falling back to Selenium for dynamic content. Handles duplicates and multiple tag types.


## Technologies Used
- **Python**: Core programming language.
- **Flask**: Web framework for the application.
- **BeautifulSoup**: Library for parsing HTML and XML documents.
- **Selenium**: Browser automation for dynamic content scraping.
- **WebDriver Manager**: Automates ChromeDriver installation.
- **Tailwind CSS**: Styling framework via CDN.
- **Jinja2**: Templating engine for HTML rendering.
- **pdfplumber**: Library for extracting text, tables, and metadata from PDF files.
- **logging**: Built-in Python module used for logging events, errors, and debugging information.

## Installation

### Prerequisites
- Python 3.x
- Chrome browser (for Selenium)


