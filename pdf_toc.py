import os
import subprocess
from pprint import pprint as pp
from ttoc import is_chapter_name, is_main_part_intro, is_pre_or_post_material
from pprint import pprint as pprint
from progress import chapters
import datetime
from pypdf import PdfReader, PdfWriter, PageRange

SAMPLE = False
md_root_dir = r"C:\Users\whip\tdr"

book_final = r"C:\Users\whip\tdr_published_files"
chapters_dir = r"C:\Users\whip\tdr"
online_book_html_path = os.path.join(book_final, "book_online.html")
book_epub_path = os.path.join(book_final, "The Deepest Revolution.epub")
book_zip_path = os.path.join(book_final, "The Deepest Revolution.zip")
book_zip_dir = os.path.join(book_final, "The Deepest Revolution -- Zip")
toc_online_pdf_path = os.path.join(book_final, "toc_online.pdf")
toc_phys_pdf_path = os.path.join(book_final, "toc_phys.pdf")
book_cover_path = os.path.join(book_final, "online_front_cover.png")
toc_online_html_path = os.path.join(book_final, "toc_online.html")
toc_phys_html_path = os.path.join(book_final, "toc_phys.html")

PHYS_TOC_MARGIN = '.85'
ONLINE_TOC_MARGIN = '.45'

images_source = r"C:\Users\whip\tdr-book-html\images"
images_dest = os.path.join(book_final, "images")

def get_name(grouping, chapter_name, chapter_number, idx):
  add_to_chapter_counter = 0
  grouping_path = os.path.join(chapters_dir, grouping)
  non_chapter_path = os.path.join(grouping_path, chapter_name)
  chapter_path = os.path.join(grouping_path, "%02d - %s" % (chapter_number, chapter_name))
  document_path = non_chapter_path
  if is_chapter_name(chapter_name, grouping_path):
    add_to_chapter_counter = 1
    name = open(chapter_path, 'r', encoding='utf-8').read().strip().split("\n")[0].split("# ")[1]

  elif is_pre_or_post_material(chapter_name, grouping_path):
    body = open(non_chapter_path, 'r', encoding='utf-8').read().strip()
    name = body.split("\n")[0].split("# ")[1]

  elif is_main_part_intro(chapter_name, grouping):
    name = grouping  
  
  return name, chapter_number+add_to_chapter_counter


def get_page_number(pdf, name, start_page):
  
  print("Name: %s, start page: %s" % (name, start_page))
  for index, page in enumerate(pdf.pages[start_page:]):
    if index+start_page+1 > 235:
      import pdb;pdb.set_trace()
    page_text = page.extract_text().strip()
    first_line = page_text.split("\n")[0]
    line = " ".join([piece for piece in first_line.strip().split(" ") if piece])
    if name[:11] == line[:11]:
      return index+1+start_page
    if name == "Image Credits" and name[:8] == line[:8]:
      return index+1+start_page
  print("ALERT %s not found" % name)
  print("  ==  Is the chapter before '%s' missing a page break?  ==  " % name)
  import pdb;pdb.set_trace()
  a = 5


def prep_pdf_toc(content_path, dimensions, phys):
  pdf = PdfReader(content_path)

  chapter_number = 1
  page_number = 0
  toc_data = {}
  add_part_name = True
  for part in chapters:
    if not part in toc_data:
      toc_data[part] = []
    for index, (a, b, chapter) in enumerate(chapters[part]): 
      name, chapter_number = get_name(part, chapter, chapter_number, index)
      if name.startswith("Part "):
        add_part_name = True
        continue  
      page_number = get_page_number(pdf, name, page_number)
      if add_part_name and not "Part 0" in part:
        toc_data[part].append((part, page_number-1))
        add_part_name = False
      toc_data[part].append((name, page_number))
  
  output_table(toc_data, dimensions, phys)
  verify(toc_data, pdf, phys)


