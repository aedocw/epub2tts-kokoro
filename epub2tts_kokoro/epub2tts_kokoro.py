import os
import sys
# Automatically enable MPS fallback on Apple Silicon macOS
if sys.platform == 'darwin':
    os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
import argparse
import numpy as np
import re
import soundfile
import subprocess
import torch
import warnings
from tqdm import tqdm
from kokoro import KPipeline

from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
import soundfile as sf
from lxml import etree
from mutagen import mp4
import nltk
from nltk.tokenize import sent_tokenize
from PIL import Image
from pydub import AudioSegment
import zipfile


namespaces = {
   "calibre":"http://calibre.kovidgoyal.net/2009/metadata",
   "dc":"http://purl.org/dc/elements/1.1/",
   "dcterms":"http://purl.org/dc/terms/",
   "opf":"http://www.idpf.org/2007/opf",
   "u":"urn:oasis:names:tc:opendocument:xmlns:container",
   "xsi":"http://www.w3.org/2001/XMLSchema-instance",
}

warnings.filterwarnings("ignore", module="ebooklib.epub")

def ensure_punkt():
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab")

def chap2text_epub(chap):
    blacklist = [
        "[document]",
        "noscript",
        "header",
        "html",
        "meta",
        "head",
        "input",
        "script",
    ]
    paragraphs = []
    soup = BeautifulSoup(chap, "html.parser")

    # Extract chapter title (assuming it's in an <h1> tag)
    chapter_title = soup.find("h1")
    if chapter_title:
        chapter_title_text = chapter_title.text.strip()
    else:
        chapter_title_text = None

    # Always skip reading links that are just a number (footnotes)
    for a in soup.findAll("a", href=True):
        if not any(char.isalpha() for char in a.text):
            a.extract()

    # Always skip anything that starts with "<sup class=" and ends with "</sup>"
    for sup in soup.findAll("sup"):
        if sup.text.isdigit():
            sup.extract()

    chapter_paragraphs = soup.find_all("p")
    if len(chapter_paragraphs) == 0:
        print(f"Could not find any paragraph tags <p> in \"{chapter_title_text}\". Trying with <div>.")
        chapter_paragraphs = soup.find_all("div")

    for p in chapter_paragraphs:
        paragraph_text = "".join(p.strings).strip()
        paragraphs.append(paragraph_text)

    return chapter_title_text, paragraphs

def get_epub_cover(epub_path):
    try:
        with zipfile.ZipFile(epub_path) as z:
            t = etree.fromstring(z.read("META-INF/container.xml"))
            rootfile_path =  t.xpath("/u:container/u:rootfiles/u:rootfile",
                                        namespaces=namespaces)[0].get("full-path")

            t = etree.fromstring(z.read(rootfile_path))
            cover_meta = t.xpath("//opf:metadata/opf:meta[@name='cover']",
                                        namespaces=namespaces)
            if not cover_meta:
                print("No cover image found.")
                return None
            cover_id = cover_meta[0].get("content")

            cover_item = t.xpath("//opf:manifest/opf:item[@id='" + cover_id + "']",
                                            namespaces=namespaces)
            if not cover_item:
                print("No cover image found.")
                return None
            cover_href = cover_item[0].get("href")
            cover_path = os.path.join(os.path.dirname(rootfile_path), cover_href)
            if os.name == 'nt' and '\\' in cover_path:
                cover_path = cover_path.replace("\\", "/")
            return z.open(cover_path)
    except FileNotFoundError:
        print(f"Could not get cover image of {epub_path}")

