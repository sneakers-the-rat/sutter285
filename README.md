# sutter285
Programmatically control the position of a Sutter 285 micromanipulator

Basic functionality provided in example.

Typical use case is to instantiate the object and set positions as needed.

Basic and badly implemented logging keeps track of when the manipulator was where.

```python
from sutter285 import Sutter
sut = Sutter(port="COM5", logfile="/some/log/file.csv")

# set an x, y, z position (microns)
sut.set_position((100, 100, 100))
```


Only position getting/setting has been implemented, other commands like switching manipulators should be trivial to add <3

serial command documentation is here:
https://www.sutter.com/SOFTWARE/USBv3.pdf
