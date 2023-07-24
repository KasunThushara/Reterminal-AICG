import tkinter as tk
import speech_recognition as sr
import pyaudio
from newsapi import NewsApiClient
import pandas as pd
import numpy as np
from gtts import gTTS
import pygame
import openai
import os
import time
import threading

newsapi = NewsApiClient(api_key='xxxxxxx') #News api key
openai.api_key = 'xxxxxxxxxx' #open api key
news = "Can you rephrase and enhance readability like news bullet remove unwanted words and summarize in one paragraph"


# Function to listen to microphone input and perform speech recognition
def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        update_label("Listening...")  # Update the label in the GUI

        audio = r.listen(source)

    try:
        update_label("Recognizing...")  # Update the label in the GUI

        text = r.recognize_google(audio)  # Use Google Speech Recognition API
        return text
        # print("You said:", text)
    except sr.UnknownValueError:
        update_label("Unable to recognize speech")  # Update the label in the GUI
        return "Error"
    except sr.RequestError as e:
        update_label(f"Error occurred: {e}")  # Update the label in the GUI
        return "Error"


def extract_country(sentence):
    countries = ["India", "US", "UK"]  # Example list of countries
    words = sentence.split()
    for word in words:
        if word in countries:
            return word
    return None


def identify_category(sentence, categories):
    words = sentence.split()
    for word in words:
        if word in categories:
            return word
    return None


def process_sentence(sentence):
    if sentence.startswith("terminal"):
        # Execute your operation here
        print("Operation executed!")
    country = extract_country(sentence)
    category = identify_category(sentence, ["technology", "sports", "politics", "tech", "general", "science", "health", "sport"])
    return country, category


def getnews(cat, cnt):
    top_headlines = newsapi.get_top_headlines(
        category=cat,
        language="en",
        country=cnt)
    article = top_headlines["articles"]
    topic = []
    desc = []

    for ar in article:
        topic.append(ar["title"])
        desc.append(ar["description"])

    df = pd.DataFrame(list(zip(topic, desc)),
                      columns=['Topic', 'Desc'])
    # print (df)

    df = df.replace(to_replace='None', value=np.nan).dropna()
    df["Combined"] = df['Topic'].astype(str) + "-" + df["Desc"]
    return df


def playtrack(dataframe):
    third_column = dataframe.iloc[:, 2]
    for i, element in enumerate(third_column[:2]):
        pygame.mixer.init()
        language = 'en'
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user",
                                                                                  "content": news + element}])
        chatgptop = completion.choices[0].message.content
        print(chatgptop)
        myobj = gTTS(text=chatgptop, lang=language, slow=False)
        filename = "welcome.mp3"
        myobj.save(filename)
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        create_news_ticker(chatgptop)
        while pygame.mixer.music.get_busy() == True:
            continue
        pygame.mixer.quit()
        os.remove(filename)


def create_news_ticker(text_content):
    # Create a Tkinter window
    window = tk.Tk()
    window.title("News Ticker")

    # Set the dimensions of the window
    window_width = 1100
    window_height = 200
    window.geometry(f"{window_width}x{window_height}")

    # Create a canvas to display the text
    canvas = tk.Canvas(window, width=window_width, height=window_height, bg="black")
    canvas.pack()

    # Set the font properties
    font_size = 36
    font = ("Helvetica", font_size, "bold")

    # Set the text color
    text_color = "white"

    # Measure the width of the text
    text_width = canvas.create_text(0, 0, text=text_content, font=font, fill=text_color, anchor="w")
    text_width = canvas.bbox(text_width)[2]  # Get the width of the text

    # Set the initial position of the text
    x_position = window_width

    # Set the animation speed
    speed = 5  # Increase this value to make the text move faster

    # Start the animation loop
    while True:
        # Update the position of the text
        x_position -= speed
        if x_position < -text_width:
            break

        # Clear the canvas
        canvas.delete("all")

        # Draw the text on the canvas
        canvas.create_text(x_position, window_height // 2, text=text_content, font=font, fill=text_color, anchor="w")

        # Update the window
        window.update()

        # Add a small delay to control the speed of the animation
        time.sleep(0.01)  # Increase this value to slow down the animation

    # Close the Tkinter window
    window.destroy()


def start_speech_recognition():
    recognize_button.config(state="disabled")  # Disable the button while speech recognition is in progress

    def background_task():
        # Initialize PyAudio
        pa = pyaudio.PyAudio()

        # Open a stream with default settings
        stream = pa.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=44100,
                         input=True,
                         frames_per_buffer=1024)

        # Continuously read and process audio
        while True:
            try:
                data = stream.read(1024)
                msg = recognize_speech()
                print(msg)
                if msg != "Error":
                    country, category = process_sentence(msg)
                    print("Country:", country)
                    print("Category:", category)
                    if country and category:
                        print("Both conditions met")
                        if country == "India":
                            cnt = "in"
                        elif country == "UK":
                            cnt = "gb"
                        elif country == "US":
                            cnt = "us"
                        else:
                            cnt = "cn"
                        data = getnews(category, cnt)
                        playtrack(data)

            except KeyboardInterrupt:
                break

        # Clean up resources
        stream.stop_stream()
        stream.close()
        pa.terminate()

        recognize_button.config(state="normal")  # Enable the button after speech recognition is finished

    # Start the background task in a new thread
    threading.Thread(target=background_task).start()


def update_label(message):
    label.config(text=message)


# Create a Tkinter window
window = tk.Tk()
window.title("Speech Recognition")
window.geometry("400x200")

# Create a label to display the messages
label = tk.Label(window, text="Click 'Recognize' to start speech recognition")
label.pack()

# Create a button to trigger the speech recognition
recognize_button = tk.Button(window, text="Recognize", command=start_speech_recognition)
recognize_button.pack()

# Start the Tkinter event loop
window.mainloop()
