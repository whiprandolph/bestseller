import os
import sys
import ttoc
import time
import shutil
import publish
import zipfile
import pdf_toc
import gen_index
import subprocess
from datetime import timedelta
from pprint import pprint as pp
from pypdf import PdfReader, PdfWriter

from progress import chapters

assert publish.CUT_OUT_REFS_AND_TOCS == True, "Set publish.CUT_OUT_REFS_AND_TOCS to True"

repo_root_dir = r"C:\Users\whip\tdr"

book_final = r"C:\Users\whip\tdr_published_files"

PHYS = {"width":5, 'height':9}

BOOK_ADDED_STYLE = """

<style>\n
  p {\n
    font-size: 10.85pt;
    color:black;
  }\n
  @page {
    size: %sin %sin;
  }
  blockquote {
    color: black;
  }
  body {
    padding-left: 0px;
    padding-right: 0px;
    padding-top: 0px;
    padding-bottom: 0px;
    max-width:40em;
  }
</style>
</html>
""" % (PHYS['width'], PHYS['height'])

chap_ids = set()

cover_src_path = os.path.join(repo_root_dir, "images\\online_front_cover.png")
biblio_copyright_path = r"C:\Users\whip\tdr\chapters\Part 4 - Closing Notes\15 - Bibliography and Copyright.md"
online_copyright_path = r"C:\Users\whip\tdr\chapters\Part 12 - Closing Notes\04 - Copyright.md"
cover_dest_path = os.path.join(book_final, "online_front_cover.png")
online_book_md_path = os.path.join(book_final, "book_online.md")
phys_book_md_path = os.path.join(book_final, "book_phys.md")
phys_pre_idx_book_md_path = os.path.join(book_final, "book_phys_pre_idx.md")
online_book_html_path = os.path.join(book_final, "book_online.html")
phys_book_html_path = os.path.join(book_final, "book_phys.html")
book_epub_path = os.path.join(book_final, "One Disease One Cure.epub")
book_zip_path = os.path.join(book_final, "One Disease One Cure.zip")
book_zip_dir = os.path.join(book_final, "One Disease One Cure -- Zip")
online_content_pdf_path = os.path.join(book_final, "content_online.pdf")
phys_content_pdf_path = os.path.join(book_final, "content_phys.pdf")
online_book_pdf_path = os.path.join(book_final, "One Disease One Cure.pdf")
phys_book_pdf_path = os.path.join(book_final, "One Disease One Cure -- PHYSICAL.pdf")
phys_book_pdf_path_tmp = os.path.join(book_final, "tmp_phys_book.pdf")
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
  # should be 30 for contents, 31 w/cover
  assert img_count == 3, "Invalid image count, %s" % img_count
  shutil.rmtree(book_zip_dir)
  os.remove(book_zip_path)


def build_ref_map(ref_blob):
  ref_map = {}

  for line in ref_blob.split("\n"):
    if not line.strip(): continue

    assert "[xxx" in line and "-aaa" in line, line

    xxx, official = line.split("-aaa ")
    xxx = xxx.strip()
    official = official.strip()
    assert xxx.startswith("[xxx") and xxx[-1] == "]", line
    assert official[0] == "(" and official[-1] == ")", line

    ref_map[xxx] = official
  return ref_map


def process_chapter(full_path):
  blob = open(full_path, 'r', encoding='utf-8').read()
  chap_id = blob.split("\n")[0].split(":")[0].strip("#").strip(" ")
  chap_id = chap_id.replace(" ", "_")
  assert chap_id not in chap_ids, chap_id
  chap_ids.add(chap_id)
  try:
    assert '<toc/>' not in blob, "Chap %s has <toc/>" % full_path
    assert "## References" not in blob, "reference in chap %s" % full_path
  except AssertionError as exc:
    response = input("FAILED ASSERTION '%s', CONFIRM WE SHOULD CONTINUE (Y/n) > " % exc)
    if response == 'n':
      sys.exit()
  return blob, []


