import os
import csv
import pdb
import shutil
import subprocess

from progress import chapters
from pprint import pprint as pp
from collections import Counter

"""
REMINDER: citation-notes can have parens, so read first open paren and last close paren! (eastman (ohiyeas)...)
"""
raise Exception("Is this module used?")
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
