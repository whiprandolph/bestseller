import os
import csv
import toc
import time
import shutil
import markdown2
import subprocess
import traceback
from progress import chapters
from pprint import pprint as pp
from collections import Counter

source_dir = r"C:\Users\whip\tdr"
md_dir = r"C:\Users\whip\tdr-md-publish"
html_dir = r"C:\Users\whip\tdr-book-html"
md_images_dir = os.path.join(source_dir, 'images')
top_images_dir = os.path.join(html_dir, 'images')
pdf_dir = r"C:\Users\whip\tdr-book-pdf"
md_publish_dir = r"C:\Users\whip\tdr-md-publish"
why_so_lost_html = r"C:\Users\whip\tdr-book-html\Part 2 - Why Are We So Lost\06 - Why Are We So Lost.html"
why_so_lost_docx = r"C:\Users\whip\tdr-md-publish\Part 2 - Why Are We So Lost\06 - Why Are We So Lost.docx"
odoc_chapters_root = r"C:\Users\whip\huhc\chapters"
rev_act_path = os.path.join(source_dir, "Scratch", "Revolutionary Activities.md")

PUBLISH = True

had_rev_act_fixup = False
open(rev_act_path, 'w', encoding='utf-8').write("")
odoc_file_list = []
odoc_refs = {}
ref_header = '### References'
full_html = ""
full_html_path = os.path.join(html_dir, 'full_book.html')
REV_ACT_COUNTER = 1 # start at 1
odoc_file_list = []

def rev_act_count_fixup(md_path):
    global REV_ACT_COUNTER, had_rev_act_fixup
    assert md_path.endswith(".md"), md_path
    rev_act_html = '<div class="rev-act"><div class="rev-act-header">Revolutionary Activity #'
    line_list = []
    rev_act_list = []    
    with open(md_path, 'r', encoding='utf-8') as file_handle:
        file_lines = file_handle.readlines()
        for idx, line in enumerate(file_lines):
            if rev_act_html in line:
                assert "<br/>" in line, line
                assert "</div>" in line, line
                act_count, rest_of_line = line.split(rev_act_html)[1].split("<br/>", 1)
                assert (len(act_count) == 1 or len(act_count) == 2) and act_count.isdigit(), "Bad rev-act count: %s in %s" % (act_count, os.path.basename(md_path))
                reassembled_line = f"{rev_act_html}{REV_ACT_COUNTER}<br/>{rest_of_line}"
                if reassembled_line != line:
                   had_rev_act_fixup = True
                line_list.append(reassembled_line)
                rev_act_list.append("".join(("<b>%s</b>" % file_lines[idx], file_lines[idx+1] + "\n")))
                REV_ACT_COUNTER += 1
            elif 'rev-act\"' in line:
                print("Potential rev-act formatting issue with line:")
                print("%s in %s" % (line, md_path))
                breakpoint()
                a = 0
            else:
                line_list.append(line)
    with open(md_path, 'w', encoding='utf-8') as file_handle:
        file_handle.write("".join(line_list))
    
    if had_rev_act_fixup:
        open(rev_act_path, 'w', encoding='utf-8').write("")
    elif rev_act_list:
        output = "### %s\n\n" % os.path.basename(md_path).strip(".md")
        if len(rev_act_list) == 1:
            output += rev_act_list[0]
        else:
            output += "\n\n".join(rev_act_list)
        output += "\n\n"
        open(rev_act_path, 'a', encoding='utf-8').write(output)


def get_file_list(ignore_images = False):
    path_list = []
    chapter_number = 1
    for part_name, chapter_names in chapters.items():
        part_path = os.path.join(source_dir, part_name)
        for a, b, chapter_name in chapter_names:
            if is_chapter_name(chapter_name, part_path):
              chapter_path = os.path.join(part_path, "%02d - %s" % (chapter_number, chapter_name))
              chapter_number += 1
            else:
              chapter_path = os.path.join(part_path, chapter_name)

            if not os.path.exists(chapter_path):
                print("Chapter path does not exist: %s" % chapter_path)
                breakpoint()
            path_list.append(chapter_path)
            
        if not ignore_images:
            images_path = os.path.join(part_path, 'images')
            if os.path.exists(images_path):
                path_list.extend([os.path.join(images_path, x) for x in os.listdir(images_path)])
    return path_list


def get_md(md_path):
    md_contents = open(md_path, 'r', encoding='utf-8').read()
    assert "healthy culture" not in md_contents.lower(), "'healthy culture' in %s" % md_path
    assert "healthy-culture" not in md_contents.lower(), "'healthy-culture' in %s" % md_path
    if not PUBLISH:
        return md_contents
    
    md_contents = md_contents.split("### References")[0]
    if "<toc/>" in md_contents:
        a, b, c = md_contents.split("<toc/>")
        md_contents = a + c
    start = md_contents.find("[xxx")
    cite_number = 1
    while start != -1:
        end = md_contents.find("]", start)+1
        md_contents = md_contents[:start] + str(cite_number) + md_contents[end:]
        start = md_contents.find("[xxx", start+1)
        cite_number+=1
    md_contents = md_contents.replace("<sup>,</sup>",",")
    while "<img" in md_contents:
       start = md_contents.find("<img")
       end = md_contents.find(">", start)
       md_contents = md_contents[:start] + md_contents[end+1:]
    return md_contents


