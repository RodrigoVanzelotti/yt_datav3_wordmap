from collections import Counter
import re

def count_word_occurrences(text):
    # Split the text into words using regular expressions
    words = re.findall(r'\w+', text.lower())

    # Count the occurrences of each word
    word_counts = Counter(words)

    return word_counts

def save_string_to_txt(string, filename='youtube_string.txt'):
    with open(filename, 'w') as file:
        file.write(string)