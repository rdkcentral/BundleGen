import subprocess
import json
import click


# goes through directories and selects all files + calculates their SHA1
# returns dictionary (SHA1 - file_path) for every file in directory
# and all its subdirectories
def get_libraries_hashes_in_box_dirs(directories, box_address):
    libs = {}

    for path in directories:
        proc = subprocess.run(["ssh", box_address, "find " + path + " -type f | xargs sha1sum"], stdout=subprocess.PIPE)

        # output is as one long line of text separated by spaces and newlines
        text = proc.stdout.decode("utf-8").split()

        # there are pairs hash + directory. Need to gather them into dictionary
        for i in range(0, len(text), 2):
            libs[text[i]] = text[i+1]

    return libs


@click.command()
@click.argument('file_name')
@click.option('-b', '--box_address', required=True, prompt='Box full address i.e. "root@10.42.0.168', help='User and ip address of box i.e. "root@10.42.0.168"')
def save_box_libs_to_file(file_name, box_address):
    # those paths will be scanned for libraries
    possible_paths = ["/usr/lib", "/lib"]

    box_libraries = get_libraries_hashes_in_box_dirs(possible_paths, box_address)
    with open(file_name, 'w') as file:
        json.dump(box_libraries, file)


if __name__ == '__main__':
    save_box_libs_to_file()

