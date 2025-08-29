# ipcalc.py
Python version of [ipcalc](https://github.com/kjokjo/ipcalc).

IPv4/v6 Calculator
Converted from the original Perl script by Krischan Jodies
Original Copyright (C) Krischan Jodies 2000 - 2021
Python conversion by Gemini 2025

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS for A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

*Disclaimer: Code was converted with Gemini AI assisstance.*

This is the ipv6 capable continuation of the subnet calculator from http://jodies.de/ipcalc. 

<pre>
> python3 ipcalc.py 192.168.1.1/24
Address:   192.168.1.1          11000000.10101000.00000001. 00000001
Netmask:   255.255.255.0 = 24   11111111.11111111.11111111. 00000000
Wildcard:  0.0.0.255            00000000.00000000.00000000. 11111111
=>
Network:   192.168.1.0/24       11000000.10101000.00000001. 00000000
HostMin:   192.168.1.1          11000000.10101000.00000001. 00000001
HostMax:   192.168.1.254        11000000.10101000.00000001. 11111110
Broadcast: 192.168.1.255        11000000.10101000.00000001. 11111111
Hosts/Net: 254                   Class C, Private Internet

> python3 ipcalc.py fde6:36fc:c985:0:c2c1:c0ff:fe1d:cc7f 64
Address: fde6:36fc:c985::c2c1:c0ff:fe1d:cc7f     1111110111100110:0011011011111100:1100100110000101:0000000000000000:1100001011000001:1100000011111111:1111111000011101:1100110001111111
Netmask: 64                                      1111111111111111:1111111111111111:1111111111111111:1111111111111111:0000000000000000:0000000000000000:0000000000000000:0000000000000000
Prefix:  fde6:36fc:c985::/64                     1111110111100110:0011011011111100:1100100110000101:0000000000000000:0000000000000000:0000000000000000:0000000000000000:0000000000000000
