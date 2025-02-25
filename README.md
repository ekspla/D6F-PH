# A MicroPython module for differential pressure sensor, D6F-PH (OMRON).
 I2C driver for D6F-PH pressure sensor (OMRON)

This code was tested with MicroPython 1.19.1 - 1.20.0 on STM32F4.
https://github.com/ekspla/D6F-PH

## How to use
**pressure_range** argument ('0505', '0025', '5050') is necessary for the pressure transfer function (defaults to D6F-PH5050), e.g. ```pressure_range='0505'```

 w/o crc check
```Python
>>> from machine import I2C
>>> i2c = I2C(1, freq=400000)
>>> i2c.scan()
[108]
>>> hex(i2c.scan()[0])
'0x6c'
>>> 
>>> from d6f_ph import D6F_PH
>>> sensor = D6F_PH(i2c)
>>> sensor.read_raw()
(31033, 11086)
>>> sensor.read()
(0.04998779, 23.53571) # Pressure/Pa, Temperature/deg.C
>>>
```

 w/ crc check
```Python
>>> from machine import I2C
>>> i2c = I2C(1, freq=400000)
>>> 
>>> from d6f_ph import D6F_PH
>>> sensor = D6F_PH(i2c, en_crc=True)
>>> sensor.read()
(0.1499939, 23.72292)
>>>
```

## Note
Because this sensor utilizes a heater and a pair of thermopile, **it should be placed horizontally**.  Otherwise, you may observe unacceptable offset in measured pressures. 
 An offset (as a raw value; n) can be subtracted by using ```offset=n``` argument.  

## Application Example
This differential pressure sensor can be used as an air speed sensor by using a Pitot tube.  An [example](https://github.com/ekspla/Pitot_GPS_Sensor_Logger/) is shown. 

## License
MIT license.

## Reference
- MEMS Differential pressure Sensor User's Manual; [en-D6F-PH_users_manual.pdf, available from OMRON](https://omronfs.omron.com/en_US/ecb/products/pdf/en-D6F-PH_users_manual.pdf)
- GitHub OMRON(https://github.com/omron-devhub)
