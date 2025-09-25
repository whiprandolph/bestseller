import os
import sys
import ttoc
import time
import shutil
import zipfile
import pdf_toc
import subprocess
from datetime import timedelta
from pprint import pprint as pp
from pypdf import PdfReader, PdfWriter
from ttoc import is_main_part_intro
from progress import chapters 
from prep_book import BOOK_ADDED_STYLE_PHYS, fixup_html, PHYS, process_chapter

import psutil
import signal

# SOURCE_PATH = r"C:\Users\whip\tdr\Part 1 - This Is Who We Really Are\05 - Why Doesn't Everybody Live in This Beautiful Way.md"

SOURCE_PATH = r"C:\Users\whip\tdr\Part 2 - Why Are We So Lost\10 - Why Are People So Racist And Hateful.md"
# SOURCE_PATH = r"C:\Users\whip\tdr\Part 2 - Why Are We So Lost\13 - Can Whole Nations Embrace High Standards.md"
# SOURCE_PATH = r"C:\Users\whip\tdr\Part 2 - Why Are We So Lost\14 - This Pervasive Abuse Must End.md"
# SOURCE_PATH = r"C:\Users\whip\tdr\Part 3 - The Deepest Revolution\17 - Build Spiritual Strength with Others.md"
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
ADD_BLANK_FIRSt_PAGE = True
repo_root_dir = r"C:\Users\whip\tdr"

tmp_dir = r"C:\Users\whip\tdr_published_files\tmp_dir"

chap_ids = set()

def main():
  pdf_path = os.path.join(tmp_dir, "test_chapter.pdf")
  html_path = os.path.join(tmp_dir, "test_chapter.html")
  md_path = os.path.join(tmp_dir, "test_chapter.md")
  md_source = SOURCE_PATH
  kill_librewolf()
  if os.path.exists(tmp_dir):
    shutil.rmtree(tmp_dir)
  os.mkdir(tmp_dir)
  added_page = ""
  if ADD_BLANK_FIRSt_PAGE:
     added_page = "<div style=\"break-after:page\"></div>\n"
  open(md_path, 'w', encoding='utf-8').write(added_page + process_chapter(md_source, {}, fix_citation=True))  
  
  
  subprocess.run(['pandoc', '-s', md_path,
                            '-o', html_path])
  fixup_html(html_path, phys=True)
  print("About to start PDF...")
  
  make_phys_book(html_path, pdf_path)
  subprocess.run([r'C:\Program Files\LibreWolf\librewolf.exe', pdf_path])


def make_phys_book(html_path, pdf_path):
  
  server_string = "python -m http.server -d %s" % tmp_dir
  print(" == Starting server (physical chapter): %s (%s)" % (server_string, time.ctime()))
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