def export(book, sourcefile):
    book_contents = []
    cover_image = get_epub_cover(sourcefile)
    image_path = None

    if cover_image is not None:
        image = Image.open(cover_image)
        image_filename = sourcefile.replace(".epub", ".png")
        image_path = os.path.join(image_filename)
        image.save(image_path)
        print(f"Cover image saved to {image_path}")

    spine_ids = []
    for spine_tuple in book.spine:
        if spine_tuple[1] == 'yes': # if item in spine is linear
            spine_ids.append(spine_tuple[0])

    items = {}
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            items[item.get_id()] = item

    for id in spine_ids:
        item = items.get(id, None)
        if item is None:
            continue
        chapter_title, chapter_paragraphs = chap2text_epub(item.get_content())
        book_contents.append({"title": chapter_title, "paragraphs": chapter_paragraphs})
    outfile = sourcefile.replace(".epub", ".txt")
    check_for_file(outfile)
    print(f"Exporting {sourcefile} to {outfile}")
    author = book.get_metadata("DC", "creator")[0][0]
    booktitle = book.get_metadata("DC", "title")[0][0]

    with open(outfile, "w", encoding='utf-8') as file:
        file.write(f"Title: {booktitle}\n")
        file.write(f"Author: {author}\n\n")

        file.write(f"# Title\n")
        file.write(f"{booktitle}, by {author}\n\n")
        for i, chapter in enumerate(book_contents, start=1):
            if chapter["paragraphs"] == [] or chapter["paragraphs"] == ['']:
                continue
            else:
                if chapter["title"] == None:
                    file.write(f"# Part {i}\n")
                else:
                    file.write(f"# {chapter['title']}\n\n")
                for paragraph in chapter["paragraphs"]:
                    clean = re.sub(r'[\s\n]+', ' ', paragraph)
                    clean = re.sub(r'[“”]', '"', clean)  # Curly double quotes to standard double quotes
                    clean = re.sub(r'[‘’]', "'", clean)  # Curly single quotes to standard single quotes
                    clean = re.sub(r'--', ', ', clean)
                    file.write(f"{clean}\n\n")

def get_book(sourcefile):
    book_contents = []
    book_title = sourcefile
    book_author = "Unknown"
    chapter_titles = []

    with open(sourcefile, "r", encoding="utf-8") as file:
        current_chapter = {"title": "blank", "paragraphs": []}
        initialized_first_chapter = False
        lines_skipped = 0
        for line in file:

            if lines_skipped < 2 and (line.startswith("Title") or line.startswith("Author")):
                lines_skipped += 1
                if line.startswith('Title: '):
                    book_title = line.replace('Title: ', '').strip()
                elif line.startswith('Author: '):
                    book_author = line.replace('Author: ', '').strip()
                continue

            line = line.strip()
            if line.startswith("#"):
                if current_chapter["paragraphs"] or not initialized_first_chapter:
                    if initialized_first_chapter:
                        book_contents.append(current_chapter)
                    current_chapter = {"title": None, "paragraphs": []}
                    initialized_first_chapter = True
                chapter_title = line[1:].strip()
                if any(c.isalnum() for c in chapter_title):
                    current_chapter["title"] = chapter_title
                    chapter_titles.append(current_chapter["title"])
                else:
                    current_chapter["title"] = "blank"
                    chapter_titles.append("blank")
            elif line:
                if not initialized_first_chapter:
                    chapter_titles.append("blank")
                    initialized_first_chapter = True
                if any(char.isalnum() for char in line):
                    sentences = sent_tokenize(line)
                    cleaned_sentences = [s for s in sentences if any(char.isalnum() for char in s)]
                    line = ' '.join(cleaned_sentences)
                    current_chapter["paragraphs"].append(line)

        # Append the last chapter if it contains any paragraphs.
        if current_chapter["paragraphs"]:
            book_contents.append(current_chapter)

    return book_contents, book_title, book_author, chapter_titles

def sort_key(s):
    # extract number from the string
    return int(re.findall(r'\d+', s)[0])

def check_for_file(filename):
    if os.path.isfile(filename):
        print(f"The file '{filename}' already exists.")
        overwrite = input("Do you want to overwrite the file? (y/n): ")
        if overwrite.lower() != 'y':
            print("Exiting without overwriting the file.")
            sys.exit()
        else:
            os.remove(filename)

def append_silence(tempfile, duration=1200):
    audio = AudioSegment.from_file(tempfile)
    # Create a silence segment
    silence = AudioSegment.silent(duration)
    # Append the silence segment to the audio
    combined = audio + silence
    # Save the combined audio back to file
    combined.export(tempfile, format="flac")

def break_long_sentence(sentence, max_length=200):
    # Split sentence based on commas
    comma_segments = sentence.split(',')
    segments = []
    current_segment = ""
    for segment in comma_segments:
        # Check if adding the next segment exceeds max_length
        temp_segment = current_segment + ("," if current_segment else "") + segment
        if len(temp_segment) > max_length:
            # Add the current segment to the list and reset it
            if current_segment:
                segments.append(current_segment)
            # Start a new segment with the current part
            current_segment = segment.strip()
        else:
            # Continue building the current segment
            current_segment = temp_segment.strip()
    # Don't forget to add the last segment if it exists
    if current_segment:
        segments.append(current_segment)
    return segments