def verify(toc_data, pdf, phys):
  if not phys:
    return
  phys_checks = {
    'chap2':11,
    'chap3':20,
    'chap4':29,
    'chap5':35,
    'chap6':42,
    'chap7':51,
    'chap8':59,
    'chap9':73,
    'chap10':91,
    'chap11':103,
    'chap12':108,
    'chap13':116,
    'chap14':133,
    'chap15':147,
    'chap16':154,
    'chap17':168,
    'chap18':182,
    'page_count':197,
  }
  online_checks = {
    'chap2':11,
    'chap8':61,
    'chap15':135,
    'page_count':185,
  }
  
  checks = online_checks
  if phys:
    checks = phys_checks

  # sanity checks
  try:
    assert checks['chap2'] == toc_data["Part 1 - This Is Who We Really Are"][2][1], "chapter 2 page num off (exp: %s, is: %s)" % (checks['chap2'], toc_data["Part 1 - This Is Who We Really Are"][2][1])
    assert checks['chap3'] == toc_data["Part 1 - This Is Who We Really Are"][3][1], "chapter 3 page num off (exp: %s, is: %s)" % (checks['chap3'], toc_data["Part 1 - This Is Who We Really Are"][3][1])
    assert checks['chap4'] == toc_data["Part 1 - This Is Who We Really Are"][4][1], "chapter 4 page num off (exp: %s, is: %s)" % (checks['chap4'], toc_data["Part 1 - This Is Who We Really Are"][4][1])
    assert checks['chap5'] == toc_data["Part 1 - This Is Who We Really Are"][5][1], "chapter 5 page num off (exp: %s, is: %s)" % (checks['chap5'], toc_data["Part 1 - This Is Who We Really Are"][5][1])
    assert checks['chap6'] == toc_data["Part 2 - Why Are We So Lost"][1][1], "chap 6 page num is off (exp: %s, is: %s)" % (checks['chap6'], toc_data["Part 2 - Why Are We So Lost"][1][1])
    assert checks['chap7'] == toc_data["Part 2 - Why Are We So Lost"][2][1], "chap 7 page num is off (exp: %s, is: %s)" % (checks['chap7'], toc_data["Part 2 - Why Are We So Lost"][2][1])
    assert checks['chap8'] == toc_data["Part 2 - Why Are We So Lost"][3][1], "chap 8 page num is off (exp: %s, is: %s)" % (checks['chap8'], toc_data["Part 2 - Why Are We So Lost"][3][1])
    assert checks['chap9'] == toc_data["Part 2 - Why Are We So Lost"][4][1], "chap 9 page num is off (exp: %s, is: %s)" % (checks['chap9'], toc_data["Part 2 - Why Are We So Lost"][4][1])
    assert checks['chap10'] == toc_data["Part 2 - Why Are We So Lost"][5][1], "chap 10 page num is off (exp: %s, is: %s)" % (checks['chap10'], toc_data["Part 2 - Why Are We So Lost"][5][1])
    assert checks['chap11'] == toc_data["Part 2 - Why Are We So Lost"][6][1], "chap 11 page num is off (exp: %s, is: %s)" % (checks['chap11'], toc_data["Part 2 - Why Are We So Lost"][6][1])
    assert checks['chap12'] == toc_data["Part 2 - Why Are We So Lost"][7][1], "chap 12 page num is off (exp: %s, is: %s)" % (checks['chap12'], toc_data["Part 2 - Why Are We So Lost"][7][1])
    assert checks['chap13'] == toc_data["Part 2 - Why Are We So Lost"][8][1], "chap 13 page num is off (exp: %s, is: %s)" % (checks['chap13'], toc_data["Part 2 - Why Are We So Lost"][8][1])
    assert checks['chap14'] == toc_data["Part 2 - Why Are We So Lost"][9][1], "chap 14 page num is off (exp: %s, is: %s)" % (checks['chap14'], toc_data["Part 2 - Why Are We So Lost"][9][1])
    assert checks['chap15'] == toc_data["Part 3 - The Deepest Revolution"][1][1], "chap 15 page num is off (exp: %s, is: %s)" % (checks['chap15'], toc_data["Part 3 - The Deepest Revolution"][1][1])
    assert checks['chap16'] == toc_data["Part 3 - The Deepest Revolution"][2][1], "chap 16 page num is off (exp: %s, is: %s)" % (checks['chap16'], toc_data["Part 3 - The Deepest Revolution"][2][1])
    assert checks['chap17'] == toc_data["Part 3 - The Deepest Revolution"][3][1], "chap 17 page num is off (exp: %s, is: %s)" % (checks['chap17'], toc_data["Part 3 - The Deepest Revolution"][3][1])
    assert checks['chap18'] == toc_data["Part 3 - The Deepest Revolution"][4][1], "chap 18 page num is off (exp: %s, is: %s)" % (checks['chap18'], toc_data["Part 3 - The Deepest Revolution"][4][1])
    assert len(pdf.pages) == checks['page_count'], "Incorrect page count (phys=%s): found: %s, expected: %s" % (phys, len(pdf.pages), checks['page_count']) # excludes title/toc pages

    assert toc_data["Part 1 - This Is Who We Really Are"][0][1] % 2 == 1, "part 1 page num is even"
    assert toc_data["Part 2 - Why Are We So Lost"][0][1] % 2 == 1, "part 2 page num is even"
    assert toc_data["Part 3 - The Deepest Revolution"][0][1] % 2 == 1, "part 3 page num is even"
  except AssertionError as exc:
    pp(toc_data)
    print("ERROR in ToC Validation (phys=%s): %s" % (phys, exc))
    import pdb;pdb.set_trace()


