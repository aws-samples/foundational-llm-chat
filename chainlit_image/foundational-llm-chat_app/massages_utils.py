import base64
import os
import re

def sanitize_filename(filename):
    # Remove consecutive whitespace characters
    filename = re.sub(r'\s+', ' ', filename)

    # Replace consecutive hyphens with a single hyphen
    filename = re.sub(r'-+', '-', filename)

    # Replace any remaining invalid characters with an underscore
    filename = re.sub(r'[^a-zA-Z0-9\s\-\(\)\[\]]', '_', filename)

    return filename


# create the content of the message body
def create_content(text, images, docs):
    content = []
    if images:
        for image in images:
            content.append(image)
    if docs:
        for doc in docs:
            content.append(doc)
    if text:
        content.append({"text": text})
    return content

def get_file_extension(file_type):
    file_extension = file_type.split("/")[1]
    if file_extension == "jpg":
        file_extension = "jpeg"
    if file_extension == "vnd.ms-excel":
        file_extension = "xls"
    if file_extension == "vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        file_extension = "xlsx"
    if file_extension == "vnd.openxmlformats-officedocument.wordprocessingml.document":
        file_extension = "docx"
    if file_extension == "msword":
        file_extension = "doc"
    if file_extension == "plain":
        file_extension = "txt"
    if file_extension == "markdown":
        file_extension = "md"
    return file_extension


# create the content of the message body if there are images
def create_image_content(images_dict):
    images = []
    for image in images_dict:
        with open(image["path"], "rb") as image_file:
            im = image_file.read()
            images.append({
                "image": {
                    "format": get_file_extension(image["mime"]),
                    "source": {
                            "bytes": im
                        }
                    }
                })
    return images

# create the content of the message body if there are images
def create_doc_content(docs_dict):
    docs = []
    for doc in docs_dict:
        print(doc)
        with open(doc["path"], "rb") as doc_file:
            d = doc_file.read()
            docs.append({
                "document": {
                    "name": sanitize_filename(doc["name"]),
                    "format": get_file_extension(doc["mime"]),
                    "source": {
                            "bytes": d
                        }
                    }
                })
    return docs