def process_large_text(line):
    # Tokenize the text into sentences
    sentences = sent_tokenize(line)
    # Initialize a list to store processed sentences
    results = []
    
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        word_count = len(sentence.split())
        
        # Combine with the next sentence if this one has fewer than 8 words
        if word_count < 8 and i + 1 < len(sentences):
            # Combine the current and next sentence
            sentence = sentence + ' ' + sentences[i + 1]
            i += 1  # Skip the next sentence since it's already combined

        if len(sentence) > 500:
            # Break the long sentences into smaller parts using commas
            results.extend(break_long_sentence(sentence, max_length=350))
        else:
            results.append(sentence)
        
        i += 1  # Move to the next sentence
    
    # Before returning, combine last elements if they are too short
    if results and len(results[-1].split()) < 8:
        if len(results) > 1:
            # Combine the last two sentences if they are both short
            results[-2] += ' ' + results[-1]
            results.pop()
            
    return results

def conditional_sentence_case(sent):
    # Split the sentence into words
    words = sent.split()

    # Check if the first two words are uppercase
    if len(words) >= 2 and words[0].isupper() and words[1].isupper():
        # Convert the entire sentence to lowercase, then capitalize the first letter
        sent = sent.lower().capitalize()

    return sent

def kokoro_read(paragraph, speaker, filename, pipeline, speed):
    audio_segments = []
    sentences = process_large_text(paragraph)
    for sent in sentences:
        sent = conditional_sentence_case(sent.strip())
        for gs, ps, audio in pipeline(sent, voice=speaker, speed=1.3, split_pattern=r'\n\n\n'):
            audio_segments.append(audio)

    final_audio = np.concatenate(audio_segments)
    soundfile.write(filename, final_audio, 24000)

def read_book(book_contents, speaker, paragraphpause, speed, notitles):
    current_device_name = torch.get_default_device() if torch.get_default_device() else 'cpu'
    current_device = torch.device(current_device_name)
    print(f"Attempting to use device: {current_device}")

    pipeline = KPipeline(lang_code=speaker[0])

    # Explicitly move the model to the current default device (e.g., 'xpu')
    if hasattr(pipeline, 'model') and pipeline.model is not None:
        try:
            pipeline.model.to(current_device)
            print(f"Kokoro model explicitly moved to {current_device}")
        except Exception as e:
            print(f"Error moving Kokoro model to {current_device}: {e}")
    else:
        print("Warning: KPipeline does not have a 'model' attribute or model is None.")

    segments = []
    for i, chapter in enumerate(book_contents, start=1):
        files = []
        partname = f"part{i}.flac"
        print(f"\n\n")

        if os.path.isfile(partname):
            print(f"{partname} exists, skipping to next chapter")
            segments.append(partname)
        else:
            print(f"Chapter: {chapter['title']}\n")
            print(f"Section name: \"{chapter['title']}\"")
            if chapter["title"] == "":
                chapter["title"] = "blank"
            if chapter["title"] != "Title" and notitles != True:
                chapter['paragraphs'][0] = chapter['title'] + ". " + chapter['paragraphs'][0]
            for pindex, paragraph in enumerate(
                tqdm(chapter["paragraphs"], desc=f"Generating audio files: ",unit='pg')
            ):
                ptemp = f"pgraphs{pindex}.flac"
                if os.path.isfile(ptemp):
                    print(f"{ptemp} exists, skipping to next paragraph")
                else:
                    #sentences = sent_tokenize(paragraph)
                    filenames = ["sntnc1.wav"]
                    kokoro_read(paragraph, speaker, "sntnc1.wav", pipeline, speed)                    
                    append_silence("sntnc1.wav", paragraphpause)
                    # combine sentences in paragraph
                    sorted_files = sorted(filenames, key=sort_key)
                    if os.path.exists("sntnc0.wav"):
                        sorted_files.insert(0, "sntnc0.wav")
                    combined = AudioSegment.empty()
                    for file in sorted_files:
                        combined += AudioSegment.from_file(file)
                    combined.export(ptemp, format="flac")
                    for file in sorted_files:
                        os.remove(file)
                files.append(ptemp)
            # combine paragraphs into chapter
            append_silence(files[-1], 2000)
            combined = AudioSegment.empty()
            for file in files:
                combined += AudioSegment.from_file(file)
            combined.export(partname, format="flac")
            for file in files:
                os.remove(file)
            segments.append(partname)
    return segments