def transform(file_list):
    mdConverter = markdown2.Markdown()
    if os.path.exists(html_dir):
        shutil.rmtree(html_dir)
    os.mkdir(html_dir)
    if os.path.exists(pdf_dir):
        shutil.rmtree(pdf_dir)
    os.mkdir(pdf_dir)
    if os.path.exists(md_publish_dir):
        shutil.rmtree(md_publish_dir)
    os.mkdir(md_publish_dir)
    for file_path in file_list:
        if not os.path.exists(file_path):
            print("not found: %s" % file_path)
            breakpoint()
            a = 4

        if 'images' in file_path:
            html_path = file_path.replace(source_dir, html_dir)
            md_path = file_path.replace(source_dir, md_dir)
            if not os.path.exists(os.path.dirname(html_path)):
                os.mkdir(os.path.dirname(html_path))
            if not os.path.exists(os.path.dirname(md_path)):
                os.mkdir(os.path.dirname(md_path))
            
            # also put image in top-level images dir
            if not os.path.exists(md_images_dir):
                os.mkdir(md_images_dir)
            if not os.path.exists(top_images_dir):
                os.mkdir(top_images_dir)
            top_img_dir_dest_path = os.path.join(top_images_dir, os.path.basename(file_path))
            shutil.copy(file_path, top_img_dir_dest_path)
            shutil.copy(file_path, html_path)
            shutil.copy(file_path, md_path)
            continue
        else:
            md_path = file_path
        
        html_path = md_path.replace(source_dir, html_dir)
        html_path = html_path.replace(".md", ".html")
        pdf_path = md_path.replace(source_dir, pdf_dir)
        pdf_path = pdf_path.replace(".md", ".pdf")
        md_publish_path = md_path.replace(source_dir, md_publish_dir)
        if not os.path.exists(os.path.dirname(html_path)):
            os.mkdir(os.path.dirname(html_path))
        if not os.path.exists(os.path.dirname(md_publish_path)):
            os.mkdir(os.path.dirname(md_publish_path))
        if not os.path.exists(os.path.dirname(pdf_path)):
            os.mkdir(os.path.dirname(pdf_path))
        md_contents = get_md(md_path)
        html = mdConverter.convert(md_contents)
        open(html_path, 'w', encoding='utf-8').write(html)
        open(full_html_path, 'a', encoding='utf-8').write(html)
        open(md_publish_path, 'w', encoding='utf-8').write(md_contents)
        
def is_chapter_name(chapter_name, directory):
  return ("Part Introduction" not in chapter_name and
         is_main_body(chapter_name, directory))
    
def is_pre_or_post_material(chapter_name, directory):
  return ("part 0" in directory.lower() or
          "part 4" in directory.lower())

def is_main_part_intro(chapter_name, directory):
  return ("Part Introduction" in chapter_name and
         is_main_body(chapter_name, directory))

def is_main_body(chapter_name, directory):
  return ("part 1" in directory.lower() or
          "part 2" in directory.lower() or
          "part 3" in directory.lower())


def migrate_citations(file_path):
    blob = open(file_path, 'r', encoding='utf-8').read().strip()
    if ref_header not in blob:
        return [],[],[],[]
    body, ref_section = blob.split(ref_header)
    unchecked_refs = []
    checked_but_unmatched_refs = []
    ref_finished_list = []
    refs = [ref.strip() for ref in ref_section.split("\n") if ref.strip()]
    for ref in refs:
        if '-aaa' in ref:
           ref_finished_list.append(ref)
           continue
        if not "-xxx" in ref:
           unchecked_refs.append(ref)
           continue
        cite = odoc_refs.get(ref.strip("-xxx"))
        if cite:
           ref = ref.replace("-xxx", "-aaa")
           ref_finished_list.append("%s %s" % (ref, cite))
        else:
           checked_but_unmatched_refs.append(ref)

    final_ref_list = unchecked_refs[:]
    final_ref_list.extend(checked_but_unmatched_refs)
    final_ref_list.extend(ref_finished_list)
    new_ref_section = "\n\n" + "\n\n".join(final_ref_list)
    assert len(refs) == len(final_ref_list), "ref replacement gone bad; %s != %s, file %s" % (len(refs), len(ref_finished_list), file_path)
    new_blob = ref_header.join((body, new_ref_section))
    open(file_path, 'w', encoding='utf-8').write(new_blob)
    if unchecked_refs:
        print("UNCHECKED: %s" % str(unchecked_refs))
    return unchecked_refs, checked_but_unmatched_refs, ref_finished_list, final_ref_list


