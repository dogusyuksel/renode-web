//
// Copyright (c) 2010-2026 Antmicro
//
// This file is licensed under the MIT License.
// Full license text is available in 'licenses/MIT.txt'.
//
using Antmicro.Renode.Core;
using Antmicro.Renode.Core.Structure.Registers;
using Antmicro.Renode.Logging;
using Antmicro.Renode.Peripherals.Bus;
using Antmicro.Renode.Peripherals.Timers;

namespace Antmicro.Renode.Peripherals.Miscellaneous
{
    [AllowedTranslations(AllowedTranslation.ByteToDoubleWord | AllowedTranslation.WordToDoubleWord)]
    public class STM32F103_RCC : BasicDoubleWordPeripheral, IKnownSize
    {
        public STM32F103_RCC(IMachine machine, IPeripheral rtc = null, IHasDivisibleFrequency systick = null,
            long hseFrequency = DefaultHseFrequency, long hsiFrequency = DefaultHsiFrequency) : base(machine)
        {
            if(systick == null)
            {
                this.Log(LogLevel.Warning, "Systick not passed in the RCC constructor. Changes to the system clock will be ignored");
            }
            this.systick = systick;

            if(rtc == null)
            {
                this.Log(LogLevel.Warning, "RTC not passed in the RCC constructor. Changes to the real-time clock will be ignored");
            }
            this.rtc = rtc;

            this.hseFrequency = hseFrequency;
            this.hsiFrequency = hsiFrequency;

            DefineRegisters();
            Reset();
        }

        public override void Reset()
        {
            pllMultiplier = 2;
            pllSource = PllClockSource.HsiDiv2;
            pllHseDivisor = 1;
            if(systick != null)
            {
                systick.Divider = 1;
            }
            base.Reset();
            UpdateSystemClock();
        }

        public long Size => 0x400;

