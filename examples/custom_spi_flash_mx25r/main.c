#include "main.h"
#include "gpio.h"
#include "i2c.h"
#include "spi.h"
#include "usart.h"
#include "printf.h"
#include <string.h>

#define BLS_CODE_DP 0xB9  /**< Power down */
#define BLS_CODE_RDP 0xAB /**< Power standby */
#define BLS_CODE_MDID 0x9F         /**< Manufacturer Device ID */

void SystemClock_Config(void);

void uart_log(const char *format, ...) {
  va_list arguments;
  char buffer[128] = {0};

  va_start(arguments, format);
  vsnprintf_(buffer, sizeof(buffer), format, arguments);
  va_end(arguments);

  if (strlen(buffer) == 0) {
    return;
  }

  HAL_UART_Transmit(&huart3, (uint8_t *)buffer, strlen((char *)buffer),
                    strlen((char *)buffer));
}

static void extFlashSelect(void) {
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6, GPIO_PIN_RESET);
}

static void extFlashDeselect(void) {
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_6, GPIO_PIN_SET);
}

static int extFlashPowerStandby(void) {
  uint8_t cmd = BLS_CODE_RDP;
  int ret = HAL_ERROR;

  extFlashSelect();
  ret = HAL_SPI_Transmit(&hspi1, &cmd, 1, 200);
  extFlashDeselect();

  return ret;
}

static int ExtFlash_readInfo(void) {
  int ret = HAL_OK;

  uint8_t tx_buf[4] = { BLS_CODE_MDID, 0x00, 0x00, 0x00 }; // 1 komut + 3 dummy
  uint8_t rx_buf[4] = {0};  
  extFlashSelect();
  HAL_SPI_TransmitReceive(&hspi1, tx_buf, rx_buf, 4, 200);
  extFlashDeselect();

  uart_log("rx_buf: %X %X %X\r\n",
        rx_buf[1], rx_buf[2], rx_buf[3]);

  return ret;
}

static int extFlashPowerDown(void) {
  uint8_t cmd = BLS_CODE_DP;
  int ret = HAL_ERROR;

  extFlashSelect();
  ret = HAL_SPI_Transmit(&hspi1, &cmd, 1, 200);
  extFlashDeselect();

  return ret;
}

int main(void) {

  HAL_Init();

  SystemClock_Config();

  MX_GPIO_Init();
  MX_SPI1_Init();
  MX_USART3_UART_Init();

  /* Put the part is standby mode */
  extFlashPowerStandby();

  HAL_Delay(1000);

  /* Verify manufacturer and device ID */
  ExtFlash_readInfo();
  HAL_Delay(1000);

  // Put the part in low power mode
  extFlashPowerDown();

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
