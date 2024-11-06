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
                      [-3 [THIRD_CHANNEL]]* (glob)
                      *-d DEVICE_NUMBER) [-s 2–127] (glob)
                      [-a {1,2,3,4,8,16,32,64,128,256}]
                      [-o {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}]
                      [-v {1.25,1.65,1.8,2.1,2.2,2.5,2.7,3.3,5,6.6}]
  
  option.* (re)
    -h, --help            show this help message and exit
  
  Measurement:
    -t* measurement time in seconds (0 for infinite runtime) (glob)
    -1* [FIRST_CHANNEL] (glob)
                          sensor channel number for first measurement channel (1
                          - 255; 0 to disable)
    -2* [SECOND_CHANNEL] (glob)
                          sensor channel number for second measurement channel
                          (1 - 255; 0 to disable)
    -3* [THIRD_CHANNEL] (glob)
                          sensor channel number for third measurement channel (1
                          - 255; 0 to disable)
  
  Sensor Device Identifier:
    -n* Name of sensor device (glob)
    -m* (glob)
                          Bluetooth MAC address of sensor device
    -d* DEVICE_NUMBER (glob)
                          Bluetooth device number of sensor device
  
  ADC:
    -s* 2–127 (glob)
                          Prescaler value
    -a* {1,2,3,4,8,16,32,64,128,256} (glob)
                          Acquisition time value
    -o* {1,2,4,8,16,32,64,128,256,512,1024,2048,4096} (glob)
                          Oversampling rate value
    -v* {1.25,1.65,1.8,2.1,2.2,2.5,2.7,3.3,5,6.6} (glob)
                          Reference voltage in V

Check help output of rename command:

  $ icon rename -h
  usage: icon rename [-h] (-n NAME | -m MAC_ADRESS | -d DEVICE_NUMBER) [name]
  
  positional arguments:
    name                  New name of STH
  
  option.* (re)
    -h, --help            show this help message and exit
  
  Sensor Device Identifier:
    -n* Name of sensor device (glob)
    -m* MAC_ADRESS (glob)
                          Bluetooth MAC address of sensor device
    -d* DEVICE_NUMBER (glob)
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