        private void DefineRegisters()
        {
            Registers.ClockControl.Define(this, 0x00000083)
                .WithFlag(0, out var hsion, name: "HSION")
                .WithFlag(1, FieldMode.Read, valueProviderCallback: _ => hsion.Value, name: "HSIRDY")
                .WithReservedBits(2, 1)
                .WithValueField(3, 5, name: "HSITRIM")
                .WithValueField(8, 8, FieldMode.Read, name: "HSICAL", valueProviderCallback: _ => 0x10)
                .WithFlag(16, out var hseon, name: "HSEON")
                .WithFlag(17, FieldMode.Read, valueProviderCallback: _ => hseon.Value, name: "HSERDY")
                .WithFlag(18, name: "HSEBYP")
                .WithTag("CSSON", 19, 1)
                .WithReservedBits(20, 4)
                .WithFlag(24, out pllOn, name: "PLLON")
                .WithFlag(25, FieldMode.Read, valueProviderCallback: _ => pllOn.Value, name: "PLLRDY")
                .WithFlag(26, out var pll2on, name: "PLL2ON")
                .WithFlag(27, FieldMode.Read, valueProviderCallback: _ => pll2on.Value, name: "PLL2RDY")
                .WithFlag(28, out var pll3on, name: "PLL3ON")
                .WithFlag(29, FieldMode.Read, valueProviderCallback: _ => pll3on.Value, name: "PLL3RDY")
                .WithReservedBits(30, 2)
                .WithWriteCallback((_, __) => UpdateSystemClock())
                ;

            Registers.ClockConfiguration.Define(this)
                .WithEnumField<DoubleWordRegister, SystemClockSourceSelection>(0, 2, out systemClockSwitch, name: "SW")
                .WithValueField(2, 2, FieldMode.Read, name: "SWS", valueProviderCallback: _ => (ulong)systemClockSwitch.Value)
                .WithValueField(4, 4, name: "HPRE",
                    writeCallback: (previous, value) =>
                    {
                        if(systick == null || previous == value)
                        {
                            return;
                        }

                        if(value < 0b1000)
                        {
                            systick.Divider = 1;
                        }
                        else
                        {
                            systick.Divider = 1 << ((int)(value & 0b111) + 1);
                        }
                        this.Log(LogLevel.Debug, "systick clock divisor changed to {0}", systick.Divider);
                    })
                .WithValueField(8, 3, name: "PPRE1")
                .WithValueField(11, 3, name: "PPRE2")
                .WithValueField(14, 2, name: "ADCPRE")
                .WithFlag(16, name: "PLLSRC",
                    writeCallback: (previous, value) =>
                    {
                        if(pllOn.Value && previous != value)
                        {
                            this.Log(LogLevel.Error, "PLLSRC modified while PLL is enabled");
                        }
                        pllSource = value ? PllClockSource.Hse : PllClockSource.HsiDiv2;
                    })
                .WithFlag(17, name: "PLLXTPRE",
                    writeCallback: (previous, value) =>
                    {
                        if(pllOn.Value && previous != value)
                        {
                            this.Log(LogLevel.Error, "PLLXTPRE modified while PLL is enabled");
                        }
                        pllHseDivisor = value ? 2 : 1;
                    })
                .WithValueField(18, 4, name: "PLLMUL",
                    writeCallback: (previous, value) =>
                    {
                        if(pllOn.Value && previous != value)
                        {
                            this.Log(LogLevel.Error, "PLLMUL modified while PLL is enabled");
                        }
                        pllMultiplier = value >= 0b1110 ? 16 : (long)value + 2;
                    })
                .WithFlag(22, name: "USBPRE")
                .WithReservedBits(23, 1)
                .WithValueField(24, 3, name: "MCO")
                .WithReservedBits(27, 5)
                .WithWriteCallback((_, __) => UpdateSystemClock())
                ;

            Registers.ClockInterrupt.Define(this)
                .WithFlag(0, FieldMode.Read, valueProviderCallback: _ => lsiReadyInterruptEnable.Value, name: "LSIRDYF")
                .WithFlag(1, FieldMode.Read, valueProviderCallback: _ => lseReadyInterruptEnable.Value, name: "LSERDYF")
                .WithFlag(2, FieldMode.Read, valueProviderCallback: _ => hsiReadyInterruptEnable.Value, name: "HSIRDYF")
                .WithFlag(3, FieldMode.Read, valueProviderCallback: _ => hseReadyInterruptEnable.Value, name: "HSERDYF")
                .WithFlag(4, FieldMode.Read, valueProviderCallback: _ => pllReadyInterruptEnable.Value, name: "PLLRDYF")
                .WithReservedBits(5, 2)
                .WithTaggedFlag("CSSF", 7)
                .WithFlag(8, out lsiReadyInterruptEnable, name: "LSIRDYIE")
                .WithFlag(9, out lseReadyInterruptEnable, name: "LSERDYIE")
                .WithFlag(10, out hsiReadyInterruptEnable, name: "HSIRDYIE")
                .WithFlag(11, out hseReadyInterruptEnable, name: "HSERDYIE")
                .WithFlag(12, out pllReadyInterruptEnable, name: "PLLRDYIE")
                .WithReservedBits(13, 3)
                .WithFlag(16, FieldMode.Write, writeCallback: (_, value) => { if(value) { lsiReadyInterruptEnable.Value = false; } }, name: "LSIRDYC")
                .WithFlag(17, FieldMode.Write, writeCallback: (_, value) => { if(value) { lseReadyInterruptEnable.Value = false; } }, name: "LSERDYC")
                .WithFlag(18, FieldMode.Write, writeCallback: (_, value) => { if(value) { hsiReadyInterruptEnable.Value = false; } }, name: "HSIRDYC")
                .WithFlag(19, FieldMode.Write, writeCallback: (_, value) => { if(value) { hseReadyInterruptEnable.Value = false; } }, name: "HSERDYC")
                .WithFlag(20, FieldMode.Write, writeCallback: (_, value) => { if(value) { pllReadyInterruptEnable.Value = false; } }, name: "PLLRDYC")
                .WithReservedBits(21, 2)
                .WithTaggedFlag("CSSC", 23)
                .WithReservedBits(24, 8)
                ;

            Registers.Apb2PeripheralReset.Define(this)
                .WithTaggedFlag("AFIORST", 0)
                .WithReservedBits(1, 1)
                .WithTaggedFlag("IOPARST", 2)
                .WithTaggedFlag("IOPBRST", 3)
                .WithTaggedFlag("IOPCRST", 4)
                .WithTaggedFlag("IOPDRST", 5)
                .WithTaggedFlag("IOPERST", 6)
                .WithTaggedFlag("IOPFRST", 7)
                .WithTaggedFlag("IOPGRST", 8)
                .WithTaggedFlag("ADC1RST", 9)
                .WithTaggedFlag("ADC2RST", 10)
                .WithTaggedFlag("TIM1RST", 11)
                .WithTaggedFlag("SPI1RST", 12)
                .WithTaggedFlag("TIM8RST", 13)
                .WithTaggedFlag("USART1RST", 14)
                .WithTaggedFlag("ADC3RST", 15)
                .WithReservedBits(16, 3)
                .WithTaggedFlag("TIM9RST", 19)
                .WithTaggedFlag("TIM10RST", 20)
                .WithTaggedFlag("TIM11RST", 21)
                .WithReservedBits(22, 10)
                ;

            Registers.Apb1PeripheralReset.Define(this)
                .WithTaggedFlag("TIM2RST", 0)
                .WithTaggedFlag("TIM3RST", 1)
                .WithTaggedFlag("TIM4RST", 2)
                .WithTaggedFlag("TIM5RST", 3)
                .WithTaggedFlag("TIM6RST", 4)
                .WithTaggedFlag("TIM7RST", 5)
                .WithReservedBits(6, 5)
                .WithTaggedFlag("WWDGRST", 11)
                .WithReservedBits(12, 2)
                .WithTaggedFlag("SPI2RST", 14)
                .WithTaggedFlag("SPI3RST", 15)
                .WithReservedBits(16, 1)
                .WithTaggedFlag("USART2RST", 17)
                .WithTaggedFlag("USART3RST", 18)
                .WithTaggedFlag("UART4RST", 19)
                .WithTaggedFlag("UART5RST", 20)
                .WithTaggedFlag("I2C1RST", 21)
                .WithTaggedFlag("I2C2RST", 22)
                .WithTaggedFlag("USBRST", 23)
                .WithTaggedFlag("CANRST", 24)
                .WithReservedBits(25, 2)
                .WithTaggedFlag("BKPRST", 27)
                .WithTaggedFlag("PWRRST", 28)
                .WithTaggedFlag("DACRST", 29)
                .WithReservedBits(30, 2)
                ;

            Registers.AhbPeripheralClockEnable.Define(this, 0x00000014)
                .WithFlag(0, name: "DMA1EN")
                .WithFlag(1, name: "DMA2EN")
                .WithFlag(2, name: "SRAMEN")
                .WithReservedBits(3, 1)
                .WithFlag(4, name: "FLITFEN")
                .WithReservedBits(5, 1)
                .WithFlag(6, name: "CRCEN")
                .WithReservedBits(7, 1)
                .WithFlag(8, name: "FSMCEN")
                .WithReservedBits(9, 1)
                .WithFlag(10, name: "SDIOEN")
                .WithReservedBits(11, 21)
                ;

            Registers.Apb2PeripheralClockEnable.Define(this)
                .WithFlag(0, name: "AFIOEN")
                .WithReservedBits(1, 1)
                .WithFlag(2, name: "IOPAEN")
                .WithFlag(3, name: "IOPBEN")
                .WithFlag(4, name: "IOPCEN")
                .WithFlag(5, name: "IOPDEN")
                .WithFlag(6, name: "IOPEEN")
                .WithFlag(7, name: "IOPFEN")
                .WithFlag(8, name: "IOPGEN")
                .WithFlag(9, name: "ADC1EN")
                .WithFlag(10, name: "ADC2EN")
                .WithFlag(11, name: "TIM1EN")
                .WithFlag(12, name: "SPI1EN")
                .WithFlag(13, name: "TIM8EN")
                .WithFlag(14, name: "USART1EN")
                .WithFlag(15, name: "ADC3EN")
                .WithReservedBits(16, 3)
                .WithFlag(19, name: "TIM9EN")
                .WithFlag(20, name: "TIM10EN")
                .WithFlag(21, name: "TIM11EN")
                .WithReservedBits(22, 10)
                ;

            Registers.Apb1PeripheralClockEnable.Define(this)
                .WithFlag(0, name: "TIM2EN")
                .WithFlag(1, name: "TIM3EN")
                .WithFlag(2, name: "TIM4EN")
                .WithFlag(3, name: "TIM5EN")
                .WithFlag(4, name: "TIM6EN")
                .WithFlag(5, name: "TIM7EN")
                .WithReservedBits(6, 5)
                .WithFlag(11, name: "WWDGEN")
                .WithReservedBits(12, 2)
                .WithFlag(14, name: "SPI2EN")
                .WithFlag(15, name: "SPI3EN")
                .WithReservedBits(16, 1)
                .WithFlag(17, name: "USART2EN")
                .WithFlag(18, name: "USART3EN")
                .WithFlag(19, name: "UART4EN")
                .WithFlag(20, name: "UART5EN")
                .WithFlag(21, name: "I2C1EN")
                .WithFlag(22, name: "I2C2EN")
                .WithFlag(23, name: "USBEN")
                .WithFlag(24, name: "CANEN")
                .WithReservedBits(25, 2)
                .WithFlag(27, name: "BKPEN")
                .WithFlag(28, name: "PWREN")
                .WithFlag(29, name: "DACEN")
                .WithReservedBits(30, 2)
                ;

            Registers.BackupDomainControl.Define(this)
                .WithFlag(0, out var lseon, name: "LSEON")
                .WithFlag(1, FieldMode.Read, valueProviderCallback: _ => lseon.Value, name: "LSERDY")
                .WithFlag(2, name: "LSEBYP")
                .WithReservedBits(3, 5)
                .WithValueField(8, 2, name: "RTCSEL")
                .WithReservedBits(10, 5)
                .WithFlag(15, writeCallback: (_, value) =>
                    {
                        if(rtc == null)
                        {
                            return;
                        }
                        sysbus.SetPeripheralEnabled(rtc, value);
                    },
                    valueProviderCallback: _ => rtc == null ? false : sysbus.IsPeripheralEnabled(rtc),
                    name: "RTCEN")
                .WithTaggedFlag("BDRST", 16)
                .WithReservedBits(17, 15)
                ;

            Registers.ControlStatus.Define(this, 0x0C000001)
                .WithFlag(0, out var lsion, name: "LSION")
                .WithFlag(1, FieldMode.Read, valueProviderCallback: _ => true, name: "LSIRDY")
                .WithReservedBits(2, 22)
                .WithTaggedFlag("RMVF", 24)
                .WithTaggedFlag("PINRSTF", 26)
                .WithTaggedFlag("PORRSTF", 27)
                .WithTaggedFlag("SFTRSTF", 28)
                .WithTaggedFlag("IWDGRSTF", 29)
                .WithTaggedFlag("WWDGRSTF", 30)
                .WithTaggedFlag("LPWRRSTF", 31)
                ;

            Registers.AhbPeripheralReset.Define(this)
                .WithTaggedFlag("USBOTGFSRST", 12)
                .WithTaggedFlag("ETHMACRST", 14)
                .WithReservedBits(0, 12)
                .WithReservedBits(13, 1)
                .WithReservedBits(15, 17)
                ;

            Registers.ClockConfiguration2.Define(this)
                .WithValueField(0, 4, name: "PREDIV1")
                .WithValueField(4, 4, name: "PREDIV2")
                .WithValueField(8, 4, name: "PLL2MUL")
                .WithValueField(12, 4, name: "PLL3MUL")
                .WithFlag(16, name: "PREDIV1SRC")
                .WithFlag(17, name: "I2S2SRC")
                .WithFlag(18, name: "I2S3SRC")
                .WithReservedBits(19, 13)
                .WithWriteCallback((_, __) => UpdateSystemClock())
                ;
        }