def generate_metadata(files, author, title, chapter_titles):
    chap = 0
    start_time = 0
    with open("FFMETADATAFILE", "w") as file:
        file.write(";FFMETADATA1\n")
        file.write(f"ARTIST={author}\n")
        file.write(f"ALBUM={title}\n")
        file.write(f"TITLE={title}\n")
        file.write("DESCRIPTION=Made with https://github.com/aedocw/epub2tts-kokoro\n")
        for file_name in files:
            duration = get_duration(file_name)
            file.write("[CHAPTER]\n")
            file.write("TIMEBASE=1/1000\n")
            file.write(f"START={start_time}\n")
            file.write(f"END={start_time + duration}\n")
            file.write(f"title={chapter_titles[chap]}\n")
            chap += 1
            start_time += duration

def get_duration(file_path):
    audio = AudioSegment.from_file(file_path)
    duration_milliseconds = len(audio)
    return duration_milliseconds

def make_m4b(files, sourcefile, speaker):
    filelist = "filelist.txt"
    basefile = sourcefile.replace(".txt", "")
    outputm4a = f"{basefile} ({speaker}).m4a"
    outputm4b = f"{basefile} ({speaker}).m4b"
    with open(filelist, "w") as f:
        for filename in files:
            filename = filename.replace("'", "'\\''")
            f.write(f"file '{filename}'\n")
    ffmpeg_command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        filelist,
        "-codec:a",
        "flac",
        "-f",
        "mp4",
        "-strict",
        "-2",
        outputm4a,
    ]
    subprocess.run(ffmpeg_command)
    ffmpeg_command = [
        "ffmpeg",
        "-i",
        outputm4a,
        "-i",
        "FFMETADATAFILE",
        "-map_metadata",
        "1",
        "-codec",
        "aac",
        outputm4b,
    ]
    subprocess.run(ffmpeg_command)
    os.remove(filelist)
    os.remove("FFMETADATAFILE")
    os.remove(outputm4a)
    for f in files:
        os.remove(f)
    return outputm4b

def add_cover(cover_img, filename):
    try:
        if os.path.isfile(cover_img):
            m4b = mp4.MP4(filename)
            cover_image = open(cover_img, "rb").read()
            m4b["covr"] = [mp4.MP4Cover(cover_image)]
            m4b.save()
        else:
            print(f"Cover image {cover_img} not found")
    except:
        print(f"Cover image {cover_img} not found")

def main():
     # Check for GPU
    if torch.cuda.is_available():
        print('Nvidia GPU available. Setting as default device.')
        torch.set_default_device('cuda')
    elif torch.xpu.is_available():
        print('Intel XPU (GPU) available. Setting as default device.')
        torch.set_default_device('xpu')
    elif torch.backends.mps.is_available():
        print('Apple MPS GPU available. Setting as default device.')
        torch.set_default_device('mps')
    elif torch.backends.rocm.is_available():
        print('AMD ROCm GPU available. Setting as default device.')
        torch.set_default_device('rocm')
    else:
        print('No GPU available. Using CPU.')
        torch.set_default_device('cpu')
        
    parser = argparse.ArgumentParser(
        prog="epub2tts-kokoro",
        description="Read a text file to audiobook format",
    )
    parser.add_argument("sourcefile", type=str, help="The epub or text file to process")
    parser.add_argument(
        "--speaker",
        type=str,
        nargs="?",
        const="af_heart",
        default="af_heart",
        help="Speaker to use (ex af_heart)",
    )
    parser.add_argument(
        "--cover",
        type=str,
        help="jpg image to use for cover",
    )
    parser.add_argument(
        "--paragraphpause",
        type=int,
        default=600,
        help="duration of pause after paragraph, in milliseconds (default: 600)"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.3,
        help="reading speed (default: 1.3)"
    )
    parser.add_argument(
        "--notitles",
        action="store_true",
        help="Do not read chapter titles"
    )

    args = parser.parse_args()
    print(args)

    ensure_punkt()

    #If we get an epub, export that to txt file, then exit
    if args.sourcefile.endswith(".epub"):
        book = epub.read_epub(args.sourcefile)
        export(book, args.sourcefile)
        exit()

   


    book_contents, book_title, book_author, chapter_titles = get_book(args.sourcefile)
    files = read_book(book_contents, args.speaker, args.paragraphpause, args.speed, args.notitles)
    generate_metadata(files, book_author, book_title, chapter_titles)
    m4bfilename = make_m4b(files, args.sourcefile, args.speaker)
    add_cover(args.cover, m4bfilename)
    
if __name__ == "__main__":
    main()
