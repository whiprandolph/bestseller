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

"""
Checks to add:
* every cite references an item in biblio
* every biblio item has >= 1 cite

"""

assert publish.CUT_OUT_REFS_AND_TOCS == True, "Set publish.CUT_OUT_REFS_AND_TOCS to True"

repo_root_dir = r"C:\Users\whip\tdr"

book_final = r"C:\Users\whip\tdr_published_files"

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
    font-size: 1.07em;
  }
  h2 {
    font-size: 1.07em;
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

cover_src_path = os.path.join(repo_root_dir, "images\\online_front_cover.png")
cover_dest_path = os.path.join(book_final, "online_front_cover.png")
phys_book_md_path = os.path.join(book_final, "book_phys.md")
online_book_md_path = os.path.join(book_final, "book_online.md")
phys_book_html_path = os.path.join(book_final, "book_phys.html")
online_book_html_path = os.path.join(book_final, "book_online.html")
epub_book_html_path = os.path.join(book_final, "book_epub.html")
book_epub_path = os.path.join(book_final, "The Deepest Revolution.epub")
book_zip_path = os.path.join(book_final, "The Deepest Revolution.zip")
book_zip_dir = os.path.join(book_final, "The Deepest Revolution -- Zip")
online_content_pdf_path = os.path.join(book_final, "content_online.pdf")
phys_content_pdf_path = os.path.join(book_final, "content_phys.pdf")
online_book_pdf_path = os.path.join(book_final, "The Deepest Revolution.pdf")
phys_book_pdf_path = os.path.join(book_final, "The Deepest Revolution -- PHYSICAL.pdf")
index_path = os.path.join(book_final, "index.pdf")
citations_path = r"C:\Users\whip\tdr\Part 4 - Closing Notes\Citations.md"
bib_path = r"C:\Users\whip\tdr\Part 4 - Closing Notes\Bibliography.md"
tmp_bib_path = os.path.join(book_final, "tmp_biblio.md")
images_source = r"C:\Users\whip\tdr-book-html\images"
images_dest = os.path.join(book_final, "images")

#assert False, "Disabled while making updates"

def verify_epub():
  # Verify all images in file
  shutil.copyfile(book_epub_path, book_zip_path)

  with zipfile.ZipFile(book_zip_path, 'r') as zip_ref:
    zip_ref.extractall(book_zip_dir)
  img_count = 0
  for path in os.listdir(book_zip_dir):
    if path.lower().endswith('png') or path.lower().endswith('jpg'):
      img_count+=1
  # should be 3 for contents, 4 w/cover
  assert img_count == 7, "Invalid image count, %s" % img_count
  shutil.rmtree(book_zip_dir)
  os.remove(book_zip_path)
  

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

  cite_list = []
  ref_map = build_ref_map(references)

  ref_start_line_check = [x for x in body.split("\n") if x.strip().startswith("[xxx")]
  assert len(ref_start_line_check) == 0, "[xxx starts a line; ref: %s, file: %s" % (ref_start_line_check, full_path)

  header_check = [x for x in body.split("\n") if x.strip().startswith("##") and not ("[" not in x and "]" not in x and "(" not in x and ")" not in x) and "Audio" not in x]
  # assert len(header_check) == 0, "edit-header; header: %s, file: %s" % (header_check, full_path)
  print("SKIPPING HEADER CHECK")
  start = body.find("[xxx")

  cite_number = 1
  while start != -1:
    end = body.find("]", start)+1
    xxx_ref = body[start:end]
    body = body[:start] + "<sup><a href=\"#cite_%s_%s_dest\" id=\"cite_%s_%s_src\" style=\"text-decoration:none\">%s</a></sup>" % (chap_id, cite_number, chap_id, cite_number, cite_number) + body[end:]
    cite_list.append((chap_id, cite_number, ref_map[xxx_ref]))
    start = body.find("[xxx", start+1)

    cite_number += 1

  # assert "**" not in blob, full_path
  print("SKIPPING ** CHECK")

  print_out = "Back-to-backs for " + os.path.basename(full_path)
  do_print = False
  for i in range(1, len(cite_list)):
    if cite_list[i][1] == cite_list[i-1][1]:
      print_out += '\n   ' + cite_list[i][1]
      do_print = True
  if do_print:
    print(print_out)

  return body, cite_list


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


def write_cites(cite_list):
  with open(citations_path, 'w', encoding='utf-8') as citations_handle:
    citations_handle.write("# Citations\n\n")
    citations_handle.write("<table class=\"cite_table\">")
    for chap, cites in cite_list:
      if not cites:
        continue

      citations_handle.write("<tr><td><b>%s</b></td></tr>" % chap)
      cites_iterable = iter(cites)
      for chap_id, cite_num, cite in cites_iterable:
      #citations_handle.write("## %s\n\n" % chap)
      #for chap_id, cite_num, cite in cites:
        #citations_handle.write("<a href=\"#cite_%s_%s_src\" id=\"cite_%s_%s_dest\" style=\"text-decoration:none\">%s</a>. %s<br/>\n" % (chap_id, cite_num, chap_id, cite_num, cite_num, cite))
        cell_contents = "<a href=\"#cite_%s_%s_src\" id=\"cite_%s_%s_dest\" style=\"text-decoration:none\">%s</a>. %s<br/>\n" % (chap_id, cite_num, chap_id, cite_num, cite_num, cite)
        try:
          next_chap_id, next_cite_num, next_cite = next(cites_iterable)
          # Even number of cites, row has two cells
          cell_contents_2 = "<a href=\"#cite_%s_%s_src\" id=\"cite_%s_%s_dest\" style=\"text-decoration:none\">%s</a>. %s<br/>\n" % (next_chap_id, next_cite_num, next_chap_id, next_cite_num, next_cite_num, next_cite)
          citations_handle.write("<tr><td>%s</td><td>%s</td></tr>\n\n" % (cell_contents, cell_contents_2))
        except Exception as exc:
          # odd number of cites, close out the row
          citations_handle.write("<tr><td>%s</td><td></td></tr>\n\n" % cell_contents)

    citations_handle.write("</table>")
    citations_handle.write("<div style=\"break-after:page\"></div>\n")


def fix_biblio():
  bib_blob = open(bib_path, 'r', encoding='utf-8').read()
  lines = bib_blob.split("\n")

  fixed_lines = []
  for line in lines:
    if line.strip() == "" or "# Bibliography" in line: continue

    if "https://" in line or "http://" in line and "a href" not in line:
      protocol = "https://" if "https://" in line else "http://"
      link = protocol + line.split(protocol)[1].strip()
      if " " in link: # if the url isn't at the end of the line
        link = link.split(" ")[0]
      line = line.replace(link, "<a href=\"%s\" style=\"color:black\">%s</a>" % (link, link))
    assert "\">\">" not in line, line
    fixed_lines.append(line)
  open(tmp_bib_path, 'w', encoding='utf-8').write("# Bibliography\n\n<div id=\"biblio\">\n\n%s\n\n</div>\n\n<div style=\"break-after:page\"></div>" % '\n\n'.join(fixed_lines))


def main():

  print("Starting at %s" % time.ctime())
  start_time = time.time()
  shutil.rmtree(book_final)
  os.mkdir(book_final)

  print(" == Running ttoc.py")
  subprocess.run(['python', 'ttoc.py'])

  shutil.copytree(images_source, images_dest)
  full_list = ttoc.get_file_list(ignore_images=True)
  assert len(full_list) == 28, "full list w/unexpected length: %s\n\n%s" % (len(full_list), full_list)
  full_cite_list = []
  with open(online_book_md_path, 'w', encoding='utf-8') as book_md:
    for file_name in full_list:
      if "citation" in file_name.lower() or "bibliography" in file_name.lower():
        continue
      body, cite_list = process_chapter(file_name)
      book_md.write("%s\n" % body)
      if 'Part ' not in file_name:
        chap_line = body.split("\n", 1)[0]
        assert chap_line.startswith("## ") or chap_line.startswith("# "), chap_line
      if cite_list:
        chapter_name = body.split("\n", 1)[0].strip("## ").strip()
        full_cite_list.append((chapter_name, cite_list))
    write_cites(full_cite_list)
    fix_biblio()
    cite_blob = open(citations_path, 'r', encoding='utf-8').read()
    bib_blob = open(tmp_bib_path, 'r', encoding='utf-8').read()
    book_md.write("%s\n\n" % cite_blob)
    book_md.write("%s\n\n" % bib_blob)
    book_md.close()
  subprocess.run(['pandoc', '-s', online_book_md_path,
                            '-o', online_book_html_path])
  fixup_html(online_book_html_path, phys=False)
  print("About to start PDF...")
  # phys book has bw images
  # online book has color images and for epub, front cover only

  shutil.copyfile(cover_src_path, cover_dest_path)
  print("Finished producing html")
  make_online_pdf()
  os.startfile(book_final)
  make_phys_book()
  make_epub()
  # cleanup()
  end_time = time.time()
  #time_diff = #timedelta(seconds=end_time-start_time)
  time_diff = round(end_time-start_time)
  print("Elapsed time: %s" % time_diff)


def make_online_pdf():
  server_string = "python -m http.server -d %s" % book_final
  print(" == Starting server: %s (online book)" % server_string)
  server = subprocess.Popen(server_string)
  try:
    print(" == Creating online content.pdf")
    subprocess.run(['node', r'C:\Users\whip\tdr_js\online_content_to_pdf.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
    pdf_toc.main(content_path=online_content_pdf_path, book_pdf_path=online_book_pdf_path, dimensions=PHYS, phys=False)
  finally:
    server.terminate()


def fixup_html(html_path, phys):
  book_html = open(html_path, 'r', encoding='utf-8').read()
  ADDED_STYLE = BOOK_ADDED_STYLE_ONLINE
  if phys:
    ADDED_STYLE = BOOK_ADDED_STYLE_PHYS
  book_html = book_html.replace("</html>", ADDED_STYLE)
  book_html = book_html.replace("**", "")
  open(html_path, 'w', encoding='utf-8').write(book_html)
  

def make_epub():
  print(" == Starting epub at %s" % time.ctime())
  subprocess.run(['pandoc', '-s', online_book_md_path,
                            '-o', epub_book_html_path,
                            '--metadata', 'title=The Deepest Revolution',
                            '--metadata', 'author=William Randolph'])
  fixup_html(epub_book_html_path, phys=False)
  html = open(epub_book_html_path, 'r', encoding='utf-8').read()
  html = html.replace("</header>", "</header><div style=\"page-break-after:page\"></div><center>Copyright 2025 William Randolph</center><div style=\"page-break-after:page\"></div>")
  open(epub_book_html_path, 'w', encoding='utf-8').write(html)
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


def make_phys_book():
  
  server_string = "python -m http.server -d %s" % book_final
  print(" == Starting server again (physical book): %s (%s)" % (server_string, time.ctime()))
  server = subprocess.Popen(server_string)
  try:
    print(" == Creating phys content.pdf")
    shutil.copy(online_book_md_path, phys_book_md_path)
    update_images_bw()
    subprocess.run(['pandoc', '-s', phys_book_md_path, # make pdf w/real index
                              '-o', phys_book_html_path])
    fixup_html(phys_book_html_path, phys=True)
    subprocess.run(['node', r'C:\Users\whip\tdr_js\phys_content_to_pdf.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
    pdf_toc.main(content_path=phys_content_pdf_path, book_pdf_path=phys_book_pdf_path, dimensions=PHYS, phys=True)
  finally:
    server.terminate()
  pass


def cleanup():
  print("Cleaning up... (%s)" % time.ctime())
  for filename in os.listdir(book_final):
    path = os.path.join(book_final, filename)
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