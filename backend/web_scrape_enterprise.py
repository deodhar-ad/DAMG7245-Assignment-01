from apify_client import ApifyClient
import os
import requests
import json
from dotenv import load_dotenv,dotenv_values
from bs4 import BeautifulSoup
import urllib.parse
import hashlib
from datetime import datetime
from uuid import uuid4
from storage.s3_utils import upload_file_to_s3

def scrape_and_convert_enterprise(url):
    """
    This function takes url as an input and uses apify client to scrape
    the webpage and converts the output to markdown format and the images
    present in the webpage are downloaded to images folder
    """
    # Load environment variables from .env file
    load_dotenv()
    

    
    # Initialize the ApifyClient with your API token
    apify_client_token = os.getenv('APIFY_TOKEN')
    client = ApifyClient(apify_client_token)

    # Define the input for the Actor
    run_input = {
    "startUrls": [{"url": url}],
    "maxCrawlPages": 1,
    "maxCrawlDepth": 0,
    "saveHtml": True,
    "saveMarkdown": True,
    "saveFiles": True,
    "downloadImages": True,
    "forceResponseEncoding": "utf-8",
    "htmlTransformer": "readableTextIfPossible",
    "includeFiles": ["jpg", "jpeg", "png", "gif","svg"],
    "cleanHtml": {
        "removeNavigation": True,
        "removeSearchboxes": True,
        "removeFooter": True,
        "keepContent": [
            "#content",
            "#main-container",
            ".subjects",
            ".list-unstyled",
            "[id^='main-']",
            "[id^='astro-ph']",
            "[id^='math']",
            "[id^='cs']"
        ]
    }
}
    # Run the Actor and wait for it to finish
    run = client.actor("apify/website-content-crawler").call(run_input=run_input)

    # Unique folder name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_folder = f"enterprise_{timestamp}_{uuid4().hex[:8]}"

    # Extract images and upload them to S3
    image_s3_urls = []

    # Fetch and process the results
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        url = item["url"]
        markdown_content = item["markdown"]

        html_content = item["html"]
        soup = BeautifulSoup(html_content,'html.parser')
        images = soup.find_all('img')

        # Download images and update markdown content
        for img in images:
            img_url = img.get('src')
            if img_url:
                original_url = img_url
                if not img_url.startswith(('http://', 'https://')):
                    img_url = urllib.parse.urljoin(url, img_url)
                try:
                    img_filename = os.path.basename(img_url)
                    img_path = f"temp_{uuid4().hex[:8]}_{img_filename}"
                    response = requests.get(img_url, timeout=10)
                    if response.status_code == 200:
                        with open(img_path, "wb") as f:
                            f.write(response.content)
                        print(f"Downloaded: {img_url}")
                    
                        print(f"uploading {img_filename} to S3...")
                        image_s3_url = upload_file_to_s3(img_path,
                                                     f"scraped_websites/enterprise/{unique_folder}/images",
                                                     "images",
                                                     metadata={
                                                         "original_url" : url,
                                                         "upload_timestamp": timestamp,
                                                         "file_type" : "image",
                                                         "unique_folder": unique_folder
                                                     })
                    
                        image_s3_urls.append(image_s3_url)
                        # Update markdown content to reference local image
                        markdown_content = markdown_content.replace(original_url, image_s3_url)
                        markdown_content = markdown_content.replace(img_url, image_s3_url)
                        os.remove(img_path)

                except Exception as e:
                    print(f"Error Downloading {img_url}:{str(e)}")

        # Write markdown content to file
        markdown_file_path = f"{uuid4().hex[:8]}.md"
        with open(markdown_file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Markdown content saved temporarily to {markdown_file_path}")

        #Uploading the markdown file to S3
        markdown_s3_url = upload_file_to_s3(
            markdown_file_path,
            f"scraped_websites/enterprise/{unique_folder}/markdown",
            "markdown",
            metadata={
                "original_url": url,
                "upload_timestamp": timestamp,
                "file_type": "markdown",
                "unique_folder": unique_folder
            }
        )
        os.remove(markdown_file_path)
        return {
            "markdown_s3_url" : markdown_s3_url,
            "image_s3_urls": image_s3_urls,
            "unique_folder": unique_folder,
            "status": "success",
            "message": "Webpage scraped and uploaded to S3 successfully."
        }
        

