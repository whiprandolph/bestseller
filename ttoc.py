import os
import toc
import shutil
import markdown2
import subprocess
from progress import chapters

md_dir = r"C:\Users\whip\short-odoc"
html_dir = r"C:\Users\whip\short-odoc-html"
pdf_dir = r"C:\Users\whip\short-odoc-pdf"
md_publish_dir = r"C:\Users\whip\short-odoc-md-publish"

PUBLISH = True


def get_chapter_path_list():
    path_list = []
    for part_name, chapter_names in chapters.items():
        part_path = os.path.join(md_dir, part_name)
        for idx, (a, b, chapter_name) in enumerate(chapter_names):
            idx+=1
            chapter_path = os.path.join(part_path, "%02d - %s" % (idx, chapter_name))
            if not os.path.exists(chapter_path):
                print("Chapter path does not exist: %s" % chapter_path)
                breakpoint()
            path_list.append(chapter_path)
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


def transform(chapter_list):
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
    for md_path in chapter_list:
        if not os.path.exists(md_path):
            print("not found: %s" % md_path)
            breakpoint()
            a = 4
        html_path = md_path.replace(md_dir, html_dir)
        html_path = html_path.replace(".md", ".html")
        pdf_path = md_path.replace(md_dir, pdf_dir)
        pdf_path = html_path.replace(".md", ".pdf")
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
        open(md_publish_path, 'w', encoding='utf-8').write(md_contents)
        #subprocess.run(['pandoc', '-s', html_path, '-o', pdf_path])

def main():
    chapter_path_list = get_chapter_path_list()
    for chapter_path in chapter_path_list:
        toc.insert_and_return_toc(chapter_path)
    transform(chapter_path_list)

if __name__ == '__main__':
    main()