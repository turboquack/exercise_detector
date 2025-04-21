import os
import time
import socket
import threading
import re

import flet as ft
from datetime import datetime
from flet import (
    ElevatedButton, FilePicker, FilePickerResultEvent, Page, Row, Text, Icons, AlertDialog, TextButton,
    Column, TextField, ListView, ListTile, colors, ProgressBar
)


# Constants
UDP_PORT = 12345
RECORDING_CYCLES = 110
BREAK_CYCLES = 20
BUFFER_FLUSH_DELAY = 0.2
UPDATE_INTERVAL = 5

def main(page: ft.Page):
    """Main function to set up the UI and UDP server logic."""

    selected_file_name = None
    udp_server_running = False
    udp_thread = None

    # UI Components
    recording_progress = ProgressBar(value=0, width=400)
    break_progress = ProgressBar(value=0, width=400, bgcolor=ft.Colors.GREY)
    #countdown_text = Text(value="", size=20, weight="bold", color=colors.RED)


    #charts
    labels = ["X", "Y", "Z"]
    chart_colors = [ft.Colors.BLUE, ft.Colors.RED, ft.Colors.GREEN]
    max_points = 25
    x_values = list(range(max_points))
    def create_chart(title, min_y, max_y):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=15, weight=ft.FontWeight.BOLD),
                ft.LineChart(
                    data_series=[
                        ft.LineChartData(
                            data_points=[ft.LineChartDataPoint(x, 0) for x in x_values],
                            color=chart_colors[i], stroke_width=4
                        ) for i in range(3)
                    ],
                    min_y=min_y,
                    max_y=max_y,
                    min_x=0,
                    max_x=max_points - 1,
                    animate=True,
                    expand=True,
                )
            ]),
            expand=True,
            padding=10
        )
    acc_chart = create_chart("Acceleration", -20000, 20000)
    gyro_chart = create_chart("Gyroscope", -20000, 20000)
    magn_chart = create_chart("Magnetometer", -500, 500)


    def parse_data(data):
        pattern = re.compile(
            r"Acce:X:(-?\d+);Y:(-?\d+);Z:(-?\d+);"
            r"Gyro:X:(-?\d+);Y:(-?\d+);Z:(-?\d+);"
            r"Magn:X:(-?\d+);Y:(-?\d+);Z:(-?\d+)"
        )

        match = pattern.search(data)

        if match:
            return list(map(int, match.groups()))

        # Debugging Logs
        print(f"⚠️ Data did not match expected format: {data}")
        return None


    def close_alert(e):
        """Close the alert dialog."""
        alert.open = False
        page.update()

    def close_filename_alert(e):
        """Close the alert dialog."""
        filename_alert.open = False
        page.update()


    def clear_udp_buffer(sock):
        """Flush any remaining UDP packets to prevent data overlap."""
        sock.setblocking(False)
        while True:
            try:
                sock.recvfrom(1024)
            except BlockingIOError:
                break
        sock.setblocking(True)

    def udp_server():
        """UDP server that listens for packets, records data, and manages break periods."""
        nonlocal udp_server_running
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", UDP_PORT))
        first_run = True  # Flag to indicate the first run

        while udp_server_running:
            if first_run:
                # Initial Break Phase
                for i in range(BREAK_CYCLES):
                    if not udp_server_running:
                        break
                    break_progress.value = (i + 1) / BREAK_CYCLES
                    page.update()
                    time.sleep(0.1)
                break_progress.value = 0
                page.update()
                first_run = False  # Mark that the first break is done

            samples = []
            recording_progress.value = 0
            page.update()
            clear_udp_buffer(sock)  # Flush old data
            start_time = datetime.now()
            #print(f"Recording phase started at: {start_time}")

            # Recording Phase
            for i in range(RECORDING_CYCLES):
                if not udp_server_running:
                    break
                try:
                    sock.settimeout(2)
                    data, addr = sock.recvfrom(1024)
                    decoded_data = data.decode("utf-8", errors="ignore")
                    samples.append(decoded_data)
                    #print(f"📩 Received UDP Data: {decoded_data}")  # Log raw UDP data
                    parsed=parse_data(decoded_data)
                    if parsed is None:
                        print("Parsing failed! Check incoming format.")  # Log parsing errors
                    update_chart(parsed)


                    recording_progress.value = (i + 1) / RECORDING_CYCLES
                    page.update()
                except socket.timeout:
                    print(f"Timeout at index {i}, no data received.")
                    continue

            end_time = datetime.now()
            print(f"Recording phase ended at: {end_time} (Duration: {end_time - start_time})")
            print(f"Number of samples",len(samples))
            # Save data if recording is complete
            if len(samples) == RECORDING_CYCLES and selected_file_name:
                with open(os.path.join(directory_path.value, selected_file_name), "a") as f:
                    f.write("\n".join(samples) + "\n")

            time.sleep(BUFFER_FLUSH_DELAY)
            clear_udp_buffer(sock)
            time.sleep(BUFFER_FLUSH_DELAY)

            # Ensure progress bar shows completion before reset
            recording_progress.value = 1.0
            page.update()
            time.sleep(0.5)
            recording_progress.value = 0
            page.update()

            # Break Phase
            start_break_time = datetime.now()
            #print(f"Break phase started at: {start_break_time}")
            for i in range(BREAK_CYCLES):
                if not udp_server_running:
                    break
                break_progress.value = (i + 1) / BREAK_CYCLES
                page.update()
                time.sleep(0.1)
            break_progress.value = 0
            page.update()
            end_break_time = datetime.now()
            print(f"Break phase ended at: {end_break_time} (Duration: {end_break_time - start_break_time})")

        sock.close()
        recording_progress.value = 0
        break_progress.value = 0
        page.update()

    def toggle_udp_server(e):
        """Start or stop the UDP server."""
        nonlocal udp_server_running, udp_thread
        if not udp_server_running:
            if not selected_file_name:
                alert.open = True
                page.update()
                return

            page.update()
            udp_server_running = True
            udp_thread = threading.Thread(target=udp_server, daemon=True)
            udp_thread.start()
            udp_server_button.text = "Stop UDP Server"
        else:
            udp_server_running = False
            if udp_thread:
                udp_thread.join()  # Ensure proper thread termination
            udp_thread = None
            udp_server_button.text = "Start UDP Server"
        page.update()

    def get_directory_result(e: FilePickerResultEvent):
        """Handle directory selection for saving data."""
        directory_path.value = e.path if e.path else "Cancelled!"
        directory_path.update()
        update_csv_list()
        page.update()

    def update_csv_list():
        """Update the list of CSV files in the selected directory."""
        if os.path.isdir(directory_path.value):
            csv_files.controls.clear()
            for file in os.listdir(directory_path.value):
                if file.endswith(".csv"):
                    csv_files.controls.append(
                        ListTile(
                            title=Text(file),
                            on_click=lambda e, selected_file=file: select_file(selected_file),
                            bgcolor=ft.Colors.GREEN if file == selected_file_name else None,
                        )
                    )
            csv_files.update()

    def add_new_csv(e):
        """Create a new CSV file in the selected directory."""
        if not directory_path.value or not os.path.isdir(directory_path.value):
            filename_alert.open = True
            page.update()
            return
        if os.path.isdir(directory_path.value):
            new_file_name = new_csv_name.value.strip()
            if new_file_name and not new_file_name.endswith(".csv"):
                new_file_name += ".csv"
            new_file_path = os.path.join(directory_path.value, new_file_name)
            try:
                with open(new_file_path, "w") as new_file:
                    pass
                    #new_file.write("Header1,Header2,Header3\n")
                update_csv_list()
                new_csv_name.value = ""
                page.update()
            except Exception as err:
                page.dialog = AlertDialog(title=Text(f"Error: {err}"))
                page.dialog.open = True
                page.update()


    def select_file(file_name):
        """Select a file for recording data."""
        nonlocal selected_file_name
        selected_file_name = file_name
        selected_file_label.value = f"Selected File: {file_name}"
        update_csv_list()
        page.update()





    def update_chart(new_data):
        if new_data is None or len(new_data) != 9:  # Ensure valid data before updating
            print("Warning: Received invalid sensor data. Skipping update.")
            return
        for i, chart_container in enumerate([acc_chart, gyro_chart, magn_chart]):
            chart = chart_container.content.controls[1]  # Correctly access LineChart inside the container
            for j, series in enumerate(chart.data_series):
                series.data_points.pop(0)
                series.data_points.append(ft.LineChartDataPoint(max_points - 1, new_data[i * 3 + j]))
                for k in range(max_points):
                    series.data_points[k] = ft.LineChartDataPoint(k, series.data_points[k].y)
        page.update()






    # UI Elements
    alert = AlertDialog(
        modal=True,
        title=Text("Alert"),
        content=Text("Select a file first!"),
        actions=[TextButton("OK", on_click=close_alert)]
    )

    filename_alert = AlertDialog(
        modal=True,
        title=Text("Alert"),
        content=Text("Insert a filename first!"),
        actions=[TextButton("OK", on_click=close_filename_alert)]
    )

    page.overlay.append(alert)
    page.overlay.append(filename_alert)

    get_directory_dialog = FilePicker(on_result=get_directory_result)
    directory_path = Text()
    page.overlay.extend([get_directory_dialog])

    page.title = "Data Capture"
    csv_files = ListView(expand=True, spacing=10)
    new_csv_name = TextField(label="New CSV File Name", hint_text="Enter file name", expand=True)
    selected_file_label = Text(value="Selected File: None", size=16, weight="bold")
    udp_server_button = ElevatedButton("Start UDP Server", on_click=toggle_udp_server)

    # Layout
    page.add(
        Column(
            controls=[
                Row([
                    ElevatedButton("Select Directory", icon=Icons.FOLDER_OPEN,
                                   on_click=lambda _: get_directory_dialog.get_directory_path()),
                    directory_path,
                ]),
                Row([new_csv_name, ElevatedButton("Add CSV File", on_click=add_new_csv)]),
                Text("CSV Files in Directory:"),
                csv_files,
                udp_server_button,
                Text("Recording Progress:"),
                recording_progress,
                Text("Break Time Progress:"),
                break_progress,
                # Place charts at the bottom, next to each other
                ft.Row([acc_chart, gyro_chart, magn_chart], alignment=ft.MainAxisAlignment.CENTER),
            ]
        )
    )


ft.app(target=main)
