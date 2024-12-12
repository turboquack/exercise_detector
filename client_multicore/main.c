#include <stdio.h>
#include "pico/stdlib.h"
#include "lwip/udp.h"
#include "lwip/ip_addr.h"
#include "pico/cyw43_arch.h"
#include "lwip/pbuf.h"
#include "pico/multicore.h"
//#include "lwip/tcp.h"

#include "icm20948/icm20948.h"
#include "lps22hb/lps22hb.h"

#define REMOTE_IP_ADDR1 192
#define REMOTE_IP_ADDR2 168
#define REMOTE_IP_ADDR3 1
#define REMOTE_IP_ADDR4 72
#define REMOTE_SERVER_IP "192.168.1.72"  // Replace with your remote server IP
#define REMOTE_SERVER_PORT 12345          // Replace with the desired port number
#define DEBUG_printf printf
#define SSID "WIFI SSID"
#define WIFI_PWD "WIFI PWD"

#define FLAG_VALUE 123
IMU_EN_SENSOR_TYPE enMotionSensorType;
IMU_ST_ANGLES_DATA stAngles;
IMU_ST_SENSOR_DATA stGyroRawData;
IMU_ST_SENSOR_DATA stAccelRawData;
IMU_ST_SENSOR_DATA stMagnRawData;
float PRESS_DATA=0;
float TEMP_DATA=0;
uint8_t u8Buf[3];

char output[128];  // Buffer size can be adjusted based on actual data size
size_t buffer_size = sizeof(output);
bool ready_to_send=false;

static void udp_data_send(char *data_to_send) {
    struct udp_pcb *pcb;
    struct pbuf *p;
    ip_addr_t remote_ip;
    err_t err;

    // Create a new UDP control block
    pcb = udp_new();
    if (pcb == NULL) {
        printf("Error: Could not create a new UDP control block.\n");
        return;
    }

    // Set the remote IP and port
    IP4_ADDR(&remote_ip, REMOTE_IP_ADDR1, REMOTE_IP_ADDR2, REMOTE_IP_ADDR3, REMOTE_IP_ADDR4);
    uint16_t remote_port = REMOTE_SERVER_PORT;

    // Allocate a new pbuf for message
    p = pbuf_alloc(PBUF_TRANSPORT, strlen(data_to_send) + 1, PBUF_RAM);
    if (p == NULL) {
        printf("Error: Could not allocate pbuf.\n");
        udp_remove(pcb);
        return;
    }

    // Copy the message into the pbuf
    pbuf_take(p, data_to_send, strlen(data_to_send) + 1);

    // Send the message
    err = udp_sendto(pcb, p, &remote_ip, remote_port);
    if (err != ERR_OK) {
        printf("Error: Could not send the message. Error code: %d\n", err);
    } else {
        printf("Sent data to %s:%d\n", REMOTE_SERVER_IP, REMOTE_SERVER_PORT);
    }

    // Clean up
    pbuf_free(p);
    udp_remove(pcb);
}

void format_sensor_data() {
    //printf("Format data now\n");
    snprintf(output, buffer_size,
             "R:%.2f;P:%.2f;Y:%.2f;"
             "P=%6.2fhPa;T=%6.2f°C;"
             "Acce:X:%d;Y:%d;Z:%d;"
             "Gyro:X:%d;Y:%d;Z:%d;"
             "Magn:X:%d;Y:%d;Z:%d;",
             stAngles.fRoll, stAngles.fPitch, stAngles.fYaw, PRESS_DATA, TEMP_DATA,
             stAccelRawData.s16X, stAccelRawData.s16Y, stAccelRawData.s16Z, stGyroRawData.s16X, stGyroRawData.s16Y, stGyroRawData.s16Z,
             stMagnRawData.s16X, stMagnRawData.s16Y, stMagnRawData.s16Z);
}

