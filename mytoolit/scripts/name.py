# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser

from mytoolit.cmdline import base64_mac_address
from mytoolit.utility import convert_base64_mac

# -- Main ---------------------------------------------------------------------


def main():
    parser = ArgumentParser(
        description="Convert the Base64 name of an STH to a MAC address"
    )
    parser.add_argument(
        "name", help="name of the STH e.g. CGvXAd6B", type=base64_mac_address
    )
    name = parser.parse_args().name
    mac = convert_base64_mac(name)
    print(mac)


if __name__ == "__main__":
    main