def write_toc_line(md, name, page_number):
  md.write("<a class=\"toc-link\" href=\"#link_to_heading\">\n")
  md.write("<span class=\"title\">%s<span class=\"leaders\" aria-hidden=\"true\"></span></span>\n" % name)
  md.write("<span class=\"page\"><span class=\"visually-hidden\">Page</span> %s</span>\n" % page_number)
  md.write("</a>\n")

def output_table(toc_data, dimensions, phys):
  toc_html_path = toc_online_html_path
  if phys:
    toc_html_path = toc_phys_html_path
  md = open(toc_html_path, encoding='utf-8', mode='w')
  md.write("<html><title>The Deepest Revolution</title>\n")
  if phys:
    updated_css = css % PHYS_TOC_MARGIN
  else:
    updated_css = css % ONLINE_TOC_MARGIN
  md.write("<style>\n%s\n</style>\n" % updated_css)
  print("pdf_toc: dimensions=%s" % dimensions)
  if dimensions:
    md.write("<style>\n@page {size: %sin %sin; }\n</style>\n" % (dimensions['width'], dimensions['height']))

  md.write("<body>\n\n<br/><br/><br/><br/><br/><br/><br/><br/><br/>")
  md.write("<center><span style=\"font-size:35pt;font-weight:bold\">The<br/>Deepest Revolution</span><br/><br/><br/>\n\n")
  md.write("<h2>William Randolph</h2><br/></center>\n\n")
  md.write("<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>\n\n")
  md.write("<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>\n\n")
  md.write("<center>Copyright 2025 William Randolph</center>\n\n")
  md.write("<div style=\"break-after:page\"></div>\n")
  md.write("<div style=\"margin-top:1in\"><center><b>Table of Contents</b></center></div>\n")
  md.write("<ol class=\"toc-list\" role=\"list\">\n")

  for part in toc_data:
    if 'Part 0 ' in part or 'Part 4' in part:
      for name, page_number in toc_data[part]:
        md.write("<li>\n")
        write_toc_line(md, name, page_number)
        md.write("</li>\n")
    else:
      md.write("<li>\n")
      writeable = part.replace("？", '?')
      write_toc_line(md, writeable, toc_data[part][0][1])
      md.write("<ol role=\"list\">\n")
      for name, page_number in toc_data[part][1:]:
        md.write("<li>\n")
        writeable = name.replace("？", '?')
        write_toc_line(md, writeable, page_number)
        md.write("</li>\n")
      md.write("</ol>\n")
      md.write("</li>\n")

  md.write("</ol>\n\n")
  md.write("</body></html>\n\n")
  md.close()

  print("  == Making ToC PDF\n")
  if phys:
    subprocess.run(['node', r'C:\Users\whip\tdr_js\phys_toc_to_pdf.js'])
  else:
    subprocess.run(['node', r'C:\Users\whip\tdr_js\online_toc_to_pdf.js'])

def merge_pdfs(content_path, book_pdf_path, phys):
  toc_pdf_path = toc_online_pdf_path
  if phys:
    toc_pdf_path = toc_phys_pdf_path
  print("  == Merging PDFs (toc path: %s)\n" % toc_pdf_path)
  pdfs = [toc_pdf_path, content_path]

  merger = PdfWriter()
  for pdf in pdfs:
    merger.append(pdf)

  merger.write(book_pdf_path)
  merger.close()