void read_sensor_data(){
        LPS22HB_START_ONESHOT();
        if((I2C_readByte(LPS_STATUS)&0x01)==0x01)   //a new pressure data is generated
        {
            u8Buf[0]=I2C_readByte(LPS_PRESS_OUT_XL);
            u8Buf[1]=I2C_readByte(LPS_PRESS_OUT_L);
            u8Buf[2]=I2C_readByte(LPS_PRESS_OUT_H);
            PRESS_DATA=(float)((u8Buf[2]<<16)+(u8Buf[1]<<8)+u8Buf[0])/4096.0f;
        }
        if((I2C_readByte(LPS_STATUS)&0x02)==0x02)   // a new pressure data is generated
        {
            u8Buf[0]=I2C_readByte(LPS_TEMP_OUT_L);
            u8Buf[1]=I2C_readByte(LPS_TEMP_OUT_H);
            TEMP_DATA=(float)((u8Buf[1]<<8)+u8Buf[0])/100.0f;
        }
		imuDataGet( &stAngles, &stGyroRawData, &stAccelRawData, &stMagnRawData);
        /*
        printf("\r\n /-------------------------------------------------------------/ \r\n");
        printf("\r\nCORE1\r\n");
		printf("\r\n Roll: %.2f     Pitch: %.2f     Yaw: %.2f \r\n",stAngles.fRoll, stAngles.fPitch, stAngles.fYaw);
	   	printf("\r\n Pressure = %6.2f hPa , Temperature = %6.2f °C\r\n", PRESS_DATA, TEMP_DATA);
		printf("\r\n Acceleration: X: %d     Y: %d     Z: %d \r\n",stAccelRawData.s16X, stAccelRawData.s16Y, stAccelRawData.s16Z);
		printf("\r\n Gyroscope: X: %d     Y: %d     Z: %d \r\n",stGyroRawData.s16X, stGyroRawData.s16Y, stGyroRawData.s16Z);
		printf("\r\n Magnetic: X: %d     Y: %d     Z: %d \r\n",stMagnRawData.s16X, stMagnRawData.s16Y, stMagnRawData.s16Z);
        */
}

void core1_entry() {
    while (1) {
        uint64_t start = time_us_64();
        //uint64_t sleep_time = 30000; //30ms
        read_sensor_data(); // Call the sensor data reading function
        format_sensor_data();
        ready_to_send = true;
        uint64_t end = time_us_64();
        // Calculate the elapsed time in microseconds
        uint64_t duration = end - start;
        // Output the elapsed time
        printf("\n\nTime taken to read IMU : %llu microseconds\n\n", duration);
        //sleep_time=sleep_time-duration;
        //printf("\n\nSleeping for :%"PRIu64" microseconds \n\n",sleep_time);
        //sleep_ms(sleep_time/1000);
    }
}

int main() {
    stdio_init_all();
    if (cyw43_arch_init()) {
        DEBUG_printf("failed to initialise\n");
        return 1;
    }
    cyw43_arch_enable_sta_mode();

    
    printf("Connecting to WiFi...\n");
    printf("Connecting to WiFi...\n");
    printf("Connecting to WiFi...\n");
    printf("Connecting to WiFi...\n");
    printf("Connecting to WiFi...\n");
    if (cyw43_arch_wifi_connect_timeout_ms(SSID, WIFI_PWD, CYW43_AUTH_WPA2_AES_PSK, 30000)) {
        printf("failed to connect.\n");
        return 1;
    } else {
        printf("Connected.\n");
    }
    printf("Connected.\n");
    
    
	imuInit(&enMotionSensorType);
	if(IMU_EN_SENSOR_TYPE_ICM20948 == enMotionSensorType)
	{
		printf("Motion sersor is ICM-20948\n" );
	}
	else
	{
		printf("Motion sersor NULL\n");
	}
	if (!LPS22HB_INIT()){
		printf("LPS22HB Init Error\n");
		return 0;
	}
    multicore_launch_core1(core1_entry); // Start Core 1 with core1_entry function

    while(1){
        
        if (ready_to_send) {
            uint64_t start = time_us_64();
            udp_data_send(output);
            uint64_t end = time_us_64();
            // Calculate the elapsed time in microseconds
            uint64_t duration = end - start;
            // Output the elapsed time
            printf("Time taken to send : %llu microseconds\n", duration);
            ready_to_send = false;
        }
        sleep_ms(2);
        
    }

    return 0;
}
