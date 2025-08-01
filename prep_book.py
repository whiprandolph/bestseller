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

assert publish.CUT_OUT_REFS_AND_TOCS == True, "Set publish.CUT_OUT_REFS_AND_TOCS to True"

repo_root_dir = r"C:\Users\whip\tdr"

book_final = r"C:\Users\whip\tdr_published_files"

PHYS = {"width":6, 'height':9}

BOOK_ADDED_STYLE = """

<style>\n
  p {\n
    font-size: 12pt;
    color:black;
  }\n
  @page {
    size: %sin %sin;
  }
  blockquote {
    color: black;
  }
  .rev-act {
    background-color: #F3F3F3;
    padding: 1em;
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
""" % (PHYS['width'], PHYS['height'])

chap_ids = set()

cover_src_path = os.path.join(repo_root_dir, "images\\online_front_cover.png")
cover_dest_path = os.path.join(book_final, "online_front_cover.png")
phys_book_md_path = os.path.join(book_final, "book_phys.md")
online_book_md_path = os.path.join(book_final, "book_online.md")
phys_book_html_path = os.path.join(book_final, "book_phys.html")
online_book_html_path = os.path.join(book_final, "book_online.html")
book_epub_path = os.path.join(book_final, "The Deepest Revolution.epub")
book_zip_path = os.path.join(book_final, "The Deepest Revolution.zip")
book_zip_dir = os.path.join(book_final, "The Deepest Revolution -- Zip")
online_content_pdf_path = os.path.join(book_final, "content_online.pdf")
phys_content_pdf_path = os.path.join(book_final, "content_phys.pdf")
online_book_pdf_path = os.path.join(book_final, "The Deepest Revolution.pdf")
phys_book_pdf_path = os.path.join(book_final, "The Deepest Revolution -- PHYSICAL.pdf")
index_path = os.path.join(book_final, "index.pdf")

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
  assert img_count == 4, "Invalid image count, %s" % img_count
  shutil.rmtree(book_zip_dir)
  os.remove(book_zip_path)
  

def process_chapter(full_path):
  blob = open(full_path, 'r', encoding='utf-8').read()
  chap_id = blob.split("\n")[0].split(":")[0].strip("#").strip(" ")
  chap_id = chap_id.replace(" ", "_")
  if not is_main_part_intro(os.path.basename(full_path), os.path.dirname(full_path)):
    assert chap_id not in chap_ids, chap_id
  chap_ids.add(chap_id)
  references = "### References"
  try:
    assert '<toc/>' not in blob, "Chap %s has <toc/>" % full_path
    assert references not in blob, "reference in chap %s" % full_path
    assert "break-after:page" in blob, "no break-after in %s" % full_path
  except AssertionError as exc:
    response = 'y'
    time.sleep(.25)
    print("FAILED ASSERTION '%s', CONFIRM WE SHOULD CONTINUE (Y/n) > " % exc)
    if response == 'n':
      sys.exit()
  if references in blob:
    return blob.split(references)[0]
  return blob


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
  with open(online_book_md_path, 'w', encoding='utf-8') as book_md:
    for file_name in full_list:
      body = process_chapter(file_name)
      book_md.write("%s\n" % body)
      if 'Part ' not in file_name:
        chap_line = body.split("\n", 1)[0]
        assert chap_line.startswith("## ") or chap_line.startswith("# "), chap_line
      
  subprocess.run(['pandoc', '-s', online_book_md_path,
                            '-o', online_book_html_path])
  fixup_html(online_book_html_path)
  print("About to start PDF...")
  # phys book has bw images
  # online book has color images and for epub, front cover only

  shutil.copyfile(cover_src_path, cover_dest_path)
  print("Finished producing html")
  make_online_pdf()
  os.startfile(book_final)
  # make_phys_book()
  # make_epub()
  cleanup()
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
    pdf_toc.main(content_path=online_content_pdf_path, book_pdf_path=online_book_pdf_path, dimensions=PHYS)
  finally:
    server.terminate()


def fixup_html(html_path):
  book_html = open(html_path, 'r', encoding='utf-8').read()
  book_html = book_html.replace("</html>", BOOK_ADDED_STYLE)
  book_html = book_html.replace("**", "")
  open(html_path, 'w', encoding='utf-8').write(book_html)
  

def make_epub():
  print(" == Starting epub at %s" % time.ctime())
  subprocess.run(['pandoc', '-s', online_book_md_path,
                            '-o', online_book_html_path,
                            '--metadata', 'title=The Deepest Revolution',
                            '--metadata', 'author=William Randolph'])
  fixup_html(online_book_html_path)
  subprocess.run(['ebook-convert', online_book_html_path, book_epub_path,
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
    fixup_html(phys_book_html_path)
    subprocess.run(['node', r'C:\Users\whip\tdr_js\phys_content_to_pdf.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
    print("Reusing table of contents...")
    pdf_toc.merge_pdfs(content_path=phys_content_pdf_path, book_pdf_path=phys_book_pdf_path)
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