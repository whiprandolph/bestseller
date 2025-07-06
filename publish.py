import os
import csv
import pdb
import time
import beepy
import shutil
import progress
import markdown2
import subprocess

from progress import chapters
from pprint import pprint as pp
from collections import Counter

"""
REMINDER: citation-notes can have parens, so read first open paren and last close paren! (eastman (ohiyeas)...)
"""

gdrive=None

docx_root_dir = r"C:\Users\whip\book_docx"

html_root_dir = r"C:\Users\whip\tdr-book-html"
md_root_dir = r"C:\Users\whip\tdr\chapters"
if not os.path.exists(html_root_dir):
  os.mkdir(html_root_dir)

book_images_dir = os.path.join(html_root_dir, "images")

DEBUG=False
UPLOAD=True

CUT_OUT_REFS_AND_TOCS = True

if DEBUG:
  print("html root: %s" % os.path.basename(html_root_dir))

book_html = ""

def fixup_html(input_file, publish_docx=False):
  html = open(input_file,'r', encoding='utf-8').read()
  header = """<head>
  <style>
  blockquote {font-style: italic;}
  table.final_list td {text-align: left; min-width:6em;}
  </style>
  <div id="header-template"></div>
  <div id="footer-template"><span class="pageNumber"></span></div>
  </head>
  """

  if html.count("<toc/>") != 2:
    open(input_file, 'w', encoding='utf-8').write("".join((header, html)))
    return

  header, toc, body = html.split("<toc/>")
  header += """<head>
  <style>
  blockquote {font-style: italic;}
  </style>
  </head>
  """
  use_color = "OO" in toc # if there are any OOs, color links
  new_toc = []
  for line in toc.split("\n"):
    if "=\"#" not in line:
      new_toc.append(line)
      continue
    anchor_name = line.split("=\"#")[1].split("\">")[0]
    header_name = line.split("\">")[1].split("</a>")[0]
    if use_color and ">OO " not in line:
      first_close = line.find("\">") + 1
      line = line[:first_close] + " style=\"color:black\" " + line[first_close:]
    new_toc.append(line)
    body = body.replace(">%s<" % header_name, " id=\"%s\">%s<" % (anchor_name, header_name))
  output = ""
  if "Newsletter" not in input_file and not publish_docx:
    output = "".join((header, '\n'.join(new_toc), body))
  else:
    output ="".join((header, body))
  open(input_file, 'w', encoding='utf-8').write(output)

def get_finality(cur_dir, input_filename, chapters):
  section_list = chapters.get(cur_dir.split(os.path.sep)[-1])
  if not section_list:
    return None
  for finality, chapter_name in section_list:
    stripped_filename = input_filename.strip(".md").split(" - ")[1]
    if stripped_filename.lower() in chapter_name.lower():
      return finality
  raise Exception("Finality not found for:\ncur_dir: %s\ninput_filename: %s\nchapters: %s\n" % (cur_dir, input_filename, chapters))

def get_section_color_number(url, chapters):
  section = url.strip("#").replace("---", ' - ')
  split_point = section.index(' - ')+3
  pieces = section[:split_point], section[split_point:]
  capitalized = pieces[1].capitalize()
  combined = pieces[0]+capitalized


def fixup_book_toc(book_toc_html, chapters):
  output = ["<html><head><style>\n" +
            ".finality_1 {color: black;}\n" +
            ".finality_2 {color: darkgoldenrod;}\n" +
            ".finality_3 {color: blue;}\n" +
            "</style>\n</head><body>"]
  for line in open(book_toc_html, 'r').readlines():
    if line.count("\"") != 2 or line.count("<a") != 1:
      output.append(line)
      continue
    url = line.split("\"")[1]
    if "---" in url[7:11] or 'part' in url[0:6]:
      color_number = get_section_color_number(url, chapters)
      output.append(line)
      continue

    section = int(url[1:3].strip("-"))
    chapter_number = int(url.split("-")[1])
    cc = [*chapters]
    finality = chapters[cc[section-1]][chapter_number-1][0]
    pieces = line.split("\">")
    new_line = pieces[0] + "\" class=\"finality_%s\">" % finality + pieces[1]
    output.append(new_line)
  output.append("</body></html>")
  open(book_toc_html,'w').write("\n".join(output))


def publish(file_list, first_run, publish_docx=False):
  global book_html

  if not os.path.exists(book_images_dir):
    os.makedirs(book_images_dir)

  for file_path in file_list:
    file_name = os.path.basename(file_path)
    html_dir = os.path.dirname(file_path).replace(md_root_dir, html_root_dir)
    if not os.path.exists(html_dir):
      os.makedirs(html_dir)

    if 'image' in html_dir:
      dest_path = os.path.join(html_dir, file_name)
      book_image_path = os.path.join(book_images_dir, file_name)
      shutil.copy(file_path, dest_path)
      shutil.copy(file_path, book_image_path)
      continue
    html_filename = file_name.replace(".md", '.html')
    html_path = os.path.join(html_dir, html_filename)
    mdConverter = markdown2.Markdown()

    markdown_input = open(file_path, 'r', encoding='utf-8').read()

    if CUT_OUT_REFS_AND_TOCS and "ToC" not in file_path:
      markdown_input = markdown_input.split("### Reference")[0] # cut references
      if "<toc/>" in markdown_input:
        pieces = markdown_input.split("<toc/>")
        markdown_input = pieces[0] + pieces[2]

    if DEBUG:
      print("input file path: %s"  % file_path)
      print("html path: %s" % html_path)
    html = mdConverter.convert(markdown_input)
    open(html_path, 'w', encoding='utf-8').write(html)
    fixup_html(html_path, publish_docx)
    if not first_run:
      book_html+=html
    if 'Book ToC.md' in file_path:
      fixup_book_toc(html_path, chapters)


def move_progress_png():
  shutil.move(os.path.join(md_root_dir, "progress_writing.png"), os.path.join(html_root_dir, "progress_writing.png"))
  shutil.move(os.path.join(md_root_dir, "progress_biblio.png"), os.path.join(html_root_dir, "progress_biblio.png"))


def get_exported_refs():
  cites = []
  with open(r"C:\Users\whip\tdr\My Library.csv", 'r', encoding='utf-8') as csvfile:
    lines = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(lines, None)
    for pieces in lines:
      if pieces[35]:
        cites.append(pieces[35])
  return cites


def set_up():
  shutil.rmtree(os.path.join(html_root_dir))
  os.mkdir(html_root_dir)


if __name__=="__main__":
  print("not supported")
  import pdb;pdb.set_trace()