def get_odoc_refs():
    odoc_refs = {}
    for odoc_path in odoc_file_list:
        with open(odoc_path, 'r', encoding='utf-8') as handle:
            blob = handle.read()
            if ref_header not in blob:
               continue
            _, ref_section = blob.split(ref_header)
            new_refs = [odoc_ref.strip().split("-aaa ") for odoc_ref in ref_section.split("\n") if odoc_ref.strip() and "-aaa" in odoc_ref]
            odoc_refs.update({a:b for a, b in new_refs})
    return odoc_refs


def get_exported_refs():
  cites = []
  with open(r"C:\Users\whip\tdr\Scratch\TDR.csv", 'r', encoding='utf-8') as csvfile:
    lines = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(lines, None)
    for pieces in lines:
      if pieces[35]:
        cites.append(pieces[35])
      else:
        print("BIBLIO entry w/o [xxx-cite]: %s" % pieces)
        breakpoint()
  return cites


def odoc_is_chapter_name(chapter_name, chapter_path):
  return 'introduction' not in chapter_name.lower() and 'appendices' not in chapter_path.lower() and "preface material" not in chapter_path.lower() and "part 12" not in chapter_path.lower()

def odoc_get_file_list():
  tocs = {}
  full_list = []
  chapter_number = 0
  for grouping in os.listdir(odoc_chapters_root):
    grouping_path = os.path.join(odoc_chapters_root, grouping)
    if not os.path.isdir(grouping_path) or ("Part 0" not in grouping and "Part 10" not in grouping):
      continue
    
    for idx, chapter_name in enumerate(os.listdir(grouping_path)):
      if 'images' in chapter_name:
        continue
      idx += 1
      non_chapter_path = os.path.join(grouping_path, chapter_name)
      chapter_path = os.path.join(grouping_path, chapter_name)
      document_path = os.path.join(grouping_path, chapter_name)
      if odoc_is_chapter_name(chapter_name, document_path):
        document_path = chapter_path
        chapter_number+=1
      else: 
        document_path = non_chapter_path
      next_toc = {}
      if os.path.exists(document_path):
        try:
          full_list.append(document_path)
        except ValueError as exc:
          raise ValueError("Error: %s\nInvalid file: %s" % (str(exc), document_path))
      else:
        print("WTF path doesn't exist: %s" % document_path)
        import pdb;pdb.set_trace()
        a = 3

  return full_list


def verify_no_extras(total_cites):
    cite_set = set()
    for cite in total_cites:
        if "|" in cite:
            assert cite.count("|") == 1, cite
            cite = cite[:cite.index("|")]+"]"
        if "xxx-bible]" not in cite and "xxx-torah" not in cite and "xxx-quran" not in cite:
            cite_set.add(cite.split("]", 1)[0] + "]")
    exported = get_exported_refs()
    if len(cite_set) != len(exported):
        print("in TDR: %s" % len(cite_set))
        print("in zot: %s" % len(exported))
    for cite in cite_set:
        if cite not in exported:
            print("Ref not in zotero:  %s" % cite)

    for ref in exported:
        if ref not in cite_set:
            print("Ref only in zotero: %s" % ref)

    exp_dupes = [k for k,v in Counter(exported).items() if v>1]
    if exp_dupes:
        print("exported dupes: %s" % exp_dupes)


def main():
    file_list = get_file_list()
    total_unchecked = 0
    total_checked = 0
    total_formatted = 0
    all_refs_set = set()
    for file_path in file_list:
        if '.md' in file_path:
            toc.insert_and_return_toc(file_path)
            rev_act_count_fixup(file_path)
            unchecked_refs, checked_but_unmatched_refs, ref_finished_list, all_refs_chapter = migrate_citations(file_path)
            unchecked_len, checked_len, formatted_len = [len(a) for a in (unchecked_refs, checked_but_unmatched_refs, ref_finished_list)]
            total_unchecked += unchecked_len
            total_checked += checked_len
            total_formatted += formatted_len
            all_refs_set.update(all_refs_chapter)
    total_cites = total_unchecked + total_checked + total_formatted
    print("unchecked: %s (%s%%)" % (total_unchecked, str(round(100*total_unchecked/total_cites,2))))
    print("checked: %s (%s%%)" % (total_checked, str(round(100*total_checked/total_cites,2))))
    print("formatted: %s (%s%%)" % (total_formatted, str(round(100*total_formatted/total_cites,2))))
    print("Unique citations: %s" % len(all_refs_set))
    verify_no_extras(all_refs_set)
    transform(file_list)
    os.chdir(os.path.dirname(why_so_lost_html))
    

odoc_file_list = odoc_get_file_list()
odoc_refs = get_odoc_refs()


if __name__ == '__main__':
    start_time = time.time()
    try:
        main()
    except Exception as exc:
        print("Error: %s" % exc)
        traceback.print_exc()
        breakpoint()
        a = 0
    print("%ss" % round(time.time()-start_time, 2))
