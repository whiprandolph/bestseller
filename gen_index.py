import os
import time
import json
import subprocess
from pprint import pprint as pp
from ttoc import is_chapter_name
from progress import chapters
from pypdf import PdfReader, PdfWriter

md_root_dir = r"C:\Users\whip\tdr\chapters"
book_final = r"C:\Users\whip\tdr_published_files"
index_html = os.path.join(book_final, 'index.html') 
index_pdf = os.path.join(book_final, 'index.pdf') 
chapters_dir = r"C:\Users\whip\tdr\chapters"
terms_path = r"C:\Users\whip\Downloads\Book collaboration tracker - Index.tsv"

content_pdf_path = os.path.join(book_final, r"content_phys.pdf")

pages = []

def is_loc_ant(text, syn_index, ants):
  for ant in ants:
    ant = ant.replace(" ", '')
      
    if text[syn_index:syn_index+len(ant)] == ant:
      return True # false match; assumes ant and syn only differ in endings, ie Indian and India
  return False


def fresh_start_check():
  print("Bypassing new content check in gen_index...")
  new_content = ''
  #new_content = input("new content? > ")
  assert new_content.lower() in ('n', 'y', ''), new_content
  if new_content.lower() != 'n' and os.path.exists('pages.json'):
    os.remove('pages.json')


def check_add_syn(text, index, entry, syn):
  """ return True = keep looking through syns; return False = stop looking through syns, we have a match """
  start = 0
  syn_index = text.find(syn, start)
  while syn_index != -1:
    # verify no ants
    if is_loc_ant(text, syn_index, entry['ants']):
      start = syn_index + len(syn)
      syn_index = text.find(syn, start) # restart search later in page-text
    else:
      entry['pages'].append(index) # "%s [%s]" % (index, text[syn_index:syn_index+len(syn)+10]))
      return True # stop looking through syns

  return False


def page_numbers_from_term(entry):
  for index, text in pages:
    for syn in entry['syns']:
      syn = syn.replace(" ", '') # remove all spaces in pdf and search terms because of pdf reading problems
      if check_add_syn(text, index, entry, syn):
        break

  entry['pages'] = compact_list(entry['pages'])


def read_index_terms():
  terms = {}
  file_contents = open(terms_path, 'r', encoding='utf-8').read()
  auto_terms_blob, manual_terms_blob = file_contents.split("xxxxx")
  for line in auto_terms_blob.split("\n"):
    if line.strip() ==  "":
      continue
    
    pieces = line.strip().split("\t") # only get actual terms
    pieces = [piece.strip() for piece in pieces if piece.strip()]
    if pieces[0] == "": 
      raise Exception("empty first cell, line: %s" % line)

    syns = []
    ants = []
    for extra_term in pieces[1:]:
      if "(" in extra_term and ")" in extra_term:
        ants.append(extra_term.lower().strip("(").strip(")"))
      else:
        syns.append(extra_term.lower())
    syns.append(pieces[0].lower())
    terms[pieces[0]] = {}
    terms[pieces[0]]['term'] = pieces[0]
    terms[pieces[0]]['syns'] = syns
    terms[pieces[0]]['ants'] = ants
    terms[pieces[0]]['pages'] = []
    terms[pieces[0]]['subterms'] = []

  parent_term = None

  for line in manual_terms_blob.split("\n"):
    if line.strip() ==  "":
      continue
    
    pieces = line.strip().split("\t") # only get actual terms
    pieces = [piece.strip() for piece in pieces if piece.strip()]
    if pieces[0] == "": 
      raise Exception("empty first cell, line: %s" % line)

    assert "(see" not in pieces[0]
    elipsis_char = open("elipsis_character.txt", 'r', encoding='utf-8').read()
    if elipsis_char in pieces[0]:
      pieces[0] = pieces[0].replace(elipsis_char, '...')
    if len(pieces) == 2:
      pages = get_manual_pages(pieces[1])
    else:
      assert len(pieces) == 1, pieces
      pages = []
    if '...' not in pieces[0]:
      terms[pieces[0]] = {
          'term':pieces[0],
          'pages':pages,
          'subterms':[],
      }
      parent_term = terms[pieces[0]]
    else:
      parent_term['subterms'].append((pieces[0], pages))
  return terms


def get_manual_pages(pages_str):
  if pages_str.strip() == "":
    return []
  pages_list = []
  if 'see' in pages_str.lower():
    return pages_str.lower()
  pieces = [piece.strip(',') for piece in pages_str.strip().split(" ") if piece.strip(',')]
  for piece in pieces:
    if '-' in piece:
      start, end = piece.split("-")
      pages_list.append((start, end))
    else:
      pages_list.append(piece)

  return pages_list


def format_pages(pages):
  if not pages:
    return ''
  if 'see' in pages:
    return pages
  printable_pages = []
  for item in pages:
    if type(item) == int or type(item) == str:
      printable_pages.append(str(item))
    else:
      assert type(item) == tuple
      start, end = item[0], item[1]
      if int(end) - int(start) == 1:
        printable_pages.append(str(start))
      else:
        printable_pages.append("%s-%s" % (item[0], item[1]))

  return ", ".join(printable_pages)


