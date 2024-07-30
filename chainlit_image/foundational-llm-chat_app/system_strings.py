from config import MAX_CHARACHERS, MAX_CONTENT_SIZE_MB

suported_file_string = "The tool accepts PNG, JPG, GIF, WEBP images and doc, docx, csv, xls, xlsx, markdown, plain text, html"

if MAX_CHARACHERS:
    supported_text_lenght = f"The tool accepts text up to {MAX_CHARACHERS} charchers."
    suported_file_string += supported_text_lenght
if MAX_CONTENT_SIZE_MB:
    suported_file_string += f"The maximum size of a single file is {MAX_CONTENT_SIZE_MB}MB."