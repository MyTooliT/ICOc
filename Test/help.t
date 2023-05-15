# Check help output

Check help output for main command:

  $ icon --help
  usage: icon [-h] {list,measure,rename,stu} ...
  
  ICOtronic CLI tool
  
  option.* (re)
    -h, --help            show this help message and exit
  
  Subcommands:
    {list,measure,rename,stu}
      list                List sensor devices
      measure             Store measurement data
      rename              Rename a sensor device
      stu                 Execute commands related to stationary receiver unit

Check help output of list command:

  $ icon list -h
  usage: icon list [-h]
  
  option.* (re)
    -h, --help  show this help message and exit

Check help output of measure command:

  $ icon measure --help
  usage: icon measure [-h] [-t TIME]
                      (-n NAME | -m MAC_ADRESS | -d DEVICE_NUMBER)
  
  option.* (re)
    -h, --help            show this help message and exit
    -t TIME, --time TIME  measurement time in seconds
    -n NAME, --name NAME  Name of sensor device
    -m MAC_ADRESS, --mac-address MAC_ADRESS
                          Bluetooth MAC address of sensor device
    -d DEVICE_NUMBER, --device-number DEVICE_NUMBER
                          Bluetooth device number of sensor device

Check help output of rename command:

  $ icon rename -h
  usage: icon rename [-h] (-n NAME | -m MAC_ADRESS | -d DEVICE_NUMBER) [name]
  
  positional arguments:
    name                  New name of STH
  
  option.* (re)
    -h, --help            show this help message and exit
    -n NAME, --name NAME  Name of sensor device
    -m MAC_ADRESS, --mac-address MAC_ADRESS
                          Bluetooth MAC address of sensor device
    -d DEVICE_NUMBER, --device-number DEVICE_NUMBER
                          Bluetooth device number of sensor device

Check help output of STU command:

  $ icon stu -h
  usage: icon stu [-h] {ota,mac} ...
  
  option.* (re)
    -h, --help  show this help message and exit
  
  Subcommands:
    {ota,mac}
      ota       Enable “over the air” (OTA) update mode
      mac       Show Bluetooth MAC address
