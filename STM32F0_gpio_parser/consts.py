PIN_INPUT = 0b00
PIN_OUTPUT = 0b01
PIN_ALT = 0b10
PIN_ANALOG = 0b11

GPIO_REGS_OFFSETS = {
    'MODER': 0x00,
    'OTYPER': 0x04,
    'OSPEEDR': 0x08,
    'PUPDR': 0x0C,
    'LCKR': 0x1C,
    'AFRL': 0x20,
    'AFRH': 0x24
}

GPIO_PORTS_LETTERS = {
    0: 'A',
    1: 'B',
    2: 'C',
    3: 'D',
    4: 'E',
    5: 'F'
}

PIN_MODES = {
    0b00: 'Input mode',
    0b01: 'Output mode',
    0b10: 'Alternative function',
    0b11: 'Analog mode'
}

PIN_OTYPE = {
    0b00: 'Output push-pull',
    0b01: ' Output open-drain',
    0b10: 'Invalid OTYPE',
    0b11: 'Invalid OTYPE'
}

PIN_OSPEED = {
    0b00: 'Low speed',
    0b01: 'Medium speed',
    0b10: 'Low speed',
    0b11: 'High speed',
}

PIN_PUPD = {
    0b00: 'No pull-up/down',
    0b01: 'Pull-up',
    0b10: 'Pull-down',
    0b11: 'Invalid PUPD'
}

PIN_LCK = {
    0b0: 'No lock',
    0b01: 'Locked pin'
}