def main():

  gen_index.fresh_start_check()

  print("Starting at %s" % time.ctime())
  start_time = time.time()

  shutil.rmtree(book_final)
  os.mkdir(book_final)

  print(" == Running ttoc.py")
  subprocess.run(['python', 'ttoc.py'])

  shutil.copytree(images_source, images_dest)
  full_list = ttoc.get_file_list(ignore_images=True)
  with open(phys_book_md_path, 'w', encoding='utf-8') as book_md:
    for file in full_list:
      if 'copyright' in file.lower(): continue # these are handled later

      body, chap_cite_list = process_chapter(file)
      book_md.write("%s\n" % body)
      chapter_name = body.split("\n", 1)[0].strip("## ").strip()
      if "introduction" in chapter_name.lower():
        assert len(chap_cite_list) == 0
  
  shutil.copyfile(phys_book_md_path, online_book_md_path)

  # phys book doesn't have the biblio, does have the index, has different copyright/biblio page
  with open(phys_book_md_path, 'a', encoding='utf-8') as phys_book_md:
    body, _ = process_chapter(biblio_copyright_path)
    phys_book_md.write("%s\n\n" % body)

  #phys_pre_idx_book_md_path

  with open(online_book_md_path, 'a', encoding='utf-8') as online_book_md:
    body, _ = process_chapter(online_copyright_path)
    online_book_md.write("%s\n\n" % body)

  shutil.copyfile(cover_src_path, cover_dest_path)
  make_online_pdf()
  make_phys_book()
  make_epub()
  #os.startfile(book_final)
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
    if os.path.exists(online_book_html_path):
      os.remove(online_book_html_path)
    subprocess.run(['pandoc', '-s', online_book_md_path,
                              '-o', online_book_html_path])
    book_html = open(online_book_html_path, 'r', encoding='utf-8').read()
    book_html = book_html.replace("</html>", BOOK_ADDED_STYLE)
    open(online_book_html_path, 'w', encoding='utf-8').write(book_html)
    subprocess.run(['node', r'C:\Users\whip\tdr_js\online_content_to_pdf.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
    pdf_toc.main(content_path=online_content_pdf_path, book_pdf_path=online_book_pdf_path, dimensions=PHYS)
  finally:
    server.terminate()


def make_epub():
  print(" == Creating book.html, starting epub at %s" % time.ctime())
  subprocess.run(['pandoc', '-s', online_book_md_path,
                            '-o', online_book_html_path,
                            '--metadata', 'title=One Disease One Cure',
                            '--metadata', 'subtitle=Ending Our Multi-Millennia Catastrophe',
                            '--metadata', 'author=Whip Randolph'])
  subprocess.run(['ebook-convert', online_book_html_path, book_epub_path,
                                   '--cover', cover_dest_path,
                                   '--level1-toc', '//h:h1',
                                   '--level2-toc', '//h:h2',
                                   '--level3-toc', '//h:h3'])
  verify_epub()


def update_images_bw():
  image_names = [
    "hawks_hunting",
    "fredgraph-nairu-unemployment-fedfunds",
    "bulldozer_pic",
    "destroy-kulaks",
    "carrying_a_tree",
    "glowing_heart_chained_heart",
    "black-white-arrest-rate-difference",
    "black-white-prison-education",
    "rise-total-incarceration-usa",
    "guerilla_gardening",
    "american_riot_police",
    "chinese_riot_police",
    "cursed_field",
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
    if os.path.exists(phys_book_html_path):
      os.remove(phys_book_html_path)
    tmp_phys_md_path = "%s_tmp" % phys_book_md_path
    shutil.copyfile(phys_book_md_path, tmp_phys_md_path)
    open(tmp_phys_md_path, 'a', encoding='utf-8').write("\n# Index\n\nfoo")
    subprocess.run(['pandoc', '-s', tmp_phys_md_path, # make pdf w/fake index to get index into ToC correctly
                              '-o', phys_book_html_path])
    book_html = open(phys_book_html_path, 'r', encoding='utf-8').read()
    book_html = book_html.replace("</html>", BOOK_ADDED_STYLE)
    open(phys_book_html_path, 'w', encoding='utf-8').write(book_html)
    subprocess.run(['node', r'C:\Users\whip\tdr_js\phys_content_to_pdf.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
    print("Generating index html...")
    gen_index.main()
    print("Making index into pdf...")
    subprocess.run(['node', r'C:\Users\whip\tdr_js\index.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])

    print("Generating table of contents...")
    pdf_toc.main(content_path=phys_content_pdf_path, book_pdf_path=phys_book_pdf_path_tmp, dimensions=PHYS, is_phys=True)
    os.remove(phys_book_html_path)
    os.remove(tmp_phys_md_path)
    os.remove(phys_book_pdf_path_tmp)
    os.remove(phys_content_pdf_path) # remove content_pdf w/placeholder index
    update_images_bw()
    print("images updated to bw, remaking phys html %s" % time.ctime())
    subprocess.run(['pandoc', '-s', phys_book_md_path, # make pdf w/real index
                              '-o', phys_book_html_path])
    book_html = open(phys_book_html_path, 'r', encoding='utf-8').read()
    book_html = book_html.replace("</html>", BOOK_ADDED_STYLE)
    open(phys_book_html_path, 'w', encoding='utf-8').write(book_html)
    print("Re-creating phys content...")
    subprocess.run(['node', r'C:\Users\whip\tdr_js\phys_content_to_pdf.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
    # add html toc to phys-book-html here
    merger = PdfWriter()
    merger.append(pdf_toc.phys_toc_pdf_path)
    merger.append(phys_content_pdf_path)
    merger.append(index_path)
    merger.write(phys_book_pdf_path)
    merger.close()
  finally:
    server.terminate()
  pass

def cleanup():
  #import pdb;pdb.set_trace()
  print("Cleaning up... (%s)" % time.ctime())
  for filename in os.listdir(book_final):
    path = os.path.join(book_final, filename)
    if online_book_pdf_path != path and phys_book_pdf_path != path and book_epub_path != path:
      if os.path.isdir(path):
        shutil.rmtree(path)
      else:
        os.remove(path)

if __name__ == "__main__":
  main()
