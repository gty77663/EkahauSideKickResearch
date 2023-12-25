#!/usr/bin/env python

import argparse
from consts import *

BYTEORDER = "big"


class GPIOPin:
    mode = 0
    otype = 0
    ospeed = 0
    pupd = 0
    lck = 0
    afunc = 0

    def __init__(self, index):
        self.index = index

    def set_mode(self, mode: int):
        self.mode = mode

    def set_otype(self, otype: int):
        self.otype = otype

    def set_ospeed(self, ospeed: int):
        self.ospeed = ospeed

    def set_pupd(self, pupd: int):
        self.pupd = pupd

    def set_lck(self, lck: int):
        self.lck = lck

    def set_afunc(self, afunc: int):
        self.afunc = afunc

    def is_input(self):
        return self.mode != PIN_OUTPUT and self.mode != PIN_ALT

    def is_reset_state(self):
        pass

    def generate_report(self):
        desc = f'{self.index}: '
        desc += PIN_MODES[self.mode] + ', '

        if self.mode == PIN_ALT:
            desc += f'AF N.{self.afunc}, '

        if not self.is_input():
            desc += PIN_OTYPE[self.otype] + ', '
            desc += PIN_OSPEED[self.ospeed] + ', '

        desc += PIN_PUPD[self.pupd] + ', '

        desc += PIN_LCK[self.lck]

        return desc


class GPIOPort:
    letter = ''
    raw_data = bytearray()

    def __init__(self, letter: str, data: bytearray):
        self.letter = letter
        self.raw_data = data
        self.pins = []

        self.parse_gpio()

    def parse_gpio(self):
        for pin_n in range(16):
            new_pin = GPIOPin(pin_n)

            # Pin mode
            reg = self.raw_data[GPIO_REGS_OFFSETS['MODER']:GPIO_REGS_OFFSETS['MODER'] + 4]
            new_pin.set_mode((int.from_bytes(reg, BYTEORDER) >> 2 * pin_n) & 0b11)

            if not new_pin.is_input():
                # Output type: push-pull/open-drain
                reg = self.raw_data[GPIO_REGS_OFFSETS['OTYPER']:GPIO_REGS_OFFSETS['OTYPER'] + 4]
                new_pin.set_otype((int.from_bytes(reg, BYTEORDER) >> pin_n) & 0b1)

                # Output speed: low/medium/high
                reg = self.raw_data[GPIO_REGS_OFFSETS['OSPEEDR']:GPIO_REGS_OFFSETS['OSPEEDR'] + 4]
                new_pin.set_ospeed((int.from_bytes(reg, BYTEORDER) >> 2 * pin_n) & 0b11)

            # Pull-up/pull-down
            reg = self.raw_data[GPIO_REGS_OFFSETS['PUPDR']:GPIO_REGS_OFFSETS['PUPDR'] + 4]
            new_pin.set_pupd((int.from_bytes(reg, BYTEORDER) >> 2 * pin_n) & 0b11)

            # Locked pin
            reg = self.raw_data[GPIO_REGS_OFFSETS['LCKR']:GPIO_REGS_OFFSETS['LCKR'] + 4]
            new_pin.set_lck((int.from_bytes(reg, BYTEORDER) >> pin_n) & 0b1)

            # Alternative function
            if new_pin.mode == PIN_ALT:
                if pin_n < 8:
                    reg = self.raw_data[GPIO_REGS_OFFSETS['AFRL']:GPIO_REGS_OFFSETS['AFRL'] + 4]
                    offset = pin_n * 4
                else:
                    reg = self.raw_data[GPIO_REGS_OFFSETS['AFRH']:GPIO_REGS_OFFSETS['AFRH'] + 4]
                    offset = (pin_n - 8) * 4
                new_pin.set_afunc((int.from_bytes(reg, BYTEORDER) >> offset) & 0b1111)

            self.add_pin(new_pin)

    def add_pin(self, pin: GPIOPin):
        self.pins.append(pin)

    def generate_summary(self):
        summary = f'PORT{self.letter}:\n'
        for pin in self.pins:
            summary += f'P{self.letter}' + pin.generate_report() + '\n'

        return summary


arg_parser = argparse.ArgumentParser(
    prog='STM32F0 GPIO parser',
    description='Simple script to parse STM32F0 GPIO registers and make a pin map from binary file '
                'with memory dump.',
    epilog='Text at the bottom of help')

arg_parser.add_argument("filename", help=" Bin/Hex file with memory dump of GPIO registers.", type=str)
arg_parser.add_argument('-O', '--offset', help='Offset in the file if GPIO registers are not located at the start of '
                                               'the file.', required=False, type=int, dest='offset', metavar='HEX')
arg_parser.add_argument("-i", "--inverse", help='Inverse the byte order in registers due to endianness(different '
                                                'programs save binary files and display in different way, so you need'
                                                'to be careful with that). The right way is when the bytes in a '
                                                'register follow the same order as in datasheet.',
                        action='store_true', required=False, dest='inverse_flag')
arg_parser.add_argument('--output', help='If present, the program output will be saved in specified location',
                        required=False, type=str, dest='output', metavar='PATH')

args = arg_parser.parse_args()

with open(args.filename, 'rb') as f:
    file = f.read()
    f.close()

if args.inverse_flag:
    BYTEORDER = "little"

gpio_ports = []
buffer = bytearray()

for port in range(len(file) // 1024):
    buffer = file[port * 1024:(port + 1) * 1024]

    new_port = GPIOPort(GPIO_PORTS_LETTERS[port], buffer)
    gpio_ports.append(new_port)

if args.output is not None:
    output_file = open(args.output, 'w')

for port in gpio_ports:
    port_summary = port.generate_summary()

    if args.output is not None:
        output_file.write(port_summary)

    print(port_summary, end='')

if args.output is not None:
    output_file.close()
