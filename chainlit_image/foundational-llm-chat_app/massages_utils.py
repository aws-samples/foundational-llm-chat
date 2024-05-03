import base64

# create the content of the message body
def create_content(text, images):
    content = []
    if images:
        for image in images:
            content.append(image)
    if text:
        content.append({"type": "text", "text": text})
    return content

# create the content of the message body if there are images
def create_image_content(images_dict):
    images = []
    for image in images_dict:
        with open(image["path"], "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            images.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image["mime"],
                    "data": encoded_string.decode("utf-8")
                }
            })
    return images
