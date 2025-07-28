import os
import subprocess
from pprint import pprint as pp
from ttoc import is_chapter_name, is_main_part_intro, is_pre_or_post_material
from pprint import pprint as pprint
from progress import chapters
from pypdf import PdfReader, PdfWriter, PageRange

md_root_dir = r"C:\Users\whip\tdr"

book_final = r"C:\Users\whip\tdr_published_files"
chapters_dir = r"C:\Users\whip\tdr"
online_book_html_path = os.path.join(book_final, "book_online.html")
book_epub_path = os.path.join(book_final, "The Deepest Revolution.epub")
book_zip_path = os.path.join(book_final, "The Deepest Revolution.zip")
book_zip_dir = os.path.join(book_final, "The Deepest Revolution -- Zip")
toc_pdf_path = os.path.join(book_final, "toc.pdf")
book_cover_path = os.path.join(book_final, "online_front_cover.png")
toc_html_path = os.path.join(book_final, "toc.html")

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
    name = open(non_chapter_path, 'r', encoding='utf-8').read().strip().split("\n")[0].split("# ")[1]

  elif is_main_part_intro(chapter_name, grouping):
    name = grouping  
  
  return name, chapter_number+add_to_chapter_counter


def get_page_number(pdf, name, start_page):
  
  print("Name: %s, start page: %s" % (name, start_page))
  for index, page in enumerate(pdf.pages[start_page:]):
    if index+start_page+1 > 177:
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


def prep_pdf_toc(content_path, dimensions={}):
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
  
  output_table(toc_data, dimensions)
  verify(toc_data, pdf)


def verify(toc_data, pdf):
  # sanity checks
  try:
    print("*** Add sanity checks! ***")
    #assert 'Chapter 10' in toc_data["Part 03 - Gift Economy vs Profit Economy"][2][0] and 94 == toc_data["Part 03 - Gift Economy vs Profit Economy"][2][1], "gift/profit"
    #assert 'Chapter 18' in toc_data["Part 05 - Heart-Opening vs Heart-Closing"][2][0] and 170 == toc_data["Part 05 - Heart-Opening vs Heart-Closing"][2][1], "heart"
    #assert 'Chapter 34' in toc_data["Part 08 - Unhealthy Cultures Sabotage Relationships"][2][0] and 351 == toc_data["Part 08 - Unhealthy Cultures Sabotage Relationships"][2][1], "sabotage"
    #assert 'Appendix 2' in toc_data["Part 11 - Appendices"][2][0] and 543 == toc_data["Part 11 - Appendices"][2][1], "appendices"
    #assert len(pdf.pages) == 605 or len(pdf.pages) == 562, len(pdf.pages)
  except AssertionError as exc:
    pp(toc_data)
    print("ERROR in ToC Validation: %s" % exc)
    import pdb;pdb.set_trace()


def write_toc_line(md, name, page_number):
  md.write("<a class=\"toc-link\" href=\"#link_to_heading\">\n")
  md.write("<span class=\"title\">%s<span class=\"leaders\" aria-hidden=\"true\"></span></span>\n" % name)
  md.write("<span class=\"page\"><span class=\"visually-hidden\">Page</span> %s</span>\n" % page_number)
  md.write("</a>\n")

def output_table(toc_data, dimensions={}):
  md = open(toc_html_path, encoding='utf-8', mode='w')
  md.write("<html><title>The Deepest Revolution</title>\n")
  md.write("<style>\n%s\n</style>\n" % css)
  print("pdf_toc: dimensions=%s" % dimensions)
  if dimensions:
    md.write("<style>\n@page {size: %sin %sin; }\n</style>\n" % (dimensions['width'], dimensions['height']))

  md.write("<body>\n\n")
  md.write("<center><h2>The<br/>Deepest Revolution</h2><br/>\n\n")
  md.write("<h2>DRAFT</h2><br/>\n\n")
  md.write("<h4>William Randolph</h4><br/></center>\n\n")

  md.write("<div style=\"break-after:always\"></div><div style=\"break-after:page\"></div>\n")
  md.write("<center><b>Table of Contents</b></center>\n")
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
  subprocess.run(['node', r'C:\Users\whip\tdr_js\toc_to_pdf.js'])

def merge_pdfs(content_path, book_pdf_path):
  print("  == Merging PDFs (toc path: %s)\n" % toc_pdf_path)
  pdfs = [toc_pdf_path, content_path]

  merger = PdfWriter()
  for pdf in pdfs:
    merger.append(pdf)

  merger.write(book_pdf_path)
  merger.close()

def sample_pdf(book_pdf_path):
  print("  == Sampling PDF\n")
  merger = PdfWriter()
  merger.append(book_pdf_path, pages=PageRange("1"))
  merger.append(book_pdf_path, pages=PageRange("40:119"))
  merger.write(book_pdf_path + " - part 2 Jul 28 pm.pdf")
  merger.close()

  part_one = PdfWriter()
  part_one.append(book_pdf_path, pages=PageRange("1"))
  part_one.append(book_pdf_path, pages=PageRange("5:44"))
  part_one.write(book_pdf_path + " - part 1 Jul 28 pm.pdf")
  part_one.close()


def main(content_path, book_pdf_path, dimensions={}):
  prep_pdf_toc(content_path, dimensions)
  merge_pdfs(content_path, book_pdf_path)
  sample_pdf(book_pdf_path)


css = """
.visually-hidden {
    clip: rect(0 0 0 0);
    clip-path: inset(100%);
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
  padding: 0;
}

.toc-list ol {
  padding-inline-start: 2ch;
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
