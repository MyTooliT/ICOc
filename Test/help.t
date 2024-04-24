# Check help output

Check help output for main command:

  $ icon --help
  usage: icon [-h] [--log {debug,info,warning,error,critical}]
              {config,dataloss,list,measure,rename,stu} ...
  
  ICOtronic CLI tool
  
  option.* (re)
    -h, --help            show this help message and exit
    --log {debug,info,warning,error,critical}
                          minimum log level
  
  Subcommands:
    {config,dataloss,list,measure,rename,stu}
      config              Open config file in default application
      dataloss            Check data loss at different sample rates
      list                List sensor devices
      measure             Store measurement data
      rename              Rename a sensor device
      stu                 Execute commands related to stationary receiver unit

Check help output of config command:

  $ icon config -h
  usage: icon config [-h]
  
  option.* (re)
    -h, --help  show this help message and exit

Check help output of list command:

  $ icon list -h
  usage: icon list [-h]
  
  option.* (re)
    -h, --help  show this help message and exit

Check help output of measure command:

  $ icon measure --help
  usage: icon measure [-h] [-t TIME] [-1 [FIRST_CHANNEL]] [-2 [SECOND_CHANNEL]]
                      [-3 [THIRD_CHANNEL]]
                      (-n NAME | -m MAC_ADRESS | -d DEVICE_NUMBER) [-s 2–127]
                      [-a {1,2,3,4,8,16,32,64,128,256}]
                      [-o {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}]
                      [-v {1.25,1.65,1.8,2.1,2.2,2.5,2.7,3.3,5,6.6}]
  
  option.* (re)
    -h, --help            show this help message and exit
  
  Measurement:
    -t TIME, --time TIME  measurement time in seconds (0 for infinite runtime)
    -1 [FIRST_CHANNEL], --first-channel [FIRST_CHANNEL]
                          sensor channel number for first measurement channel (1
                          - 255; 0 to disable)
    -2 [SECOND_CHANNEL], --second-channel [SECOND_CHANNEL]
                          sensor channel number for second measurement channel
                          (1 - 255; 0 to disable)
    -3 [THIRD_CHANNEL], --third-channel [THIRD_CHANNEL]
                          sensor channel number for third measurement channel (1
                          - 255; 0 to disable)
  
  Sensor Device Identifier:
    -n NAME, --name NAME  Name of sensor device
    -m MAC_ADRESS, --mac-address MAC_ADRESS
                          Bluetooth MAC address of sensor device
    -d DEVICE_NUMBER, --device-number DEVICE_NUMBER
                          Bluetooth device number of sensor device
  
  ADC:
    -s 2–127, --prescaler 2–127
                          Prescaler value
    -a {1,2,3,4,8,16,32,64,128,256}, --acquisition {1,2,3,4,8,16,32,64,128,256}
                          Acquisition time value
    -o {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}, --oversampling {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}
                          Oversampling rate value
    -v {1.25,1.65,1.8,2.1,2.2,2.5,2.7,3.3,5,6.6}, --voltage-reference {1.25,1.65,1.8,2.1,2.2,2.5,2.7,3.3,5,6.6}
                          Reference voltage in V

Check help output of rename command:

  $ icon rename -h
  usage: icon rename [-h] (-n NAME | -m MAC_ADRESS | -d DEVICE_NUMBER) [name]
  
  positional arguments:
    name                  New name of STH
  
  option.* (re)
    -h, --help            show this help message and exit
  
  Sensor Device Identifier:
    -n NAME, --name NAME  Name of sensor device
    -m MAC_ADRESS, --mac-address MAC_ADRESS
                          Bluetooth MAC address of sensor device
    -d DEVICE_NUMBER, --device-number DEVICE_NUMBER
                          Bluetooth device number of sensor device

Check help output of STU command:

  $ icon stu -h
  usage: icon stu [-h] {ota,mac,reset} ...
  
  option.* (re)
    -h, --help       show this help message and exit
  
  Subcommands:
    {ota,mac,reset}
      ota            Enable “over the air” (OTA) update mode
      mac            Show Bluetooth MAC address
      reset          Reset STU
