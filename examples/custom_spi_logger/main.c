#include "main.h"
#include "gpio.h"
#include "i2c.h"
#include "spi.h"
#include "usart.h"

#define LSM6DS_ADDRESS 0x6B
#define WHO_AM_I_LSM6DS 0x0F // should return 01101010 = 0x6A
#define MC25LCxxx_SPI_RDSR 0x05

void SystemClock_Config(void);

#define MC25LCxxx_SPI_RDID 0xAB
#define MC25LCxxx_SPI_RDSR 0x05
#define MC25LCxxx_SPI_WREN 0x06
#define MC25LCxxx_SPI_WRDI 0x04

static void MC25LC512_ReleaseDeepPowerDownMode(void) {

  unsigned char SendOneByte;
  unsigned char RecieveByteOfReleaseDeepPowerMode = 0;
  SendOneByte = MC25LCxxx_SPI_RDID;


  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6, GPIO_PIN_RESET);

  HAL_SPI_Transmit(&hspi1, &SendOneByte, 1, 200);

  HAL_SPI_Receive(&hspi1, &RecieveByteOfReleaseDeepPowerMode, 1,
                  200); // Address of Manufaturer id High
  HAL_SPI_Receive(&hspi1, &RecieveByteOfReleaseDeepPowerMode, 1,
                  200); // Address of Manufaturer id Low
  HAL_SPI_Receive(&hspi1, &RecieveByteOfReleaseDeepPowerMode, 1,
                  200); // Manufaturer id

  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6, GPIO_PIN_SET);
}

static void MC25LC512_ReadStatusRegister(void) {

  unsigned char SendOneByte = 0;
  unsigned char ReceiveOneByte;
  SendOneByte = MC25LCxxx_SPI_RDSR;

  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6, GPIO_PIN_RESET);
  HAL_SPI_Transmit(&hspi1, &SendOneByte, 1, 200);
  HAL_SPI_Receive(&hspi1, &ReceiveOneByte, 1,
                  200); // Address of Manufaturer id High
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6, GPIO_PIN_SET);
}

static void MC25LC512_WriteEnableOrDisable(unsigned char EnableOrDisable) {
  unsigned char SendOneByte = 0;

  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6, GPIO_PIN_RESET);

  if (EnableOrDisable == 1) {
    SendOneByte = MC25LCxxx_SPI_WREN;
  } else {
    SendOneByte = MC25LCxxx_SPI_WRDI;
  }
  HAL_SPI_Transmit(&hspi1, &SendOneByte, 1, 200);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6, GPIO_PIN_SET);
}


int main(void) {

  HAL_Init();

  SystemClock_Config();

  MX_GPIO_Init();
  MX_SPI1_Init();
  MX_USART3_UART_Init();

  MC25LC512_ReleaseDeepPowerDownMode();
  MC25LC512_ReadStatusRegister();
  MC25LC512_WriteEnableOrDisable(1);

  HAL_Delay(5000);
}

void SystemClock_Config(void) {
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                                RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK) {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC;
  PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV2;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK) {
    Error_Handler();
  }
}

void Error_Handler(void) {
  __disable_irq();
  while (1) {
  }
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line) {}
#endif /* USE_FULL_ASSERT */
