cmake_minimum_required(VERSION 3.13)

# Board: Raspberry Pi Pico 2 (RP2350). Do not change to pico2_w (wireless variant is out of scope).
set(PICO_BOARD pico2 CACHE STRING "Board type")

# Pico SDK location: export PICO_SDK_PATH=/path/to/pico-sdk (tag 2.2.0, see pico_sdk_version.txt)
if(NOT DEFINED ENV{PICO_SDK_PATH})
    message(FATAL_ERROR "Set PICO_SDK_PATH to a pico-sdk 2.2.0 checkout")
endif()
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(usb_obs_controller C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(usb_obs_controller
    src/main.c
    src/oled.c
)
target_include_directories(usb_obs_controller PRIVATE src)

target_compile_options(usb_obs_controller PRIVATE -Wall -Wextra -Werror=implicit-function-declaration)

target_link_libraries(usb_obs_controller
    pico_stdlib
    hardware_i2c
    hardware_gpio
)

# USB CDC serial is the only stdio channel; UART stdio stays off.
pico_enable_stdio_usb(usb_obs_controller 1)
pico_enable_stdio_uart(usb_obs_controller 0)

pico_add_extra_outputs(usb_obs_controller)
