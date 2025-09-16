import re
import os
import csv
from ttoc import get_file_list, biblio_csv_path, raw_biblio_path, final_biblio_path
import ttoc
from pprint import pprint as pp
from pprint import pformat


source_dir = r"C:\Users\whip\tdr"
md_dir = r"C:\Users\whip\tdr-md-publish"

def output_biblio(biblio_dict):
    with open(final_biblio_path, 'w', encoding='utf-8') as final_biblio:
        final_biblio.write(f"# Bibliography\n\n<table id=\"biblio_table\"><tbody>")
        for key, value in biblio_dict.items():
            if value['index']:
                final_biblio.write(f"<tr><td colspan=\"2\"><div class=\"biblio-div\" id=\"cite_{value['index']}_dest\"><span style=\"font-weight:bold\">{value['index']}DOTHERE</span> {value['original']}</div></td></tr>\n")

            else:
                final_biblio.write(f"<tr><td colspan=\"2\"><div class=\"biblio-div\">{value['original']}</div></td></tr>\n")
                left_side = True
                for sub_entry in value['sub_entries']:
                    if left_side:
                        final_biblio.write("<tr><td class=\"half-cell\">")
                    else:
                        final_biblio.write("<td>")
                    final_biblio.write(f"\t<div class=\"biblio-div\" id=\"cite_{sub_entry[0]}_dest\"><span style=\"font-weight:bold\">{sub_entry[0]}DOTHERE</span> {sub_entry[2]}</div>\n")
                    if left_side:
                        final_biblio.write("</td>")
                    else:
                        final_biblio.write("</td></tr>")
                    left_side = not left_side
                if not left_side:
                    final_biblio.write("<td class=\"half-cell\"> </td></tr>")

        final_biblio.write("</tbody></table>")


def map_cites():
    """
    1. biblio_dict: create ordered dict of biblio entries that map to sub-bullets of (index, "page 4") or (index, "chapter x") (empty to start)
    {lower_biblio_line: {'index':None, 'sub_entries':list, 'original':Original_line}}
    2. cite_to_biblio_line_dict: create simple cite map of [xxx-foo] -> lower case biblio line
    {'[xxx-foo]':original} # no subcites in this map
    3. cite_to_subcite_dict: Create map of [xxx-foo|bar] -> "Chapter Bar"
    4. Iterate through cite_to_subcite_dict, add line (if not already present) to biblio dict
    5. Go through biblio dict and add indices for all items
    6. cite_to_index_dict: Create map of [xxx] to index, use to fix up book
    """
    biblio_dict = create_biblio_dict()
    cite_to_biblio_line_dict = create_cite_to_biblio_line_dict(biblio_dict)
    cite_to_subcite_dict, cite_to_index_dict = create_cite_to_subcite_and_index_dicts()
    add_subcites_to_biblio(biblio_dict, cite_to_biblio_line_dict, cite_to_subcite_dict)
    output_biblio(biblio_dict)
    create_cite_to_index_dict(cite_to_index_dict, biblio_dict, cite_to_biblio_line_dict, cite_to_subcite_dict)
    return cite_to_index_dict

