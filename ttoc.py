import os
import toc
import time
import shutil
import markdown2
import subprocess
from progress import chapters

md_dir = r"C:\Users\whip\tdr"
html_dir = r"C:\Users\whip\tdr-book-html"
top_images_dir = os.path.join(html_dir, 'images')
pdf_dir = r"C:\Users\whip\tdr-book-pdf"
md_publish_dir = r"C:\Users\whip\tdr-md-publish"

PUBLISH = True

full_html = ""
full_html_path = os.path.join(html_dir, 'full_book.html')

def get_file_list(ignore_images = False):
    path_list = []
    chapter_number = 0
    for part_name, chapter_names in chapters.items():
        part_path = os.path.join(md_dir, part_name)
        for a, b, chapter_name in chapter_names:
            if not is_chapter_name(chapter_name, part_path):
                chapter_path = os.path.join(part_path, chapter_name)
            else:
                chapter_path = os.path.join(part_path, "%02d - %s" % (chapter_number, chapter_name))
                chapter_number += 1
            if not os.path.exists(chapter_path):
                print("Chapter path does not exist: %s" % chapter_path)
                breakpoint()
            path_list.append(chapter_path)
            
        if not ignore_images:
            images_path = os.path.join(part_path, 'images')
            if os.path.exists(images_path):
                path_list.extend([os.path.join(images_path, x) for x in os.listdir(images_path)])
    return path_list


def get_md(md_path):
    md_contents = open(md_path, 'r', encoding='utf-8').read()
    if not PUBLISH:
        return md_contents
    
    md_contents = md_contents.split("### References")[0]
    if "<toc/>" in md_contents:
        a, b, c = md_contents.split("<toc/>")
        md_contents = a + c
    return md_contents


def transform(file_list):
    mdConverter = markdown2.Markdown()
    if os.path.exists(html_dir):
        shutil.rmtree(html_dir)
    os.mkdir(html_dir)
    if os.path.exists(pdf_dir):
        shutil.rmtree(pdf_dir)
    os.mkdir(pdf_dir)
    if os.path.exists(md_publish_dir):
        shutil.rmtree(md_publish_dir)
    os.mkdir(md_publish_dir)
    for file_path in file_list:
        if not os.path.exists(file_path):
            print("not found: %s" % file_path)
            breakpoint()
            a = 4

        if 'images' in file_path:
            html_path = file_path.replace(md_dir, html_dir)
            if not os.path.exists(os.path.dirname(html_path)):
                os.mkdir(os.path.dirname(html_path))
            # also put image in top-level images dir
            if not os.path.exists(top_images_dir):
                os.mkdir(top_images_dir)
            top_img_dir_dest_path = os.path.join(top_images_dir, os.path.basename(file_path))
            shutil.copy(file_path, top_img_dir_dest_path)
            shutil.copy(file_path, html_path)
            continue
        else:
            md_path = file_path
        
        html_path = md_path.replace(md_dir, html_dir)
        html_path = html_path.replace(".md", ".html")
        pdf_path = md_path.replace(md_dir, pdf_dir)
        pdf_path = pdf_path.replace(".md", ".pdf")
        md_publish_path = md_path.replace(md_dir, md_publish_dir)
        if not os.path.exists(os.path.dirname(html_path)):
            os.mkdir(os.path.dirname(html_path))
        if not os.path.exists(os.path.dirname(md_publish_path)):
            os.mkdir(os.path.dirname(md_publish_path))
        if not os.path.exists(os.path.dirname(pdf_path)):
            os.mkdir(os.path.dirname(pdf_path))
        md_contents = get_md(md_path)
        html = mdConverter.convert(md_contents)
        open(html_path, 'w', encoding='utf-8').write(html)
        open(full_html_path, 'a', encoding='utf-8').write(html)
        open(md_publish_path, 'w', encoding='utf-8').write(md_contents)
        
def is_chapter_name(chapter_name, directory):
  return ("Part Introduction" not in chapter_name and
          "preface material" not in directory.lower() and 
          "part 4" not in directory.lower())


def main():
    file_list = get_file_list()
    for file_path in file_list:
        if '.md' in file_path:
            toc.insert_and_return_toc(file_path)
    transform(file_list)

if __name__ == '__main__':
    start_time = time.time()
    try:
        main()
    except Exception as exc:
        print("Error: %s" % exc)
        breakpoint()
    print("%ss" % round(time.time()-start_time, 2))
