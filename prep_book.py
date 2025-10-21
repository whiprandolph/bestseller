import os
import re
import sys
import time
import ttoc
import shutil
import zipfile
import pdf_toc
import threading
import subprocess
import cite_wizard
from enum import Enum
from datetime import timedelta
from pprint import pprint as pp
from pypdf import PdfReader, PdfWriter
from ttoc import is_main_part_intro, repo_root_dir, js_dir, images_source, images_dest, pub_dir, final_biblio_path_epub, final_biblio_path_pdf
from progress import chapters 

"""
Checks to add:
* every cite references an item in biblio
* every biblio item has >= 1 cite
"""

cover_src_path = os.path.join(repo_root_dir, "images/online_front_cover.png")
cover_dest_path = os.path.join(pub_dir, "online_front_cover.png")

## MD
online_pdf_book_md_path = os.path.join(pub_dir, "book_online_pdf.md")
phys_book_md_path = os.path.join(pub_dir, "book_phys.md")
epub_book_md_path = os.path.join(pub_dir, "book_epub.md")

## HTML
phys_html_path = os.path.join(pub_dir, "book_phys.html")
online_pdf_book_html_path = os.path.join(pub_dir, "book_online_pdf.html")
epub_book_html_path = os.path.join(pub_dir, "book_epub.html")

## FINAL
online_book_pdf_path = os.path.join(pub_dir, "The Deepest Revolution.pdf")
phys_book_pdf_path = os.path.join(pub_dir, "The Deepest Revolution -- PHYSICAL.pdf")
book_epub_path = os.path.join(pub_dir, "The Deepest Revolution.epub")

online_content_pdf_path = os.path.join(pub_dir, "content_online.pdf")
phys_content_pdf_path = os.path.join(pub_dir, "content_phys.pdf")

class Version(Enum):
  EPUB = 1
  ONLINE_PDF = 2
  PHYS = 3

PHYS = {"width":6, 'height':9}

BOOK_ADDED_STYLE_BASE = """
  <style>\n
  .rev-act-header {
    text-align: center;
    font-weight: bold;
  }
  blockquote {
    color: black;
  }
  .rev-act {
    background-color: #e6e6e6;
    padding: .75em;
  }
  .rev-act-first {
    background-color: #e6e6e6;
    padding-top: .75em;
    padding-left: 1em;
    padding-right: 1em;
    padding-bottom: .75em;
  }
  .rev-act-last {
    background-color: #e6e6e6;
    padding-top: .75em;
    padding-left: 1em;
    padding-right: 1em;
    padding-bottom: 1em;
  }
  .rev-act-middle {
    background-color: #e6e6e6;
    padding-top: .75em;
    padding-left: 1em;
    padding-right: 1em;
    padding-bottom: .75em;
  }
  .title {
    font-size: 40pt;
    text-align:center;
  }
  .author {
    font-size: 22pt;
    text-align:center;
  }
  .nations_referenced_table {
    display: table;
    font-size:12pt;
  }
  .nations_referenced_tbody {
    border:0;
  }
  .quarterwidth {
    width: 25%;
  }
  p, .rev-act {\n
    font-size: 12pt;
    color:black;
    text-align: justify;
  }\n

  sup {
    font-size:9pt;
  }

  .part-intro {
    font-size: 38px;
  }
"""

BOOK_ADDED_STYLE_BOTH_PDF = BOOK_ADDED_STYLE_BASE + """

  td {
    word-wrap: break-word;
    word-break: break-all;
    padding-top:.125em;
    padding-bottom:.25em;
    padding-right:0em;
    padding-left:0em;
    margin:0px;
  }
  td.partial-cell {
    width:33.3%;
    padding-left:1em;    
  }
  .biblio-div {
    font-size:7.1pt;
  }
  td.full-cell {
    width:100%;
    
  }
  table.biblio_table {
    border:0px;
    margin:0em;
    table-layout: fixed;
  }
  #biblio_table_body {
    border:0px;
    margin:0px;
    font-size:6.9pt;
  }
  h1, h2, h3, h4, h5, h6 {
    margin-top: 1.2em;
  }
  h1 {
    /* h1 same as h2, so the pre/post material fit on the page better in PDF, and are indented at the right level (h1 level) in the epub */
    font-size: 1.07em;
  }
  h2 {
    font-size: 1.07em;
  }
  h3 {
    font-size: .87em;
  }
  h4 {
    font-size: 0.84em;
  }
  body {
    padding-left: 0px;
    padding-right: 0px;
    padding-top: 0px;
    padding-bottom: 0px;
  }
"""

