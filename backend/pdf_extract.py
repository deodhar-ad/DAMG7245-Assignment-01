import os
from uuid import uuid4
from datetime import datetime
import logging

from pathlib import Path
from docling_core.types.doc import ImageRefMode, PictureItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from storage.s3_utils import upload_file_to_s3  # Import S3 utilities

IMAGE_RESOLUTION_SCALE = 2.0


def process_pdf(file_content: bytes) -> dict:
    """
    Process a PDF file to extract markdown content and images, and upload them to S3.

    Args:
        file_content (bytes): The content of the uploaded PDF file.

    Returns:
        dict: A dictionary with S3 URLs for the markdown file, extracted images, and status information.
    """
    logging.basicConfig(level=logging.DEBUG)

    try:
        logging.debug("Starting the PDF processing function.")

        # Step 1: Validate the PDF file
        if not file_content.startswith(b"%PDF"):
            logging.error("The uploaded file is not a valid PDF.")
            raise ValueError("The provided file is not a valid PDF.")
        logging.debug("PDF file content validated.")

        # Step 2: Create a unique folder name for this processing task
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"pdf_{timestamp}_{uuid4().hex[:8]}"  # Unique folder name
        logging.debug(f"Unique S3 folder for this PDF: {unique_folder}")

        # Step 3: Write the PDF content to a temporary file
        temp_pdf_path = Path(f"temp_{uuid4().hex[:8]}.pdf")
        with open(temp_pdf_path, "wb") as temp_file:
            temp_file.write(file_content)
        logging.debug(f"Temporary PDF saved to {temp_pdf_path}.")

        # Step 4: Configure pipeline options for image extraction
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True
        pipeline_options.do_table_structure = True
        logging.debug(f"Pipeline options configured: {pipeline_options}")

        # Step 5: Initialize DocumentConverter and convert the PDF
        logging.debug("Initializing DocumentConverter...")
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        conv_res = doc_converter.convert(Path(temp_pdf_path))
        logging.debug("PDF conversion completed successfully.")

        # Step 6: Extract and upload images to S3
        logging.debug("Extracting images from PDF...")
        image_s3_urls = []
        picture_counter = 0
        for element, _level in conv_res.document.iterate_items():
            if isinstance(element, PictureItem):
                picture_counter += 1
                temp_image_path = f"{Path(temp_pdf_path).stem}-picture-{picture_counter}.png"
                with open(temp_image_path, "wb") as fp:
                    element.get_image(conv_res.document).save(fp, "PNG")
                logging.debug(f"Image saved temporarily: {temp_image_path}")

                # Upload the image to S3
                image_s3_url = upload_file_to_s3(
                    temp_image_path,
                    f"processed_pdfs/opensource/{unique_folder}/images",
                    "images",
                    metadata={
                        "upload_timestamp": timestamp,
                        "file_type": "image",
                        "unique_folder": unique_folder
                    }
                )
                image_s3_urls.append(image_s3_url)
                logging.debug(f"Image uploaded to S3: {image_s3_url}")

                # Clean up the temporary image file
                os.remove(temp_image_path)
                logging.debug(f"Temporary image file deleted: {temp_image_path}")

        # Step 7: Save and upload Markdown content to S3
        logging.debug("Saving Markdown content...")
        temp_markdown_path = temp_pdf_path.with_suffix("").with_name(f"temp_{uuid4().hex[:8]}_with_images.md")
        conv_res.document.save_as_markdown(temp_markdown_path, image_mode=ImageRefMode.REFERENCED)
        logging.debug(f"Markdown content saved temporarily: {temp_markdown_path}")

        # Upload Markdown to S3
        markdown_s3_url = upload_file_to_s3(
            temp_markdown_path,
            f"processed_pdfs/opensource/{unique_folder}/markdown",
            "markdown",
            metadata={
                "upload_timestamp": timestamp,
                "file_type": "markdown",
                "unique_folder": unique_folder
            }
        )
        logging.debug(f"Markdown uploaded to S3: {markdown_s3_url}")

        # Step 8: Clean up temporary files
        os.remove(temp_pdf_path)
        os.remove(temp_markdown_path)
        logging.debug("Temporary files cleaned up.")

        # Step 9: Return success response
        logging.debug("PDF processing completed successfully.")
        return {
            "markdown_s3_url": markdown_s3_url,
            "image_s3_urls": image_s3_urls,
            "unique_folder": unique_folder,
            "status": "success",
            "message": "PDF processed and uploaded to S3 successfully"
        }

    except Exception as e:
        logging.error(f"Error processing PDF: {e}", exc_info=True)
        raise RuntimeError(f"Error processing PDF: {str(e)}")
