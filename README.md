# Ekahau SideKick 1 reverse engineering
To start, I just want to say that this is a pretty much useless project, because of very little number of such devices manufactured. 
The first reason for me of doing such deep investigation is to repair one of these devices, 
and than I got kinda carried away and started digging deeper to have fun and to learn, and hopefully for you to enjoy.

## Device architecture & description
The PCB is composed of two main blocks:
* A STM32F030 MCU, responsible of basic functions, like powering on the device, battery management and handling the buttons & LEDs.
* And an Embedian SMARC FiMX6 module, with few ICs for PCIe multiplexing, USB & Bluetooth communications, etc., handling main features like WIFI scanning and spectrum analysis.

The MCU and the SMARC module are connected and communicating through a UART bus.

## The actual "research"
Initially I got my hands on one SideKick, that was not booting, the LED was flashing, but after few seconds was turning off.
My first thought is to identify the guilty block, if it is the MCU or the compute module.   

### Finding the snitch

#### SMARC FiMX6 debug console
After tickling the board with multimeter's probes, I found that the LEDs and the buttons are connected to the STM32F030, 
so preliminarily we can assume that the MCU is good and passed the snitch exam.  
Than, according to the SMARC FiMX6 user manual, the SER3 interface is used for the debug console and, what a coincidence, 
exposed on one of the debug headers on the PCB. Thank you, Ekahau! After connecting my UART adapter - complete silence there.  
Still, I was not convinced and was still hopping that the compute module was OK(because, a little spoiler, it is around ~180 USD with shipping).

#### Communication between blocks
The next step is to find how the MCU and the IMX6 communicate, so the STM can give the user some feedback with the LEDs.  
To do so, the first step is to find the pins of the communication bus, and only then the protocol used.
To our luck and for whatever reason the SWD interface and the memory of the MCU are not locked, 
so what I came up with(and what other smarter people came up with a long time before me), 
was to determine the pin configuration based on STM32F030 GPIO registers, that are accessible with a SWD debugger.  

##### Understanding the GPIO configuration of the STM32F030
To those, who are not very familiar with STM32 microcontrollers(just as I was and still am lol) I'll clarify.
STM32 microcontrollers have only few GPIO configuration register that are interesting for us: 

* GPIOx_MODER, it is used to configure the function of a GPIO pin y, of a port x. Each MODER register for each port is 32 bit long
and divided to 16 2-bit long blocks, one block per pin of port x. Each block can have 4 binary values, the one that we are interested in is 10 in binary, 
because this would attribute an alternative function to the pin. This is important as all communication protocols use pin's alternative functions. 
To clarify you can look at the picture below from the STM32F030x8 reference manual. Hopefully that helps!
<img src="https://github.com/Foxdogface/EkahauSideKickResearch/blob/main/assets/STM32_GPIOx_MODER.PNG" width="500"/>

* The next pair of registers are GPIOx_AFRL & GPIOx_AFRH, GPIO alternative function low & high registers accordingly  
The low register is responsible for pin 0-7 and the high for pins 8-15. These registers are also divided to blocks, 
but in this case they are 4-bit long and there are 8 of them in each registers. 
Each 4-bit block selects the alternative function number for the corresponding pin.  
The images below should give you a better understanding of the process.
<p float=left>
  <img src="https://github.com/Foxdogface/EkahauSideKickResearch/blob/main/assets/STM32_GPIOx_AFR_combined.png" height="430"/>
  <img src="https://github.com/Foxdogface/EkahauSideKickResearch/blob/main/assets/STM32_GPIOA_AF_TABLE.png" height="430"/>
</p>

##### Reversing the pinout of the STM32F030
So, now, that we understand how the GPIO configuration of STM32F030 works we can actually reverse the communication bus pins beetween the MCU and the SMARC module.
First, we need actually to read the register values, located at following base addresses with offsets of 0x00 for MODR reg, 0x20 for AFRL and 0x24 for AFRH.
<img src="https://github.com/Foxdogface/EkahauSideKickResearch/blob/main/assets/STM32_GPIO_REGISTERS_OFFSET.png" height="300"/>
<img src="https://github.com/Foxdogface/EkahauSideKickResearch/blob/main/assets/STM32_GPIO_MEMORY_MAP.png" height="316"/>

## Debug headers pinout
There are 3 headers on the main PCB(neither of them has a reference designator, I'll call them J1, J2 and J3):
1. SMARC IMX6, 20 pin, 1mm pitch, J1 header  
  
|              |        |        |            |
|--------------|--------|--------|------------|
| GND          | **20** | **19** | SER3_TX    |
| GND          | **18** | **17** | SER3_RX    |
| PEX_VDD_CORE | **16** | **15** | PA5        |
| IO_PWR_OFF*  | **14** | **13** | RST_IN#    |
| PWR_ON_BTN   | **12** | **11** | TEST#      |
| GbE_MDI1‐    | **10** | **9**  | GbE_MDI1+  |
| GbE_MDI0‐    | **8**  | **7**  | GbE_MDI0+  |
| GbE_CTREF    | **6**  | **5**  | VDD3       |
| VDD_IN_SMARC | **4**  | **3**  | BUCK_SYNC* |
| GND          | **2**  | **1**  | GND        |

* - If pulled-down turns off IO_VVD(PCIe multiplexer, USB hub, ) 3.3V line + 1.8V linear voltage converter.

2. STM32F030 SWD, 10 pin, 1mm pitch, J2 header

|        |        |       |     |
|--------|--------|-------|-----|
| nRST   | **10** | **9** | GND |
| NC     | **8**  | **7** | KEY |
| NC     | **6**  | **5** | GND |
| SWDCLK | **4**  | **3** | GND |
| SWDIO  | **2**  | **1** | VCC |

3. BOOT_SEL, 10 pin, 2.54mm, J3 header   
This is a block of jumpers, and there is one installed from factory, between pins 10 & 9.  
Because there is no silkscreen on the PCB it's difficult to tell which pin is considered the 1st one, 
so I assume that it is the one in the down right corner, as it's shown on the photo down below.  

|          |        |       |                         |
|----------|--------|-------|-------------------------|
| GND*     | **10** | **9** | Phase2 voltage switch** |
| ?        | **8**  | **7** | GND                     |
| BOOTSEL2 | **6**  | **5** | GND                     |
| BOOTSEL1 | **4**  | **3** | GND                     |
| BOOTSEL0 | **2**  | **1** | GND                     |

* - only connected to GND when spectrum analyzer pcie module is inserted
** -  This pin goes to a resistor, connected to phase 2 FB pin.
      When it gets connected to ground, the resistor devider switches the output voltage from 3.3V to 5V for the spectrum analyzer.