# no left/right margin differences online
BOOK_ADDED_STYLE_EPUB = BOOK_ADDED_STYLE_BASE + """
  .epub-bib-singleton-row {
    font-size:12pt;
  }
  .sub-entry-container {
    padding-left: 30px;
  }
  .biblio-div {
  
  }
  .biblio-sub-entry {
    font-size:11pt;
  }
  </style>
  </html>
"""

BOOK_ADDED_STYLE_PHYS = BOOK_ADDED_STYLE_BOTH_PDF + """

  @page :left {
    size: %sin %sin;
    margin-left: .55in;
    margin-right: .90in;
    margin-top: .6in;
    margin-bottom: .55in
  }
    @page :right {
    size: %sin %sin;
    margin-left: .90in;
    margin-right: .55in;
    margin-top: .55in;
    margin-bottom: .55in
  }
  </style>
  </html>
""" % (PHYS['width'], PHYS['height'], PHYS['width'], PHYS['height'])

# no left/right margin differences online
BOOK_ADDED_STYLE_ONLINE_PDF = BOOK_ADDED_STYLE_BOTH_PDF + """

    @page {
    size: %sin %sin;
    margin-left: .55in;
    margin-right: .55in;
    margin-top: .55in;
    margin-bottom: .55in
  }
  </style>
  </html>
""" % (PHYS['width'], PHYS['height'])

chap_ids = set()

#assert False, "Disabled while making updates"

def verify_epub():
  book_zip_path = os.path.join(pub_dir, "The Deepest Revolution.zip")
  book_zip_dir = os.path.join(pub_dir, "The Deepest Revolution -- Zip")

  # Verify all images in file
  shutil.copyfile(book_epub_path, book_zip_path)

  with zipfile.ZipFile(book_zip_path, 'r') as zip_ref:
    zip_ref.extractall(book_zip_dir)
  img_count = 0
  for path in os.listdir(book_zip_dir):
    if path.lower().endswith('png') or path.lower().endswith('jpg'):
      img_count+=1
  # should be 6 for contents, 7 w/cover
  assert img_count == 7, "Invalid image count, %s" % img_count
  shutil.rmtree(book_zip_dir)
  os.remove(book_zip_path)
  

def process_chapter(full_path, cite_to_index_dict, fix_citation=False):
  blob = open(full_path, 'r', encoding='utf-8').read()
  chap_line = blob.split("\n")[0]
  if ttoc.is_chapter_name(os.path.basename(full_path), os.path.dirname(full_path)):
    assert chap_line.startswith("## "), "%s contains wrong number of # (main body)" % chap_line
  elif ttoc.is_pre_or_post_material(os.path.basename(full_path), os.path.dirname(full_path)):
    assert chap_line.startswith("# "), "%s contains wrong number of # (pre/post)" % chap_line
  elif ttoc.is_main_part_intro(os.path.basename(full_path), os.path.dirname(full_path)):
    pass # don't have # headers, have straight html
  else:
    assert False, full_path
  chap_id = chap_line.split(":")[0].strip("#").strip(" ")
  
  chap_id = chap_id.replace(" ", "_")
  if not is_main_part_intro(os.path.basename(full_path), os.path.dirname(full_path)):
    assert chap_id not in chap_ids, chap_id
  chap_ids.add(chap_id)
  ref_header = "### References"
  assert '<toc/>' not in blob, "Chap %s has <toc/>" % full_path
  if "06 - Why Are We So Lost" in full_path:
    assert blob.count("break-after:page") == 1, "page CONTAINS too many break-after in %s" % full_path
  else:
    assert "break-after:page" not in blob, "page CONTAINS break-after in %s" % full_path
  
  if not "[xxx-" in blob:
    blob += "\n\n<div style=\"break-after:page\"></div>\n"
    return blob

  body, references = blob.split(ref_header)
  body += "\n\n<div style=\"break-after:page\"></div>\n"
  
  ref_start_line_check = [x for x in body.split("\n") if x.strip().startswith("[xxx")]
  assert len(ref_start_line_check) == 0, "[xxx starts a line; ref: %s, file: %s" % (ref_start_line_check, full_path)

  header_check = [x for x in body.split("\n") if x.strip().startswith("##") and not ("[" not in x and "]" not in x and "(" not in x and ")" not in x) and "Audio" not in x]
  assert len(header_check) == 0, "edit-header; header: %s, file: %s" % (header_check, full_path)
  start = body.find("[xxx")

  while start != -1:
    end = body.find("]", start)+1
    xxx_ref = body[start:end]
    cite_num = cite_to_index_dict[xxx_ref] if not fix_citation else 100
    body = body[:start] + "<sup><a href=\"#cite_%s_dest\" id=\"cite_%s_src\" style=\"text-decoration:none\">%s</a></sup>" % (cite_num, cite_num, cite_num) + body[end:]
    start = body.find("[xxx", start+1)

  # only ** are in chap 18 We are the promised land.
  assert "**" not in blob or ("_**" in blob and blob.count("**") == 2), full_path
  underscore_indices = [i for i, c in enumerate(blob) if c == '_']
  questionable = [i for i in underscore_indices if blob[i+1] in ",.;:'?!"]
  try:
    assert not questionable or ("**_" in blob and blob.count("**") == 2), full_path
  except Exception as exc:
    print("Underscore - punctuation ordering problem:")
    print("\n")
    for i in questionable:
      print(blob[i-40:min(i+50, len(blob))])
    print("\n")
    breakpoint()
    a = 5
  return body