def create_cite_to_index_dict(cite_to_index_dict, biblio_dict, cite_to_biblio_line_dict, cite_to_subcite_dict):  
    for cite in cite_to_index_dict:
        if "|" in cite:
            top_level_cite = cite.split("|")[0] + "]"
            biblio_line = cite_to_biblio_line_dict[top_level_cite]
            assert biblio_dict[biblio_line]['sub_entries'], biblio_dict[biblio_line]
            for sub_entry in biblio_dict[biblio_line]['sub_entries']:
                if cite_to_subcite_dict[cite] == sub_entry[1]:
                    assert cite == sub_entry[-1], "mismatch cites: %s, %s, %s" % (cite, sub_entry, biblio_dict[biblio_line])
                    cite_to_index_dict[cite] = sub_entry[0]
                    break
        else:
            biblio_line = cite_to_biblio_line_dict[cite]
            assert biblio_dict[biblio_line]['index'], "%s %s" % (cite, biblio_dict[biblio_line])
            cite_to_index_dict[cite] = biblio_dict[biblio_line]['index']
    for cite in cite_to_index_dict:
        if not cite_to_index_dict[cite]:
            print("cite with no index: %s" % cite)

    ttoc_all_lines_set = ttoc.main()
    ttoc_all_refs = set()
    for line in ttoc_all_lines_set:
        ttoc_all_refs.add(line.split("-aaa")[0].strip())

    for line in ttoc_all_lines_set:
        cite = line.split("-aaa")[0].strip()
        count = 0
        for line_ in ttoc_all_lines_set:
            if cite in line_:
                count += 1
        assert count >= 1
        if count > 1:
            print("[xxx-cite points to multiple legibles: %s" % cite)

    for ttoc_cite in ttoc_all_refs:
        for wizard_cite in cite_to_index_dict:
            if ttoc_cite == wizard_cite:
                break
        else:
            print("Unmatched in ttot, not in wizard: %s" % ttoc_cite)

    for wizard_cite in cite_to_index_dict:
        for ttoc_cite in ttoc_all_refs:
            if ttoc_cite == wizard_cite:
                break
        else:
            print("Unmatched in wizard, not in ttoc: %s" % wizard_cite)
    assert len(cite_to_index_dict) == len(ttoc_all_refs), "len mismatch; %s != %s" % (len(cite_to_index_dict), len(ttoc_all_refs))
    return cite_to_index_dict


