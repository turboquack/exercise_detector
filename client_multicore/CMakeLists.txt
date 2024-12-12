# Set minimum required version of CMake
cmake_minimum_required(VERSION 3.13)

# Include build functions from Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

# Set name of project (as PROJECT_NAME) and C/C   standards
set(PICO_BOARD pico_w)
project(client_multicore C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(PICO_BOARD pico_w)
# Creates a pico-sdk subdirectory in our project for the libraries
pico_sdk_init()

include_directories( 
        ${CMAKE_CURRENT_LIST_DIR}
        ${CMAKE_CURRENT_LIST_DIR}/.. # for our common lwipopts
        )

add_subdirectory(icm20948)
add_subdirectory(lps22hb)
include_directories(./icm20948)
include_directories(./lps22hb)

# Tell CMake where to find the executable source file
add_executable(${PROJECT_NAME} 
    main.c
)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(${PROJECT_NAME})

# Link to pico_stdlib (gpio, time, etc. functions)
target_link_libraries(${PROJECT_NAME} 
    pico_stdlib
    hardware_i2c
    icm20948 	
    lps22hb
    pico_cyw43_arch_lwip_threadsafe_background
    pico_multicore
)

# Enable usb output, disable uart output
pico_enable_stdio_usb(${PROJECT_NAME} 1)
pico_enable_stdio_uart(${PROJECT_NAME} 1)

# Pull in our pico_stdlib which pulls in commonly used features
#pico_add_extra_outputs(imu)
#target_link_libraries(imu pico_stdlib icm20948 lps22hb hardware_i2c)
