from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from flask import session
import serial
import requests
import time

global send_message
send_message = 0

COM_PORT = "COM10"
BAUD_RATE = 9600

ser = serial.Serial(COM_PORT, BAUD_RATE)

def send_notification():
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_USERNAME = 'dalian.ardelean@gmail.com'
    SMTP_PASSWORD = 'twsj pdyk zvcn aaos'
    RECIPIENT_EMAIL = 'ardeleanharalambie21@gmail.com'

    message = MIMEMultipart()
    message['From'] = SMTP_USERNAME
    message['To'] = RECIPIENT_EMAIL
    message['Subject'] = 'Alertă! Inundație detectată!'

    # Construct the message body
    body = "A fost detectată o inundație la data și ora: " + time.strftime("%Y-%m-%d %H:%M:%S")
    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = message.as_string()
        server.sendmail(SMTP_USERNAME, RECIPIENT_EMAIL, text)
        server.quit()
        print("E-mail trimis cu succes!")
    except Exception as e:
        print("Eroare la trimiterea e-mailului:", e)

def check_cloud_led_state():
    try:
        response = requests.get("http://localhost:5000/get_led")
        if response.status_code == 200:
            cloud_led_state = int(response.text)
            return cloud_led_state
        else:
            print(f"Failed to get cloud LED state. Status code: {response.status_code}")
            return None
    except Exception as e:
        print("Error:", e)
        return None

def check_cloud_message():
    try:
        response = requests.get("http://localhost:5000/get_message")
        if response.status_code == 200:
            message = response.text
            return message
        else:
            print(f"Failed to get cloud message. Status code: {response.status_code}")
            return None
    except Exception as e:
        print("Error:", e)
        return None

def read_serial_and_send_data():
    global send_message, cloud_led_state
    last_message = ""  # Initialize a variable to store the last message sent  # Initialize the serial LED state
    while True:
        #print("send_message_flag = " + str(send_message))

        # Check the LED state from the cloud and the message state
        cloud_led_state = check_cloud_led_state()
        message = check_cloud_message()

        # Send the message to the Arduino only if it's different from the last one
        if message != "NULL" and message != last_message:
            ser.write(message.encode())  # Send the message
            print(message)
            last_message = message
            send_message = 1

        # Reset the message send flag after it's sent
        if send_message == 1:
            send_message = 0

        # Update the LED state based on the message
        if message == 'A':
            ser.write(b'A')  # Turn on the LED
            print("LED turned ON - message A")
        elif message == 'S':
            ser.write(b'S')  # Turn off the LED
            print("LED turned OFF - message S")
        else:
            # Update the LED state based on the cloud LED state
            if cloud_led_state == 1:
                ser.write(b'A')  # Turn on the LED
                print("LED turned ON - cloud")
            elif cloud_led_state == 0:
                ser.write(b'S')  # Turn off the LED
                print("LED turned OFF - cloud")

        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            if data.startswith("Temperatura celsius: "):
                temperature = data.split(": ")[1]
                try:
                    response = requests.post("http://localhost:5000/update_temperature", data={"temperature": temperature})
                    if response.status_code == 200:
                        print("Temperature data sent successfully to the Azure web app.")
                    else:
                        print(f"Failed to send temperature data to the Azure web app. Status code: {response.status_code}")
                except Exception as e:
                    print("Error sending temperature data:", e)
            elif data == "Inundatie detectata!":
                send_notification()
       
if __name__ == "__main__":
    print("Starting serial communication...")
    read_serial_and_send_data()