        private void UpdateSystemClock()
        {
            if(systick == null)
            {
                return;
            }

            var old = systick.Frequency;
            switch(systemClockSwitch.Value)
            {
            case SystemClockSourceSelection.Hsi:
                systick.Frequency = hsiFrequency;
                break;
            case SystemClockSourceSelection.Hse:
                systick.Frequency = hseFrequency;
                break;
            case SystemClockSourceSelection.Pll:
                if(!pllOn.Value)
                {
                    this.Log(LogLevel.Warning, "Systick source set to PLL when PLL is disabled");
                }
                systick.Frequency = PllFrequency;
                break;
            default:
                this.Log(LogLevel.Warning, "Reserved system clock source selected: {0}", systemClockSwitch.Value);
                systick.Frequency = hsiFrequency;
                break;
            }

            if(old != systick.Frequency)
            {
                this.Log(LogLevel.Debug, "systick clock frequency changed to {0}. Current effective frequency: {1}",
                    systick.Frequency, systick.Frequency / systick.Divider);
            }
        }

        private long PllFrequency
        {
            get
            {
                var input = pllSource == PllClockSource.Hse ? hseFrequency / pllHseDivisor : hsiFrequency / 2;
                return input * pllMultiplier;
            }
        }

        private IEnumRegisterField<SystemClockSourceSelection> systemClockSwitch;
        private IFlagRegisterField pllOn;
        private IFlagRegisterField lsiReadyInterruptEnable;
        private IFlagRegisterField lseReadyInterruptEnable;
        private IFlagRegisterField hsiReadyInterruptEnable;
        private IFlagRegisterField hseReadyInterruptEnable;
        private IFlagRegisterField pllReadyInterruptEnable;

        private PllClockSource pllSource;
        private long pllMultiplier;
        private long pllHseDivisor;

        private readonly long hseFrequency;
        private readonly long hsiFrequency;
        private readonly IHasDivisibleFrequency systick;
        private readonly IPeripheral rtc;

        private const long DefaultHseFrequency = 8000000;
        private const long DefaultHsiFrequency = 8000000;

        private enum SystemClockSourceSelection
        {
            Hsi,
            Hse,
            Pll,
            Reserved,
        }

        private enum PllClockSource
        {
            HsiDiv2,
            Hse,
        }

        private enum Registers
        {
            ClockControl = 0x00,
            ClockConfiguration = 0x04,
            ClockInterrupt = 0x08,
            Apb2PeripheralReset = 0x0C,
            Apb1PeripheralReset = 0x10,
            AhbPeripheralClockEnable = 0x14,
            Apb2PeripheralClockEnable = 0x18,
            Apb1PeripheralClockEnable = 0x1C,
            BackupDomainControl = 0x20,
            ControlStatus = 0x24,
            AhbPeripheralReset = 0x28,
            ClockConfiguration2 = 0x2C,
        }
    }
}
