import os
import json
import logging
import zipfile
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import ExtractRenditionsElementType

from storage.s3_utils import upload_file_to_s3  # Import S3 utilities

logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def process_pdf_enterprise(file_content: bytes) -> dict:
    """
    Process a PDF file using Adobe PDF Services to extract text, tables, and images, and upload them to S3.
    
    Args:
        file_content (bytes): The content of the uploaded PDF file.
    
    Returns:
        dict: A dictionary containing S3 URLs for the extracted markdown, images, and processing status.
    """
    try:
        logging.debug("Starting PDF extraction using Adobe PDF Services.")
        
        # Validate PDF file
        if not file_content.startswith(b"%PDF"):
            logging.error("The uploaded file is not a valid PDF.")
            raise ValueError("The provided file is not a valid PDF.")
        
        # Create unique folder name for S3
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"pdf_{timestamp}_{uuid4().hex[:8]}"
        logging.debug(f"Unique S3 folder: {unique_folder}")
        
        # Save PDF temporarily
        temp_pdf_path = Path(f"temp_{uuid4().hex[:8]}.pdf")
        with open(temp_pdf_path, "wb") as temp_file:
            temp_file.write(file_content)
        logging.debug(f"Temporary PDF saved at {temp_pdf_path}.")
        
        # Authenticate Adobe PDF Services
        credentials = ServicePrincipalCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        pdf_services = PDFServices(credentials=credentials)
        
        # Upload PDF
        input_asset = pdf_services.upload(input_stream=file_content, mime_type=PDFServicesMediaType.PDF)
        
        # Set extraction parameters
        extract_pdf_params = ExtractPDFParams(
            elements_to_extract=[ExtractElementType.TEXT, ExtractElementType.TABLES],
            elements_to_extract_renditions=[ExtractRenditionsElementType.FIGURES, ExtractRenditionsElementType.TABLES]
        )
        
        # Submit extraction job
        extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
        location = pdf_services.submit(extract_pdf_job)
        pdf_services_response = pdf_services.get_job_result(location, ExtractPDFResult)
        result_asset: CloudAsset = pdf_services_response.get_result().get_resource()
        stream_asset: StreamAsset = pdf_services.get_content(result_asset)
        
        # Save extracted content as zip
        temp_zip_path = temp_pdf_path.with_suffix(".zip")
        with open(temp_zip_path, "wb") as zip_file:
            zip_file.write(stream_asset.get_input_stream())
        logging.debug(f"Extracted content saved to {temp_zip_path}.")
        
        # Process extracted content
        markdown_output, image_paths = extract_content(temp_zip_path)
        
        # Save Markdown file
        temp_markdown_path = temp_pdf_path.with_suffix(".md")
        with open(temp_markdown_path, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_output)
        logging.debug(f"Markdown content saved to {temp_markdown_path}.")
        
        # Upload Markdown to S3
        markdown_s3_url = upload_file_to_s3(
            temp_markdown_path,
            f"processed_pdfs/enterprise/{unique_folder}/markdown",
            "markdown",
            metadata={
                "upload_timestamp": timestamp,
                "file_type": "markdown",
                "unique_folder": unique_folder
            }
        )
        logging.debug(f"Markdown uploaded to S3: {markdown_s3_url}")
        
        # Upload images to S3
        image_s3_urls = []
        for image_path in image_paths:
            image_s3_url = upload_file_to_s3(
                image_path,
                f"processed_pdfs/enterprise/{unique_folder}/images",
                "images",
                metadata={
                    "upload_timestamp": timestamp,
                    "file_type": "image",
                    "unique_folder": unique_folder
                }
            )
            image_s3_urls.append(image_s3_url)
            logging.debug(f"Image uploaded to S3: {image_s3_url}")
            os.remove(image_path)
        
        # Clean up temporary files
        os.remove(temp_pdf_path)
        os.remove(temp_zip_path)
        os.remove(temp_markdown_path)
        logging.debug("Temporary files deleted.")
        
        return {
            "markdown_s3_url": markdown_s3_url,
            "image_s3_urls": image_s3_urls,
            "unique_folder": unique_folder,
            "status": "success",
            "message": "PDF processed and uploaded to S3 successfully"
        }
    
    except (ServiceApiException, ServiceUsageException, SdkException, Exception) as e:
        logging.error(f"Error processing PDF: {e}", exc_info=True)
        raise RuntimeError(f"Error processing PDF: {str(e)}")


def extract_content(zip_file_path) -> tuple:
    """Extracts text, tables, and figures from the zip file and formats them as Markdown."""
    markdown_output = []
    image_paths = []
    
    with zipfile.ZipFile(zip_file_path, 'r') as archive:
        with archive.open('structuredData.json') as json_entry:
            data = json.load(json_entry)
            markdown_output.append(process_text(data))
        
        for file in archive.namelist():
            if file.startswith(('tables/', 'figures/')) and file.endswith(('.png', '.jpg', '.jpeg')):
                image_data = archive.read(file)
                image_name = os.path.basename(file)
                temp_image_path = Path(image_name)
                with open(temp_image_path, 'wb') as image_file:
                    image_file.write(image_data)
                image_paths.append(temp_image_path)
    
    return "\n\n".join(markdown_output), image_paths


def process_text(data) -> str:
    """Processes extracted text elements and formats them as Markdown."""
    return "\n\n".join([element["Text"] for element in data.get("elements", []) if "Text" in element])