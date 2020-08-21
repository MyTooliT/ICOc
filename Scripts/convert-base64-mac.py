# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import argv, exit, stderr
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(abspath(__file__)))
module_path.append(repository_root)

from mytoolit.utility import convert_base64_mac

# -- Functions ----------------------------------------------------------------


def usage(command):
    print(f"Usage: {command} name", file=stderr)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    EXIT_USAGE = 2

    if len(argv) != 2:
        usage(argv[0])
        exit(EXIT_USAGE)

    name = argv[1]
    try:
        if len(name) != 8:
            raise ValueError
        mac = convert_base64_mac(name)
        print(mac)
    except ValueError:
        print(f"Please use a Base64 encoded name with length 8", file=stderr)
        exit(EXIT_USAGE)
