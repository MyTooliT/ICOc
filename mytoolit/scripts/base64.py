# -- Imports ------------------------------------------------------------------

from sys import argv, exit, stderr

from mytoolit.utility import convert_base64_mac

# -- Functions ----------------------------------------------------------------


def usage(command):
    print(f"Usage: {command} name", file=stderr)


# -- Main ---------------------------------------------------------------------


def main():
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
        print("Please use a Base64 encoded name with length 8", file=stderr)
        exit(EXIT_USAGE)


if __name__ == '__main__':
    main