def add_subcites_to_biblio(biblio_dict, cite_to_biblio_line_dict, cite_to_subcite_dict):
    for cite, subcite in cite_to_subcite_dict.items():
        root_cite = cite
        if "|" in cite:
            root_cite = cite.split("|")[0] + "]"

        biblio_line = cite_to_biblio_line_dict[root_cite]
        prefixed_subcite = subcite # default
        if "the quran" in biblio_line:
            prefixed_subcite = "Verse %s" % subcite
        elif "version bible" in biblio_line:
            pass # go with default of subcite above
        elif subcite.isdigit() or bool(re.search(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$",subcite.upper())):
            prefixed_subcite = "p. %s" % subcite
        elif subcite.count("-") == 1 and subcite.split("-")[0].isdigit() and subcite.split("-")[1].isdigit():
            prefixed_subcite = "pp. %s" % subcite
        else:
            assert subcite.count("\"") == 2, "Error: %s, %s; line: %s" % (cite, subcite, biblio_line)
            if "Chapter" not in subcite:
                prefixed_subcite = "Chapter %s" % subcite
        sub_entry = [None, subcite, prefixed_subcite, cite]
        if sub_entry not in biblio_dict[biblio_line]['sub_entries']:
            biblio_dict[biblio_line]['sub_entries'].append(sub_entry)
    
    # alphabetize subentries and add indices
    biblio_index = 1
    for key in biblio_dict:
        if not biblio_dict[key]['sub_entries']:
            biblio_dict[key]['index'] = biblio_index
            biblio_index += 1
            continue
        else:
            biblio_dict[key]['sub_entries'].sort(key=lambda a:a[1])
            for line in biblio_dict[key]['sub_entries']:
                line[0] = biblio_index
                biblio_index += 1
    # Sanity checks
    for key, value in biblio_dict.items():
        if value['index']: # assert if it does not have index, it has 1+ sub entries
            assert len(value['sub_entries']) == 0, value
        if len(value['sub_entries']) != 0: # vice versa
            assert value['index'] == None, value


def create_cite_to_subcite_and_index_dicts():
    cite_to_subcite_dict = {}
    cite_to_index_dict = {}
    file_list = get_file_list(ignore_images=True)
    for file_path in file_list:
        file_blob = open(file_path, 'r', encoding='utf-8').read().strip()
        if '## References' not in file_blob:
            continue
        aaa_ref_list = [ref.strip() for ref in file_blob.split("## References")[1].split("\n") if "-aaa" in ref]
        for aaa_ref in aaa_ref_list:
            before, after = aaa_ref.split("-aaa ")
            assert before[0] == '[' and before[-1] == ']' and '[xxx-' in before, "before: %s" % before
            assert after[0] == '(' and after[-1] == ')', "after: %s" % after
            cite_to_index_dict[before] = None
            if "|" in before:
                if "The Quran" in after:
                    title, verse, translator = after.split(",")
                    subcite = verse.strip()
                elif "Version Bible" in after:
                    verse, title = after.split(",")
                    subcite = verse.strip().strip("(")
                else:
                    assert after.count(",") >= 2, aaa_ref
                    auth, date, subcite = after.split(",", 2)
                    subcite = subcite.strip().strip(")")
                if before in cite_to_subcite_dict:
                    assert cite_to_subcite_dict[before] == subcite, "map of %s to %s != %s" % (before, cite_to_subcite_dict[before], subcite)
                else:
                    cite_to_subcite_dict[before] = subcite
    for cite in cite_to_subcite_dict:
        if "|" in cite:
            assert cite_to_subcite_dict[cite], "cite %s with bar should map but doesn't" % cite
    return cite_to_subcite_dict, cite_to_index_dict


def create_biblio_dict():
    biblio_dict = {}
   # first clean up punctuation
    biblio = open(raw_biblio_path, 'r', encoding='utf-8').read().strip()
    biblio = biblio.replace("’", "'")
    biblio = biblio.replace("‘", "'")
    biblio = biblio.replace("“", "'")
    biblio = biblio.replace("”", "'")
    biblio = biblio.replace("\"", "'")
    open(raw_biblio_path, 'w', encoding='utf-8').write(biblio) # write out to support scanning later

    csv_file = open(biblio_csv_path, 'r', encoding='utf-8').read().strip()
    csv_file = csv_file.replace("’", "'")
    csv_file = csv_file.replace("‘", "'")
    csv_file = csv_file.replace("“", "'")
    csv_file = csv_file.replace("”", "'")
    open(biblio_csv_path, 'w', encoding='utf-8').write(csv_file) # write out to support scanning later


    biblio_lines = biblio.split("\n")
    assert "# Biblio" in biblio_lines[0], biblio_lines[0]
    assert not biblio_lines[1], biblio_lines[1]
    biblio_lines = biblio_lines[2:]
    for line in biblio_lines:
        biblio_dict[line.lower()] = {'original':line, 'index':None, 'sub_entries':[]}
    return biblio_dict


def create_cite_to_biblio_line_dict(biblio_dict):
    cite_to_biblio_line_dict = {}
    with open(biblio_csv_path, 'r', encoding='utf-8') as csvfile:
        csvlines = csv.reader(csvfile, delimiter=',', quotechar='"')
        next(csvlines, None)
        for pieces in csvlines:
            cite = pieces[35]
            match_count = 0
            found = False
            lower_case_title = pieces[4].lower()[:40]
            assert lower_case_title, "Title required, not present for %s" % str(pieces)
            lower_case_author = pieces[3].lower()
            for biblio_line in biblio_dict.keys():
                if lower_case_title in biblio_line:
                    if 'utopia' in lower_case_title and 'postcolonial' in biblio_line:
                        continue
                        
                    if cite in cite_to_biblio_line_dict:#, "Cite %s already in cite_to_biblio_line_dict %s" % (cite, cite_to_biblio_line_dict)
                        print("dupe cite %s, lower title %s, lower author %s" % (cite, lower_case_title, lower_case_author))
                        breakpoint()
                        a=5
                    cite_to_biblio_line_dict[cite] = biblio_line.lower()
                    found = True
                    # Don't break - make sure we go through whole list to verify no dupes
            if not found:
                print("cite '%s' Not found: %s, %s" % (cite, pieces[3], pieces[4]))
                breakpoint()
    # exclude title and empty second line, verify all keys + values are unique and match
    # expected number of bibliographic lines
    if (len(cite_to_biblio_line_dict) != len(biblio_dict) or \
        set([num for num in cite_to_biblio_line_dict.values() if list(cite_to_biblio_line_dict.values()).count(num) > 1])):
        print("Final cite checks failed: %s %s %s" % (len(cite_to_biblio_line_dict) != len(biblio_dict)-2,
        set([num for num in cite_to_biblio_line_dict.values() if list(cite_to_biblio_line_dict.values()).count(num) > 1])))
        breakpoint()
        a = 5
    return cite_to_biblio_line_dict


def main():
    map_cites()


if __name__ == "__main__":
    main()