def build_ref_map(ref_blob):
  ref_map = {}

  for line in ref_blob.split("\n"):
    if not line.strip(): continue

    # assert "[xxx" in line and "-aaa" in line, line
    if '-xxx' in line:
      xxx, official = line.split("-xxx")
      ref_map[xxx] = "(author, date)"
      print("ADDING FAKE CITES TILL THEY'RE DONE (%s)" % xxx)
      continue
    elif '-aaa' not in line:
      xxx = line
      ref_map[xxx] = "(author, date)"
      print("ADDING FAKE CITES TILL THEY'RE DONE (%s)" % xxx)
      continue

    else:
      xxx, official = line.split("-aaa ")
      xxx = xxx.strip()
      official = official.strip()
      try:
        assert xxx.startswith("[xxx") and xxx[-1] == "]", line
        assert official[0] == "(" and official[-1] == ")", line
      except Exception as exc:
        print(exc)
        print(line)
        print(xxx)
        breakpoint()
        pass

    ref_map[xxx] = official
  return ref_map


def fix_biblio(bib_path):
  lines = open(bib_path, 'r', encoding='utf-8').readlines()[2:]
  
  fixed_lines = []
  for line in lines:
    line = line.strip()
    if "https://" in line or "http://" in line and "a href" not in line:
      protocol = "https://" if "https://" in line else "http://"
      link = protocol + line.split(protocol)[1].strip()
      if " " in link: # if the url isn't at the end of the line
        link = link.split(" ")[0]
        line = line.replace(link, "<a href=\"%s\" style=\"color:black\">%s</a>" % (link, link))
      elif link.endswith("</div>"):
        link = link.strip("</div>")
        line = line.replace(link, "<a href=\"%s\" style=\"color:black\">%s</a>" % (link, link)) + "</div>"
    assert "\">\">" not in line, line
    fixed_lines.append(line)
  return "# Bibliography\n\n%s\n\n<div style=\"break-after:page\"></div>" % '\n\n'.join(fixed_lines)


def main():

  start_time = time.time()
  shutil.rmtree(pub_dir)
  os.mkdir(pub_dir)
  cite_to_index_dict = cite_wizard.map_cites()

  shutil.copytree(images_source, images_dest)
  full_list = ttoc.get_file_list(ignore_images=True)
  assert len(full_list) == 28, "full list w/unexpected length: %s\n\n%s" % (len(full_list), full_list)
  base_book_pieces = []
  for file_name in full_list:
    if "bibliography" in file_name.lower():
      continue
    body = process_chapter(file_name, cite_to_index_dict)
    if 'Part ' not in file_name:
      chap_line = body.split("\n", 1)[0]
      assert chap_line.startswith("## ") or chap_line.startswith("# "), chap_line
    base_book_pieces.append("%s\n" % body)
  base_book_md = "".join(base_book_pieces)

  bib_blob_epub = fix_biblio(final_biblio_path_epub)
  bib_blob_pdf = fix_biblio(final_biblio_path_pdf)
  both_pdf_base_md = "".join((base_book_md, bib_blob_pdf))
  epub_base_md = "".join(("<div style=\"page-break-after:page\"></div><center>Copyright 2025 William Randolph</center><div style=\"page-break-after:page\"></div>", base_book_md, bib_blob_epub))
  
  
  

  print("About to start final production...")

  threads = (
    threading.Thread(target=make_phys_book, args=(both_pdf_base_md,)),
    threading.Thread(target=make_online_pdf, args=(both_pdf_base_md,)),
    threading.Thread(target=make_epub, args=(epub_base_md,))
  )
  for thread in threads:
    thread.start()

  subprocess.Popen(["open", pub_dir])

  for thread in threads:
    thread.join()

  cleanup()
  end_time = time.time()
  #time_diff = #timedelta(seconds=end_time-start_time)
  time_diff = round(end_time-start_time)
  print("Elapsed time: %s" % time_diff)


