import re


def find_images_in_text(text):
    matches = list(re.findall(r'https:[^"]+\.jpg', text))
    return matches


def replace_image_in_text(text, match, replacement):
    result = text.replace(match, replacement)
    return result