def printable_entry(term):
  if term.get('subterms'):
    lines = []
    entry_str = "<b>%s</b>" % term['term']
    if term['pages']:
      entry_str += format_pages(term.get('pages'))
    #pp(term)
    #import pdb;pdb.set_trace()
    for subterm, pages in term['subterms']:
      if 'see also' in subterm:
        entry_str += "<br/>%s %s" % (subterm, format_pages(pages))
      else:
        entry_str += "<br/>%s: %s" % (subterm, format_pages(pages))
    return entry_str

  else:
    printable_pages = format_pages(term['pages'])
    
    return "<b>%s</b> %s" % (term['term'], printable_pages)


def write_index(terms):
  table = "<meta charset=\"utf-8\"><style>\n p { font-size: 10.85pt; }\n @page { size: 8.5in 11in; }\n table.cite_table td {font-size:9px;}\n table.index td {max-width: 20em;}\ntable.index_left {width:49%; float:left;}\ntable.index_right {width:49%; float:right;}</style><body><h1>Index</h1>"

  keys = sorted(list(terms.keys()))
  iterable = iter(keys)
  idx = 0
  table_columns = (
    (19,13), 
    (12,16), # 2
    (15,16),
    (13,15), # 4
    (11,12),
    (14,15),  # 6
    (10,4),
    (13,5), # 8
    (7,9), 
    (13,16), # 10
    (10,0), 
  )
  for left, right in table_columns:
    # left
    table += "<table class=\"index index_left\">"
    for x in range(left):
      if idx+x >= len(keys): 
        print('stopped at x-%s/%s' % (x, left))
        break
      entry = terms[keys[idx+x]]
      table += "<tr><td>%s</td><td></td></tr>\n" % printable_entry(entry)
    idx+=left

    table += "</table><table class=\"index index_right\">"
    for y in range(right):
      if idx+y >= len(keys): 
        print('stopped at y-%s/%s' % (y,right))
        break
      entry = terms[keys[idx+y]]
      table += "<tr><td>%s</td><td></td></tr>\n" % printable_entry(entry)
    idx+=right
    table += "</table>"
    table += "<div style=\"break-after:page;clear:both\"></div>"

  assert idx == len(keys), "idx: %s, len(keys): %s" % (idx, len(keys))

  table += "</body>"
  open(index_html, 'w', encoding='utf-8').write(table)


def prep_pages():
  global pages
  if os.path.exists('pages.json'):
    pages = json.load(open('pages.json', 'r', encoding='utf-8'))
    return
  pdf = PdfReader(content_pdf_path) 
  for index, page in enumerate(pdf.pages):
    text = page.extract_text().lower()
    text = text.replace("\n", "")
    text = text.replace(" ", "")
    pages.append((index+1, text))
    if index+1 == 543:
      break # end of appendix 1

  open("pages.json", 'w', encoding='utf-8').write(json.dumps(pages))

def compact_list(orig_list):
  compacted_list = []
  in_span = False
  span_start = -1
  last_page = -1
  for page in orig_list:
    if page - last_page == 1:
      if not in_span: # if this is the second in a span
        in_span = True
        span_start = last_page
        del compacted_list[-1] # will always be something to remove here
      else: # already in span, and it continues
        pass # nothing to do
    else:
      if in_span: # need to end the previous span
        compacted_list.append((span_start, last_page)) 
        span_start = -1
        in_span = False 

      # either way, put this page on the list
      compacted_list.append(page)
    last_page = page
  if in_span:
    compacted_list.append((span_start, last_page))
  return compacted_list
  

def main():
  if os.path.exists(index_html):
    os.remove(index_html)
  if os.path.exists(index_pdf):
    os.remove(index_pdf)
  print("Prepping pdf pages... %s" % time.ctime())
  prep_pages()
  print("Reading... %s" % time.ctime())
  terms = read_index_terms()
  count = 0
  print("Scanning... %s" % time.ctime())
  for term in terms.keys():
    if terms[term]['pages'] or terms[term]['subterms']:
      continue
    page_numbers_from_term(terms[term])
    count += 1
  print("Writing out... %s" % time.ctime())
  write_index(terms)


if __name__ == "__main__":
  main()
  PHYS = {"width":8.5, 'height':11}
#  index_file = open(index_html, 'r', encoding='utf-8').read()
#  index_file = "<html><style>table.index td {font-size:10.85pt;}</style>%s</html>" % index_file
#  open(index_html, 'w', encoding='utf-8').write(index_file)
  server_string = "python -m http.server -d %s" % book_final
  print(" == Starting server again (physical book): %s" % server_string)
  server = subprocess.Popen(server_string) 
  subprocess.run(['node', r'C:\Users\whip\tdr_js\index.js', '--paper-width=%s' % PHYS['width'], '--paper-height=%s' % PHYS['height']])
  server.terminate() 
