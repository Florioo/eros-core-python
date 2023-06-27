#!/usr/bin/env python3

from eros import Eros, ErosSerial,ErosTCP,ErosTerminal

# transport = ErosSerial()

transport = ErosTCP("10.172.255.18", 6666)
eros = Eros(transport)
cli = ErosTerminal(eros,5,6)
cli.run()
