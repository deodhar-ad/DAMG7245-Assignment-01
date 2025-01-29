import os
import requests
from bs4 import BeautifulSoup
from markitdown import MarkItDown
from uuid import uuid4
from datetime import datetime
from storage.s3_utils import upload_file_to_s3  # Import S3 utilities


def scrape_and_convert(url: str) -> dict:
    """
    Scrapes a web page, extracts images, and converts content to Markdown, storing everything on S3.

    Args:
        url (str): The URL of the web page to scrape.

    Returns:
        dict: A dictionary with S3 URLs for the Markdown file and extracted images.
    """
    try:
        # Step 1: Generate a unique folder for this URL
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"web_{timestamp}_{uuid4().hex[:8]}"  # Unique folder name

        # Step 2: Fetch the web page
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        print(f"Scraping content from {url}")

        # Step 3: Extract images and upload them to S3
        image_s3_urls = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                # Resolve the absolute URL of the image
                img_url = requests.compat.urljoin(url, src)

                # Extract the image file name
                img_name = os.path.basename(img_url)
                if not img_name:  # Handle cases where the path is empty
                    img_name = f"image_{uuid4().hex[:8]}.png"

                # Download the image
                try:
                    img_response = requests.get(img_url)
                    img_response.raise_for_status()

                    # Save the image temporarily
                    temp_image_path = f"temp_{uuid4().hex[:8]}_{img_name}"
                    with open(temp_image_path, "wb") as temp_file:
                        temp_file.write(img_response.content)

                    # Upload the image to S3
                    print(f"Uploading {img_name} to S3...")
                    image_s3_url = upload_file_to_s3(
                        temp_image_path,
                        f"scraped_websites/{unique_folder}/images",
                        "images",
                        metadata={
                            "original_url": url,
                            "upload_timestamp": timestamp,
                            "file_type": "image",
                            "unique_folder": unique_folder
                        }
                    )
                    image_s3_urls.append(image_s3_url)

                    # Update the image src in the HTML to the S3 URL
                    img["src"] = image_s3_url

                    # Clean up the temporary file
                    os.remove(temp_image_path)
                except Exception as e:
                    print(f"Failed to process image {img_url}: {e}")

        # Step 4: Convert the HTML to Markdown
        md = MarkItDown()
        temp_html_path = f"temp_{uuid4().hex[:8]}.html"
        temp_markdown_path = f"{uuid4().hex[:8]}.md"
        try:
            # Save the HTML to a temporary file for conversion
            with open(temp_html_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(str(soup))
            print(f"HTML content saved temporarily to {temp_html_path}")

            # Convert the HTML to Markdown
            result = md.convert(temp_html_path)
            markdown_content = result.text_content

            # Save the Markdown content temporarily
            with open(temp_markdown_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(markdown_content)
            print(f"Markdown content saved temporarily to {temp_markdown_path}")

            # Upload the Markdown file to S3
            print(f"Uploading Markdown to S3...")
            markdown_s3_url = upload_file_to_s3(
                temp_markdown_path,
                f"scraped_websites/{unique_folder}/markdown",
                "markdown",
                metadata={
                    "original_url": url,
                    "upload_timestamp": timestamp,
                    "file_type": "markdown",
                    "unique_folder": unique_folder
                }
            )
        finally:
            # Clean up temporary files
            if os.path.exists(temp_html_path):
                os.remove(temp_html_path)
            if os.path.exists(temp_markdown_path):
                os.remove(temp_markdown_path)

        # Step 5: Return the S3 URLs
        return {
            "markdown_s3_url": markdown_s3_url,
            "image_s3_urls": image_s3_urls,
            "unique_folder": unique_folder,
            "status": "success",
            "message": "Webpage scraped and uploaded to S3 successfully."
        }

    except Exception as e:
        print(f"Error scraping webpage: {e}")
        raise RuntimeError(f"Error scraping webpage: {str(e)}")
