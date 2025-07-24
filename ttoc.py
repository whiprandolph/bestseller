import os
import toc
import time
import shutil
import markdown2
import subprocess
import traceback
from progress import chapters

source_dir = r"C:\Users\whip\tdr"
md_dir = r"C:\Users\whip\tdr-md-publish"
html_dir = r"C:\Users\whip\tdr-book-html"
md_images_dir = os.path.join(source_dir, 'images')
top_images_dir = os.path.join(html_dir, 'images')
pdf_dir = r"C:\Users\whip\tdr-book-pdf"
md_publish_dir = r"C:\Users\whip\tdr-md-publish"
why_so_lost_html = r"C:\Users\whip\tdr-book-html\Part 2 - Why Are We So Lost\06 - Why Are We So Lost.html"
why_so_lost_docx = r"C:\Users\whip\tdr-md-publish\Part 2 - Why Are We So Lost\06 - Why Are We So Lost.docx"

PUBLISH = True

full_html = ""
full_html_path = os.path.join(html_dir, 'full_book.html')
REV_ACT_COUNTER = 1 # start at 1


def rev_act_count_fixup(md_path):
    global REV_ACT_COUNTER
    assert md_path.endswith(".md"), md_path
    rev_act_html = '<div class="rev-act"><div class="rev-act-header">Revolutionary Activity #'
    line_list = []
    with open(md_path, 'r', encoding='utf-8') as file_handle:
        for line in file_handle:     
            if rev_act_html in line:
                assert "<br/>" in line, line
                assert "</div>" in line, line
                act_count, rest_of_line = line.split(rev_act_html)[1].split("<br/>", 1)
                assert (len(act_count) == 1 or len(act_count) == 2) and act_count.isdigit(), "Bad rev-act count: %s in %s" % (act_count, os.path.basename(md_path))
                reassembled_line = f"{rev_act_html}{REV_ACT_COUNTER}<br/>{rest_of_line}"
                line_list.append(reassembled_line)
                REV_ACT_COUNTER += 1
            elif 'rev-act\"' in line:
                print("Potential rev-act formatting issue with line:")
                print(line)
                breakpoint()
                a = 0
            else:
                line_list.append(line)
    with open(md_path, 'w', encoding='utf-8') as file_handle:
        file_handle.write("".join(line_list))


def get_file_list(ignore_images = False):
    path_list = []
    chapter_number = 1
    for part_name, chapter_names in chapters.items():
        part_path = os.path.join(source_dir, part_name)
        for a, b, chapter_name in chapter_names:
            if is_chapter_name(chapter_name, part_path):
              chapter_path = os.path.join(part_path, "%02d - %s" % (chapter_number, chapter_name))
              chapter_number += 1
            else:
              chapter_path = os.path.join(part_path, chapter_name)

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
            html_path = file_path.replace(source_dir, html_dir)
            md_path = file_path.replace(source_dir, md_dir)
            if not os.path.exists(os.path.dirname(html_path)):
                os.mkdir(os.path.dirname(html_path))
            if not os.path.exists(os.path.dirname(md_path)):
                os.mkdir(os.path.dirname(md_path))
            
            # also put image in top-level images dir
            if not os.path.exists(md_images_dir):
                os.mkdir(md_images_dir)
            if not os.path.exists(top_images_dir):
                os.mkdir(top_images_dir)
            top_img_dir_dest_path = os.path.join(top_images_dir, os.path.basename(file_path))
            shutil.copy(file_path, top_img_dir_dest_path)
            shutil.copy(file_path, html_path)
            shutil.copy(file_path, md_path)
            continue
        else:
            md_path = file_path
        
        html_path = md_path.replace(source_dir, html_dir)
        html_path = html_path.replace(".md", ".html")
        pdf_path = md_path.replace(source_dir, pdf_dir)
        pdf_path = pdf_path.replace(".md", ".pdf")
        md_publish_path = md_path.replace(source_dir, md_publish_dir)
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
         is_main_body(chapter_name, directory))
    
def is_pre_or_post_material(chapter_name, directory):
  return ("part 0" in directory.lower() or
          "part 4" in directory.lower())

def is_main_part_intro(chapter_name, directory):
  return ("Part Introduction" in chapter_name and
         is_main_body(chapter_name, directory))

def is_main_body(chapter_name, directory):
  return ("part 1" in directory.lower() or
          "part 2" in directory.lower() or
          "part 3" in directory.lower())


def main():
    file_list = get_file_list()
    for file_path in file_list:
        if '.md' in file_path:
            toc.insert_and_return_toc(file_path)
            rev_act_count_fixup(file_path)
    transform(file_list)
    os.chdir(os.path.dirname(why_so_lost_html))
    

if __name__ == '__main__':
    start_time = time.time()
    try:
        main()
    except Exception as exc:
        print("Error: %s" % exc)
        traceback.print_exc()
        breakpoint()
        a = 0
    print("%ss" % round(time.time()-start_time, 2))