def make_online_pdf(both_pdf_base_md):
  open(online_pdf_book_md_path, 'w', encoding='utf-8').write(both_pdf_base_md)
  subprocess.run(['pandoc', '-s', online_pdf_book_md_path,
                            '-o', online_pdf_book_html_path])
  server_string = ["python3", "-m", "http.server", "2000", "-d", pub_dir]
  print(" == Starting server: %s (online book)" % server_string)
  server = subprocess.Popen(server_string)
  try:
    fixup_html(online_pdf_book_html_path, Version.ONLINE_PDF)
    print(" == Creating online content.pdf")
    subprocess.run(['node', f'{js_dir}/online_content_to_pdf.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
    pdf_toc.main(content_path=online_content_pdf_path, book_pdf_path=online_book_pdf_path, dimensions=PHYS, phys=False)
  finally:
    server.terminate()


def fixup_html(html_path, version: Version):
  book_html = open(html_path, 'r', encoding='utf-8').read()
  ADDED_STYLE = None
  if version == Version.ONLINE_PDF:
    ADDED_STYLE = BOOK_ADDED_STYLE_ONLINE_PDF
  elif version == Version.PHYS:
    ADDED_STYLE = BOOK_ADDED_STYLE_PHYS
  else:
    ADDED_STYLE = BOOK_ADDED_STYLE_EPUB
  book_html = book_html.replace("</html>", ADDED_STYLE)
  book_html = book_html.replace("**", "")
  book_html = book_html.replace("DOTHERE", ".")
  open(html_path, 'w', encoding='utf-8').write(book_html)


def pandoc_epub_fix():
  html = open(epub_book_html_path, 'r', encoding='utf-8').read()
  pieces = html.split("body {", 1)
  end = pieces[1].split("}", 1)[1]
  open(epub_book_html_path, 'w', encoding='utf-8').write(pieces[0] + end)


def make_epub(epub_base_md):
  open(epub_book_md_path, 'w', encoding='utf-8').write(epub_base_md)
  subprocess.run(['pandoc', '-s', epub_book_md_path,
                            '-o', epub_book_html_path,
                            '--metadata', 'title=The Deepest Revolution',
                            '--metadata', 'author=William Randolph'])
  fixup_html(epub_book_html_path, Version.EPUB)
  pandoc_epub_fix()
  shutil.copyfile(cover_src_path, cover_dest_path)
  subprocess.run(['ebook-convert', epub_book_html_path, book_epub_path,
                                   '--cover', cover_dest_path,
                                   '--level1-toc', '//h:h1',
                                   '--level2-toc', '//h:h2',
                                   '--level3-toc', '//h:h3'])
  verify_epub()


def update_images_bw():
  image_names = [
    "american_riot_police",
    "chinese_riot_police",
    "venezuelan_riot_police",
    "hawks_hunting",
  ]
  phys_book_md = open(phys_book_md_path, 'r', encoding='utf-8').read()

  for name in image_names:
    for item in os.listdir(images_dest):
      if '%s_bw' % name in item:
        break
    else:
      raise Exception("%s does not exist in images dir" % name)
    assert phys_book_md.count(name) == 1, name
    phys_book_md = phys_book_md.replace(name, '%s_bw' % name)

  open(phys_book_md_path, 'w', encoding='utf-8').write(phys_book_md)


def make_phys_book(both_pdf_base_md):
  open(phys_book_md_path, 'w', encoding='utf-8').write(both_pdf_base_md)
  server_string = ["python3", "-m", "http.server", "-d", pub_dir]
  print(" == Starting server again (physical book): %s (%s)" % (server_string, time.ctime()))
  server = subprocess.Popen(server_string)
  try:
    print(" == Creating phys content.pdf")
    update_images_bw()
    subprocess.run(['pandoc', '-s', phys_book_md_path, # make pdf w/real index
                              '-o', phys_html_path])
    fixup_html(phys_html_path, Version.PHYS)
    proc = subprocess.run(['node', rf'{js_dir}/phys_content_to_pdf.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
    pdf_toc.main(content_path=phys_content_pdf_path, book_pdf_path=phys_book_pdf_path, dimensions=PHYS, phys=True)
  finally:
    server.terminate()
  pass


def cleanup():
  print("Cleaning up... (%s)" % time.ctime())
  for filename in os.listdir(pub_dir):
    path = os.path.join(pub_dir, filename)
    if not (online_book_pdf_path in path) and online_book_pdf_path != path and phys_book_pdf_path != path and book_epub_path != path:
      if os.path.isdir(path):
        shutil.rmtree(path)
      else:
        os.remove(path)


if __name__ == "__main__":
  try:
    main()
  except Exception as exc:
    import traceback
    traceback.print_exc()
    print("Error!")
    print(exc)
    breakpoint()
    pass