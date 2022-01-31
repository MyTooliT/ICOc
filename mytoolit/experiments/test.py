from mytoolit.config import settings
from mytoolit.cmdline.commander import Commander, CommanderException

if __name__ == '__main__':
    commander = Commander(
        serial_number=settings.sth.programming_board.serial_number,
        chip='BGM113A256V2')
    try:
        commander.enable_debug_mode()
        print("Successfully enabled debug mode for STH")
    except CommanderException as exception:
        print(str(exception))
