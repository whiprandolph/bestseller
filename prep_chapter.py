import os
import sys
import ttoc
import time
import shutil
import publish
import zipfile
import pdf_toc
import subprocess
from datetime import timedelta
from pprint import pprint as pp
from pypdf import PdfReader, PdfWriter
from ttoc import is_main_part_intro
from progress import chapters 

import psutil
import signal

process_name_to_kill = "librewolf.exe" # Replace with the actual process name

def kill_librewolf():
  for proc in psutil.process_iter(['pid', 'name']):
    if proc.info['name'] == process_name_to_kill:
        try:
            os.kill(proc.info['pid'], signal.SIGTERM)
            print(f"Sent SIGTERM to process '{process_name_to_kill}' with PID: {proc.info['pid']}")
        except ProcessLookupError:
            print(f"Process '{process_name_to_kill}' with PID {proc.info['pid']} not found.")
        except Exception as e:
            print(f"An error occurred while killing process '{process_name_to_kill}': {e}")

"""
Checks to add:
* every cite references an item in biblio
* every biblio item has >= 1 cite

"""

assert publish.CUT_OUT_REFS_AND_TOCS == True, "Set publish.CUT_OUT_REFS_AND_TOCS to True"

repo_root_dir = r"C:\Users\whip\tdr"

tmp_dir = r"C:\Users\whip\tdr_published_files\tmp_dir"

PHYS = {"width":6, 'height':9}

BOOK_ADDED_STYLE_BASE = """

  .title {
    font-size: 40pt;
    text-align:center;
  }
  .author {
    font-size: 22pt;
    text-align:center;
  }
  p, .rev-act {\n
    font-size: 12pt;
    color:black;
    text-align: justify;
  }\n
  #biblio p {
    font-size: 6.9pt;
  }
  .part-intro {
    font-size: 38px;
  }

  table.cite_table td {
    font-size:6.9pt;
    padding-left: 0em;

  }
  blockquote {
    color: black;
  }
  .rev-act {
    background-color: #e3e3e3;
    padding: .75em;
  }
  .rev-act-first {
    background-color: #e3e3e3;
    padding-top: .75em;
    padding-left: 1em;
    padding-right: 1em;
    padding-bottom: .75em;
  }
  .rev-act-last {
    background-color: #e3e3e3;
    padding-top: .75em;
    padding-left: 1em;
    padding-right: 1em;
    padding-bottom: 1em;
  }
  .rev-act-middle {
    background-color: #e3e3e3;
    padding-top: .75em;
    padding-left: 1em;
    padding-right: 1em;
    padding-bottom: .75em;
  }
  h1, h2, h3, h4, h5, h6 {
    margin-top: 1.2em;
  }
  h1 {
    /* h1 same as h2, so the pre/post material fit on the page better in PDF, and are indented at the right level (h1 level) in the epub */
    font-size: 1.1em;
  }
  h2 {
    font-size: 1.1em;
  }
  h3 {
    font-size: .9em;
  }
  h4 {
    font-size: 0.8em;
  }
  .rev-act-header {
    text-align: center;
    font-weight: bold;
  }
  body {
    padding-left: 0px;
    padding-right: 0px;
    padding-top: 0px;
    padding-bottom: 0px;
    /*max-width:40em;*/
  }
</style>
</html>
""" 

# no left/right margin differences online
BOOK_ADDED_STYLE_PHYS = """
  <style>\n
  @page :left {
    size: %sin %sin;
    margin-left: .55in;
    margin-right: .90in;
    margin-top: .55in;
    margin-bottom: .55in
  }
    @page :right {
    size: %sin %sin;
    margin-left: .90in;
    margin-right: .55in;
    margin-top: .55in;
    margin-bottom: .55in
  }
  %s
""" % (PHYS['width'], PHYS['height'], PHYS['width'], PHYS['height'], BOOK_ADDED_STYLE_BASE)

BOOK_ADDED_STYLE_ONLINE = """
    <style>\n
    @page {
    size: %sin %sin;
    margin-left: .55in;
    margin-right: .55in;
    margin-top: .55in;
    margin-bottom: .55in
  }
  %s
""" % (PHYS['width'], PHYS['height'], BOOK_ADDED_STYLE_BASE)

chap_ids = set()

def process_chapter(full_path):
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
  
  if not ref_header in blob:
    blob += "\n\n<div style=\"break-after:page\"></div>\n"
    return blob, []

  body, references = blob.split(ref_header)
  body += "\n\n<div style=\"break-after:page\"></div>\n"

  ref_start_line_check = [x for x in body.split("\n") if x.strip().startswith("[xxx")]
  assert len(ref_start_line_check) == 0, "[xxx starts a line; ref: %s, file: %s" % (ref_start_line_check, full_path)

  start = body.find("[xxx")

  cite_number = 1
  while start != -1:
    end = body.find("]", start)+1
    xxx_ref = body[start:end]
    body = body[:start] + "<sup>%s</sup>" % cite_number + body[end:]
    start = body.find("[xxx", start+1)

    cite_number += 1

  return body

def main():
  pdf_path = os.path.join(tmp_dir, "test_chapter.pdf")
  html_path = os.path.join(tmp_dir, "test_chapter.html")
  md_path = os.path.join(tmp_dir, "test_chapter.md")
  md_source = r"C:\Users\whip\tdr\Part 3 - The Deepest Revolution\17 - Build Spiritual Strength with Others.md"
  kill_librewolf()
  if os.path.exists(tmp_dir):
    shutil.rmtree(tmp_dir)
  os.mkdir(tmp_dir)
  open(md_path, 'w', encoding='utf-8').write(process_chapter(md_source))  
  
  
  subprocess.run(['pandoc', '-s', md_path,
                            '-o', html_path])
  fixup_html(html_path, phys=True)
  print("About to start PDF...")
  
  make_phys_book(html_path, pdf_path)
  subprocess.run([r'C:\Program Files\LibreWolf\librewolf.exe', pdf_path])
  

def fixup_html(html_path, phys):
  book_html = open(html_path, 'r', encoding='utf-8').read()
  ADDED_STYLE = BOOK_ADDED_STYLE_ONLINE
  if phys:
    ADDED_STYLE = BOOK_ADDED_STYLE_PHYS
  book_html = book_html.replace("</html>", ADDED_STYLE)
  book_html = book_html.replace("**", "")
  open(html_path, 'w', encoding='utf-8').write(book_html)
  
def make_phys_book(html_path, pdf_path):
  
  server_string = "python -m http.server -d %s" % tmp_dir
  print(" == Starting server (physical book): %s (%s)" % (server_string, time.ctime()))
  server = subprocess.Popen(server_string)
  try:
    print(" == Creating test_chapter.pdf")
    subprocess.run(['node', r'C:\Users\whip\tdr_js\test_to_pdf.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
  finally:
    server.terminate()
  pass


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