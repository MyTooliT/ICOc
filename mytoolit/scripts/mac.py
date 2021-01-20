# -- Imports ------------------------------------------------------------------

from sys import argv, exit, stderr

from mytoolit.utility import convert_mac_base64

# -- Functions ----------------------------------------------------------------


def usage(command):
    print(f"Usage: {command} MAC", file=stderr)


# -- Main ---------------------------------------------------------------------


def main():
    EXIT_USAGE = 2

    if len(argv) != 2:
        usage(argv[0])
        exit(EXIT_USAGE)

    mac_input = argv[1]
    mac = mac_input.split(":")

    try:
        if len(mac) != 6:
            raise ValueError
        mac = [int(byte, 16) for byte in mac]
        name = convert_mac_base64(mac)
        print(name)
    except ValueError:
        print(f"Please use a MAC address of the form xx:xx:xx:xx:xx:xx",
              file=stderr)
        exit(EXIT_USAGE)


if __name__ == '__main__':
    main()
