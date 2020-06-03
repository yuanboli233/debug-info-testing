import subprocess
import sys

def get_output(binary_file_name : str) -> str:
    ret = subprocess.run(['readelf', '-wL', binary_file_name], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, universal_newlines = True)
    return ret.stdout

def parse_output(output : str, source_file_name : str) -> list:
    lines = output.splitlines()
    is_header = lambda line : len(line) >= len('File name') and line[:len('File name')] == 'File name'
    while len(lines) > 0 and (not is_header(lines[0])):
        lines.pop(0)
    lines.pop(0)
    line_number_set = set()
    for line in lines:
        entries = line.split()
        if len(entries) == 3:
            file_name, line_number, starting_address = entries[0], int(entries[1]), entries[2]
            if file_name == source_file_name:
                line_number_set.add(line_number)
    line_number_list = []
    for line_number in line_number_set:
        line_number_list.append(line_number)
    line_number_list.sort()
    return line_number_list

def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python3 {} <source-file-name(please don't include path)> <binary-file-path>".format(sys.argv[0]))
    line_number_list = parse_output(get_output(sys.argv[2]), sys.argv[1])
    for line_number in line_number_list:
        print(line_number)

main()