def sample_pdf(book_pdf_path):
  part_two_path = book_pdf_path + " - part 2 %s.pdf" % datetime.datetime.now().strftime("%B %d %p")
  part_one_path = book_pdf_path + " - part 1 %s.pdf" % datetime.datetime.now().strftime("%B %d %p")
  part_3_path = book_pdf_path + " - part 3 %s.pdf" % datetime.datetime.now().strftime("%B %d %p")
  bib_path = book_pdf_path + " - bib %s.pdf" % datetime.datetime.now().strftime("%B %d %p")

  bib = PdfWriter()
  bib.append(book_pdf_path, pages=PageRange("185:193"))
  bib.write(bib_path)
  bib.close()

  print("  == Sampling PDF\n")
  part_two = PdfWriter()
  part_two.append(book_pdf_path, pages=PageRange("1"))
  part_two.append(book_pdf_path, pages=PageRange("41:144"))
  part_two.write(part_two_path)
  part_two.close()

  part_two_reader = PdfReader(part_two_path)
  try:
    assert "Table of Contents" in part_two_reader.pages[0].extract_text(), "Part 2 page count change caused the excerpt to be misaligned (ToC)"
    assert "Why Are We So Lost" in part_two_reader.pages[1].extract_text(), "Part 2 page count change caused the excerpt to be misaligned (title page)"
    assert "paths to creating a new" in part_two_reader.pages[-1].extract_text(), "Part 2 page count change caused the excerpt to be misaligned (ending)"
  except AssertionError as exc:
    print(exc)
    breakpoint()
    a = 4 

  part_3 = PdfWriter()
  part_3.append(book_pdf_path, pages=PageRange("1"))
  part_3.append(book_pdf_path, pages=PageRange("144:184"))
  part_3.write(part_3_path)
  part_3.close()

  part_3_reader = PdfReader(part_3_path)
  try:
    assert "Table of Contents" in part_3_reader.pages[0].extract_text(), "Part 3 page count change caused the excerpt to be misaligned (ToC)"
    assert "Deepest Revolution" in part_3_reader.pages[1].extract_text(), "Part 3 page count change caused the excerpt to be misaligned (title page)"
    assert "reciprocity with people and the Earth. (3, 15)" in part_3_reader.pages[-1].extract_text(), "Part 3 page count change caused the excerpt to be misaligned (ending)"
  except AssertionError as exc:
    print(exc)
    breakpoint()
    a = 4 

  part_one = PdfWriter()
  part_one.append(book_pdf_path, pages=PageRange("1"))
  part_one.append(book_pdf_path, pages=PageRange("4:41"))
  part_one.write(part_one_path)
  part_one.close()

  part_one_reader = PdfReader(part_one_path)
  try:
    assert "Table of Contents" in part_one_reader.pages[0].extract_text(), "Part 1 page count change caused the excerpt to be misaligned (ToC)"
    assert "This Is Who We Really Are" in part_one_reader.pages[1].extract_text(), "Part 1 page count change caused the excerpt to be misaligned (title page)"
    assert "Many people avoid watching" in part_one_reader.pages[-1].extract_text(), "Part 1 page count change caused the excerpt to be misaligned (ending)"
  except AssertionError as exc:
    print(exc)
    breakpoint()
    a = 4 

def main(content_path, book_pdf_path, dimensions, phys):
  prep_pdf_toc(content_path, dimensions, phys)
  merge_pdfs(content_path, book_pdf_path, phys)
  if not phys and SAMPLE:
    sample_pdf(book_pdf_path)

css = """
html {
  font-size:11.5pt;
}

.visually-hidden {
    clip: rect(0 0 0 0);
    clip-path: inset(100%%);
    height: 1px;
    overflow: hidden;
    position: absolute;
    width: 1px;
    white-space: nowrap;
}

.toc-link {
  color: black;
  hover: blue;
}

.toc-list, .toc-list ol {
  list-style-type: none;
}

.toc-list {
  padding-right: %sin;
  padding-left: .45in;
}

.toc-list ol {
  padding-inline-start: 1ch;
}

.toc-list > li > a {
  font-weight: bold;
  margin-block-start: 1em;
}

.toc-list li > a {
    text-decoration: none;
    display: grid;
    grid-template-columns: auto max-content;
    align-items: end;
}

.toc-list li > a > .title {
    position: relative;
    overflow: hidden;
}

.toc-list li > a .leaders::after {
    position: absolute;
    padding-inline-start: .25ch;
    content: " . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . "
        ". . . . . . . . . . . . . . . . . . . . . . . ";
    text-align: right;
}

.toc-list li > a > .page {
    min-width: 2ch;
    font-variant-numeric: tabular-nums;
    text-align: right;
}
"""

if __name__ == "__main__":
  main(r'C:\Users\whip\book_final\content_phys.pdf', r'C:\Users\whip\book_final\book-phys.pdf')
