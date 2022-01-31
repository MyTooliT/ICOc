from mytoolit.config import settings
from mytoolit.cmdline.commander import Commander

if __name__ == '__main__':
    commander = Commander(
        serial_number=settings.sth.programming_board.serial_number,
        chip='BGM113A256V2')
    power_usage = commander.read_power_usage()
    print(f"Power Usage: {power_usage} mW")
