import re
from datetime import datetime, timezone

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

def extract_and_process_prompt(prompt_data):
    # Extract the prompt text
    prompt_text = prompt_data['variants'][0]['templateConfiguration']['text']['text']
    
    # Extract input variables
    input_variables = prompt_data['variants'][0]['templateConfiguration']['text']['inputVariables']
    
    # Get current date and time
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")  # Current date in YYYY-MM-DD format
    utc_time = now.strftime("%Y-%m-%d %H:%M:%S UTC")  # Current time in YYYY-MM-DD HH:MM:SS UTC format
    
    # Process variables
    for var in input_variables:
        var_name = var['name']
        if var_name == 'TODAY':
            prompt_text = prompt_text.replace('{{TODAY}}', today)
        elif var_name == 'UTC_TIME':
            prompt_text = prompt_text.replace('{{UTC_TIME}}', utc_time)
        elif var_name == 'AI':
            # For now, we'll leave {{AI}} as is, but you can replace it if needed
            pass
        else:
            # For other variables, you might want to prompt the user or use a default value
            replacement = input(f"Please provide a value for {var_name}: ")
            prompt_text = prompt_text.replace(f'{{{{{var_name}}}}}', replacement)
    
    return prompt_text