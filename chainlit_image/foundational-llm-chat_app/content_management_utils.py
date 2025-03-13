from config import MAX_CHARACHERS, MAX_CONTENT_SIZE_MB, bedrock_models
from PIL import Image
import os
import logging
import chainlit as cl

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

img_supported = [bedrock_models[key]["id"] for key in bedrock_models.keys() if "vision" in bedrock_models[key] and bedrock_models[key]["vision"] == True]
doc_supported = [bedrock_models[key]["id"] for key in bedrock_models.keys() if "document" in bedrock_models[key] and bedrock_models[key]["document"] == True]
tool_supported = [bedrock_models[key]["id"] for key in bedrock_models.keys() if "tool" in bedrock_models[key] and bedrock_models[key]["tool"] == True]

# check if the images are supported images and limit the size
# if MAX_CONTENT_SIZE_MB is defined
def verify_image_content(images):
    if len(images) == 0 or images is None:
        return True
    for image in images:
        if not os.path.isfile(image["path"]):
            return False
        else:
            img = Image.open(image["path"])
            try:
                img.verify()
                if img.format not in ["PNG", "JPEG", "GIF", "WEBP"]:
                    return False
                size = os.stat(image["path"]).st_size / (1024 * 1024)
                if MAX_CONTENT_SIZE_MB and size > MAX_CONTENT_SIZE_MB:
                    return False
            except Exception:
                return False
    return True

def verify_doc_content(docs):
    if len(docs) == 0 or docs is None:
        return True
    for doc in docs:
        if not os.path.isfile(doc["path"]):
            return False
        else:
            try:
                # if you want to be sure you can add a check about the document itself. You also need to check the document name since
                # per bedrock converse api docs for document chat the name can be use for prompt injection
                size = os.stat(doc["path"]).st_size / (1024 * 1024)
                if MAX_CONTENT_SIZE_MB and size > MAX_CONTENT_SIZE_MB:
                    return False
            except Exception:
                return False
    return True

# check if the text is defined and if MAX_CHARACHERS is defined the len of the text
def verify__text_content(text_content):
    if text_content is None or text_content == "":
        return False
    if MAX_CHARACHERS: 
        if len(text_content) > MAX_CHARACHERS:
            return False
    return True

# validate message contents
def verify_content(text_content, images, docs):
    return verify_image_content(images) and verify__text_content(text_content) and verify_doc_content(docs)

def what_supports(model_id):
    return (model_id in img_supported, model_id in doc_supported, model_id in tool_supported)

def split_message_contents(message, model_id):
    # Claude https://docs.anthropic.com/claude/docs/vision#getting-started support these
    # if you want to allow more contents you need to modify also ./.chainlit/congif.toml line 32
    images = []
    docs = []
    other_files = []
    img_supported, doc_supported, _ = what_supports(model_id)
    if message.elements:
        for elem in message.elements:
            if img_supported and elem.mime in ["image/jpeg", "image/gif", "image/png","image/webp"]:
                images.append({"name": elem.name, "path": elem.path, "mime": elem.mime})
            elif doc_supported and elem.mime in ["application/pdf",
                             "text/csv",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             "application/vnd.ms-excel",
                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             "application/msword",
                             "text/plain",
                             "text/html",
                             "text/markdown"
                             ]:
                docs.append({"name": elem.name, "mime": elem.mime, "path": elem.path})
            else:
                other_files.append({"name": elem.name, "mime": elem.mime, "path": elem.path})
    cl.user_session.set(
            "directory_paths",
            set([os.path.dirname(c["path"]) for c in (images + other_files)])
    )
    return images, docs, other_files

# delete the temp folder with uploaded files
def delete_contents(contents, delete_directory = False):
    if contents is None or len(contents) == 0:
        return
    for c in contents:
        logger.info("removing " + c["path"])
        # If the file exists, delete it.
        if os.path.isfile(c["path"]):
            os.remove(c["path"])
        else:
            # If it fails, inform the user.
            logger.error("Error: %s file not found" % c["path"])

    # Remove empty directories
    # We delete the directory on chat end
    if delete_directory:
        # Get the set of unique directory paths from the file paths
        directory_paths = cl.user_session.get("directory_paths")
        for directory_path in directory_paths:
            try:
                os.rmdir(directory_path)
                logger.info(f"Removed empty directory: {directory_path}")
            except OSError as e:
                logger.error(f"Error: {e.strerror} ({e.filename})")
