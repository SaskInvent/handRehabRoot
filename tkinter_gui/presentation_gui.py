import datetime
import queue
import logging
import signal
import serial
import time
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk, VERTICAL, HORIZONTAL, N, S, E, W


logger = logging.getLogger(__name__)

# Read serial in from port "ACM0" or "ACM1"
# (usb ports, the device id is may be different each time)
# TODO: Generalize this statement to allow for running the GUI when hooked up to a windows PC.
# ser = serial.Serial('/dev/ttyACM0', 9600)
ser = serial.Serial('COM5', 9600)


class SerialConsoleOutput(threading.Thread):
    """Accept Serial input and write to the serial console.

    """
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        logger.debug('Started reading Serial from Arduino')
        while not self._stop_event.is_set():
            if ser.in_waiting:
                logger.log(logging.INFO, ser.readline())

    def stop(self):
        self._stop_event.set()


class QueueHandler(logging.Handler):
    """Class to send logging records to a queue

    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """
    # Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    # (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
    # See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class ConsoleUi:
    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, frame):
        self.frame = frame
        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText(frame, state='disabled', height=12)
        self.scrolled_text.grid(row=0, column=0, sticky=(N, S, W, E))
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        # Add something to to formatter if you want a specific output prepended to each line
        formatter = logging.Formatter('')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)
        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg.lstrip().rstrip() + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)


class FormUi:

    def __init__(self, frame):
        self.frame = frame

        inflateButton = tk.Button(frame, text="Inflate Fingers")
        inflateButton.bind("<Button-1>", init_inflate_mode)
        inflateButton.grid(row=0, column=0, sticky=W, padx=4)

        RESET_button = tk.Button(frame, text="RESET")
        RESET_button.bind("<Button-1>", RESET)
        RESET_button.grid(row=1, column=0, sticky=W, padx=4)

class ThirdUi:

    def __init__(self, frame):
        self.frame = frame
        ttk.Label(self.frame, text='Instructions:').grid(column=0, row=1, sticky=W)
        ttk.Label(self.frame, text='1. Set the potentiometer so trueFlex reads between 400 and 600.').grid(column=0, row=2, sticky=W)
        ttk.Label(self.frame, text='2. Use the potentiometer to control the inflation and deflation of the finger actuators.').grid(column=0, row=3, sticky=W)
        ttk.Label(self.frame, text='3. If the system goes into Emergency Shutoff mode (You can no longer control the actuator and the output changes) then hit the RESET button and return to step 1.\n    You may have to hit the RESET button multiple times.').grid(column=0, row=4, sticky=W)


def set_idle_mode(event):
    ser.write(b'0')


def init_inflate_mode(event):
    ser.write(b'2')


def RESET(event):
    # char 'R' for RESET
    ser.write(b'R')


class App:

    def __init__(self, root):
        self.root = root
        root.title('Logging Handler')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        # Create the panes and frames
        vertical_pane = ttk.PanedWindow(self.root, orient=VERTICAL)
        vertical_pane.grid(row=0, column=0, sticky="nsew")
        horizontal_pane = ttk.PanedWindow(vertical_pane, orient=HORIZONTAL)
        vertical_pane.add(horizontal_pane)
        form_frame = ttk.Labelframe(horizontal_pane, text="MyForm")
        form_frame.columnconfigure(1, weight=1)
        horizontal_pane.add(form_frame, weight=1)
        console_frame = ttk.Labelframe(horizontal_pane, text="Console")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        horizontal_pane.add(console_frame, weight=1)
        third_frame = ttk.Labelframe(vertical_pane, text="Third Frame")
        vertical_pane.add(third_frame, weight=1)
        # Initialize all frames
        self.form = FormUi(form_frame)
        self.console = ConsoleUi(console_frame)
        self.third = ThirdUi(third_frame)
        # self.clock = Clock()
        # self.clock.start()
        ########### NEW CODE #################
        self.serial_arduino = SerialConsoleOutput()
        self.serial_arduino.start()
        ######################################
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        signal.signal(signal.SIGINT, self.quit)

    def quit(self, *args):
        # self.clock.stop()
        ########### NEW CODE #################
        self.serial_arduino.stop()
        ######################################
        self.root.destroy()


def main():
    logging.basicConfig(level=logging.DEBUG)
    root = tk.Tk()
    app = App(root)
    app.root.mainloop()


if __name__ == '__main__':
    main()
