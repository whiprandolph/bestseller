import os
import sys
import time
from pprint import pprint as pp

PRINT_BIBLIO_INCOMPLETE_CHAPTERS = False

search_terms = []

def get_pound_count(line):
  count = 0
  idx = 0
  line_len = len(line)
  while idx < line_len and line[idx] == '#':
    count += 1
    idx += 1
  return count

def make_link(line):
  try:
    pounds, title = line.split(" ", 1)
  except ValueError:
    raise ValueError("pounds w/no title: %s" % line)
  title = title.strip()

  link_title = title.replace(" ", "-")
  link_title = link_title.replace(")", "\)")
  link_title = link_title.replace("(", "\(")
  link_title = link_title.lower()
  for char in (":;@,\"'"):
    link_title = link_title.replace(char, "")

  return "[%s](#%s)" % (title, link_title)

def make_toc(toc_links, idx, depth, need_map):
  indent_level = toc_links[idx][1]
  md = ""
  while idx < len(toc_links) and toc_links[idx][1] >= indent_level:
    if toc_links[idx][1] == indent_level:
      md += depth * 2 * " " + "* %s\n" % toc_links[idx][0]
      need = need_map.get(toc_links[idx][0])
      if need:
        md += ((depth * 2) + 2) * " " + "* %s\n" % need
      idx+=1
    else:
      new_md, idx = make_toc(toc_links, idx, depth+1, need_map)
      md += new_md
  return md, idx

def insert_toc(toc, filename):
  with open(filename, 'r', encoding="utf-8") as handle:
    contents = handle.read()
  contents = fill_out_refs(contents, os.path.basename(filename))
  start_idx = contents.find("<toc/>")
  if start_idx == '-1':
    sys.exit("no <toc/> tags in file %s" % filename)
  end_idx = contents.find("<toc/>", start_idx+1)
  if end_idx == '-1':
    sys.exit("no second <toc/> tag in %s" % filename)
  contents = contents[:start_idx+len("<toc/>")] + "\n\n" + toc + contents[end_idx:]
  weird_count = 0 
  while weird_count < 3:
    try:
      file_exists = os.path.exists(filename)
      open(filename, 'w', encoding="utf-8").write(contents)
      weird_count = 3
    except Exception as exc:
      weird_count += 1
      print("weird_count: %s with file %s" % (weird_count, filename))
      if weird_count == 3:
        print(str(file_exists) + " " + str(os.path.exists(filename)))
        print(exc)
        import pdb;pdb.set_trace()
      time.sleep(.5)

def line_search(line, input_filename):
  line = line.lower()
  for term in search_terms:
    if term not in line:
      return
  print("search terms found in %s" % input_filename)
  print("line:    ===%s===\n\n" % line)

def double_cite_search(line):
  pass

def insert_and_return_toc(input_filename):
  #print(input_filename)
  need_map = {}
  try:
    file_blob = open(input_filename, 'r', encoding="utf-8").read()
  except Exception as exc:
    print(exc)
    print("File name: %s" % input_filename)
    import pdb;pdb.set_trace()
    raise
  start_idx = file_blob.find("<toc/>", 1)
  if start_idx == -1:
    start_idx = 0
  file_blob = file_blob[start_idx:]
  lines = file_blob.split("\n")
  toc_links = []
  lower_file_name = input_filename.lower()
  for line in lines:
    line = line.strip()
    if 'biblio' not in lower_file_name:
      assert line.count("_") %2 == 0 or (line.count('_') %2 == 1 and ('cite_table' in line or 'hawks' in line or 'undermining' in line)), "line '%s' has odd count of underscores, file %s" % (line, input_filename)
    if start_idx == 0: continue
    if search_terms:
      line_search(line, input_filename)
    pound_count = get_pound_count(line)
    if pound_count > 0:
        toc_links.append((make_link(line), pound_count))
    if '[NEED' in line and line[0] != '*': # avoid if in the toc
      if len(toc_links) == 0:
        raise Exception("No [NEED] allowed before a header, file %s" % input_filename)
      need_map[toc_links[-1][0]] = line

  if len(toc_links) > 0:
    toc, tmp = make_toc(toc_links, 0, 0, need_map)
    insert_toc(toc, input_filename)
  else:
    # just update references
    with open(input_filename, 'r', encoding="utf-8") as handle:
      contents = handle.read()
    contents = fill_out_refs(contents, os.path.basename(input_filename))
    with open(input_filename, 'w', encoding="utf-8") as handle:
      handle.write(contents)
    return {}
  return toc

def get_refs(contents, is_ref_section = False, chapter_name=""):
  print_chapter_name = False
  refs = []
  if '[xxx' not in contents:
    return refs
  pieces = contents.split("[xxx")[1:]
  for piece in pieces:
    try:
      ref, rest = piece.split("]", 1)
    except Exception as exc:
      print(exc)
      print(pieces)
      breakpoint()
      a=2
    refs.append(ref)
    if is_ref_section and PRINT_BIBLIO_INCOMPLETE_CHAPTERS:
      if not rest.startswith("-aaa"):
        print_chapter_name = True
        print("   " + ref)
  if print_chapter_name:
    print("Unfinished refs in chapter %s" % chapter_name)
  return refs

def ref_check(contents, chapter_name):
  if 'citations' in chapter_name.lower() or 'biblio' in chapter_name.lower(): return
  lines = contents.strip().split("\n")
  count = 1
  for line in lines:
    line = line.strip()
    if not line: continue
    
    # missing xxx-
    #if '[' in line and ']' in line and "xxx-" not in line and line[0] != '*':
    #  print("(%s) Possibly missing xxx- in %s:\n\n%s\n\n" % (count, chapter_name, line))

    # citation at front of line
    if "## References" in line: break
    if line[0] =='[' and '-aaa' not in line:
      print("(%s) Line starts with bracket in %s:\n\n%s\n\n" % (count, chapter_name, line))
    count+=1

def fill_out_refs(contents, chapter_name):
  ref_check(contents, chapter_name)
  if "### Ref" not in contents:
    body_refs = get_refs(contents)
    if not body_refs:
      return contents
    ref_section = ""
    body = contents
  else:
    references_header = "### References"
    body, ref_section = contents.split(references_header)
    body = body.strip()
    ref_section = "%s\n\n" % ref_section.strip()
    body_refs = get_refs(body)
  body_refs = set(body_refs)

  for body_ref in body_refs:
    if ("[xxx%s]" % body_ref) not in ref_section:
      ref_section = "%s[xxx%s]\n\n" % (ref_section, body_ref)
  get_refs(ref_section, True, chapter_name)
  return "%s\n\n### References\n\n%s\n" % (body, ref_section.strip())

if __name__ == "__main__":
  if len(sys.argv) != 2:
    sys.exit("python toc.py [file.md]")
  if not os.path.exists(sys.argv[1]):
    sys.exit("%s not found")
  if not insert_and_return_toc(sys.argv[1]):
    print("no toc")
