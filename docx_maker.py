import os
import subprocess

def main():

    part1_dir = r"C:\Users\whip\short-odoc\part 1 - Healthy Cultures Do Exist"
    for filename in os.listdir(part1_dir):
        docx_filename = filename.replace(".md", '.docx')
        source_filepath = os.path.join(part1_dir, filename)
        docx_filepath = os.path.join(part1_dir, docx_filename)
        if os.path.exists(docx_filepath):
            os.remove(docx_filepath)
        
        subprocess.run(['pandoc', '-s', source_filepath, '-o', docx_filepath], cwd=part1_dir)

if __name__ == "__main__":
    main()