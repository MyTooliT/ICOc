# -- Imports ------------------------------------------------------------------

from mytoolit.old import Network

# -- Main ---------------------------------------------------------------------


def main():
    network = Network()

    network.__exit__()  # Cleanup resources (read thread)


if __name__ == '__main__':
    main()
