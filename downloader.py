import logging
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import pytube as pt
import requests
from PIL import Image, ImageShow, ImageTk

print("YT Downloader 0.0.3")
# https://www.youtube.com/watch?v=fyQ5EmzbnM4
# https://www.youtube.com/watch?v=F7mKD2Un65I
# https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Exception handing
logging.basicConfig(filename='log.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)
# handler = logging.StreamHandler(stream=sys.stdout)
# logger.addHandler(handler)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception


# App
TITLE_FONT = ("Verdana", 20, "bold")
DESC_FONT = ("Helvetica", 15, "")


class CustomEntry():
    REGULAR_FOREGROUND = "#000000"
    PLACEHOLDER_FOREGROUND = "#aaaaaa"

    def __init__(self, master: tk.Frame, placeholder: str = "") -> None:
        self.master = master
        self.placeholder = placeholder

        self.entry = ttk.Entry(
            master,
            foreground=self.PLACEHOLDER_FOREGROUND,
            width=40,
        )

        self.text_variable = tk.StringVar(self.entry, value=placeholder)
        self.entry.configure(textvariable=self.text_variable)

        self.entry.bind("<FocusIn>", self.handle_focus_in)
        self.entry.bind("<FocusOut>", self.handle_focus_out)


    def handle_focus_in(self, event=None):
        if str(self.entry["foreground"]) == self.PLACEHOLDER_FOREGROUND:
            self.text_variable.set("")
            self.entry.configure(foreground=self.REGULAR_FOREGROUND)

    def handle_focus_out(self, event=None):
        if self.entry.get() == "":
            self.entry.configure(foreground=self.PLACEHOLDER_FOREGROUND)
            self.text_variable.set(self.placeholder)

    def grid(self, *args, **kwargs):
        self.entry.grid(*args, **kwargs)

    def get(self):
        if str(self.entry["foreground"]) == self.PLACEHOLDER_FOREGROUND:
            return ""
        else:
            return self.text_variable.get()
    
    def set(self, text: str = ""):
        self.entry.insert(0, text)


class App(tk.Tk):
    # Columns for the treeview, and how to retrieve that information from a Stream() object
    COLUMN_DISPLAY = {
        "filesize": "Filesize (MB)",
        "type": "File type",
        "audio": "Audio",
        "video": "Video",
        "abr": "Audio Bitrate",
        "fps": "Frames/Second",
        "res": "Resolution",
    }

    COLUMN_VALUES = {
        "filesize": lambda x: x.filesize_mb,
        "type": lambda x: x.__dict__['mime_type'],
        "audio": lambda x: x.includes_audio_track,
        "video": lambda x: x.includes_video_track,
        "abr": lambda x: x.__dict__['abr'],
        "fps": lambda x: x.__dict__.get('fps', "N/A"),
        "res": lambda x: x.__dict__.get('resolution', "N/A"),
    }

    TYPE_FILTER_DROPDOWN_VALUES = {
        # Display String: [Audio-only filter, Video-only filter]
        "Any": [None, None, None],
        "Video only": [None, True, None],
        "Audio only": [True, None, None],
        "Audio & Video": [None, None, True],
    }

    # Padding values
    THUMBNAIL_SIZE_X = 130
    THUMBNAIL_PADX = 30
    TEXT_PADX = 20

    TREEVIEW_COLUMN_MINWIDTH = 90

    # Minimum with must be above thumbnail + text width, as well as above treeview width
    MINSIZE_X = max(
        100 + THUMBNAIL_SIZE_X + 2 * (THUMBNAIL_PADX + TEXT_PADX),
        len(COLUMN_VALUES) * TREEVIEW_COLUMN_MINWIDTH,
    )

    def __init__(self) -> None:
        super().__init__()

        # Make window resizable
        self.minsize(self.MINSIZE_X, 400)
        self.resizable(True, True)

        top = self.winfo_toplevel()
        top.grid_columnconfigure(0, weight=1)
        top.grid_rowconfigure(0, weight=1)

        self.grid_columnconfigure(0, weight=1) # Entire window
        self.grid_rowconfigure(0, weight=0) # Top
        self.grid_rowconfigure(4, weight=1) # Stream list

        # Top bar
        self.top_frame = tk.Frame(self)
        self.url_entry = CustomEntry(self.top_frame, "URL")
        self.go_button = tk.Button(self.top_frame, text="Go", command=self.handle_go_button)

        self.top_frame.grid(row=0, column=0, sticky="EW")
        self.url_entry.grid(row=0, column=0, sticky="EW")
        self.go_button.grid(row=0, column=1, sticky="E")

        self.top_frame.grid_columnconfigure(0, weight=1)


        # Video info
        self.video_frame = tk.Frame(self)
        self.thumbnail_lb = ttk.Label(self.video_frame)
        self.title_lb = tk.Label(self.video_frame, text="Video Title", font=TITLE_FONT)
        self.desc_tb = tk.Label(self.video_frame, text="Video Description", font=DESC_FONT)
        self.set_image("placeholder.png")

        self.video_frame.grid(row=1, column=0, pady=0)
        self.thumbnail_lb.grid(row=0, column=0, rowspan=2, padx=self.THUMBNAIL_PADX)
        self.title_lb.grid(row=0, column=1, padx=self.TEXT_PADX)
        self.desc_tb.grid(row=1, column=1, padx=self.TEXT_PADX)

        self.video_frame.grid_columnconfigure(1, weight=1)
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_rowconfigure(1, weight=1)


        # Filters
        self.filters_frame = tk.Frame(self)
        self.type_lb = tk.Label(self.filters_frame, text="Media Type")
        self.type_drop = ttk.Combobox(self.filters_frame,
                                      values=list(self.TYPE_FILTER_DROPDOWN_VALUES.keys()),
                                      state="readonly")
        self.type_drop.bind("<<ComboboxSelected>>", self.show_streams)
        self.type_drop.set("Any")

        self.filters_frame.grid(row=2, column=0)
        self.type_lb.grid(row=0, column=0)
        self.type_drop.grid(row=1, column=0)


        # Streams list
        self.treeview_frame = tk.Frame(self)
        self.treeview = ttk.Treeview(self.treeview_frame, columns=self.COLUMN_DISPLAY.keys(), selectmode="browse", show="headings")
        for i, (column_key, column_disp) in enumerate(self.COLUMN_DISPLAY.items()):
            self.treeview.heading(column=i, text=column_disp)
            self.treeview.column(i, minwidth=self.TREEVIEW_COLUMN_MINWIDTH, width=self.TREEVIEW_COLUMN_MINWIDTH, stretch=True)

        self.treeview_frame.grid(row=4, column=0, sticky="NESW")
        self.treeview.grid(row=0, column=0, sticky="NESW")

        # Resizable
        self.treeview_frame.grid_propagate(False)
        self.treeview.grid_propagate(False)
        self.treeview_frame.grid_rowconfigure(0, weight=1)
        self.treeview_frame.grid_columnconfigure(0, weight=1)

        self.streams = []


        # Download button
        self.buttons_frame = tk.Frame(self)
        self.download_button = tk.Button(self.buttons_frame, text="Start Download", command=self.handle_download_buttton)
        self.auto_download_button = tk.Button(self.buttons_frame, text="Auto Download Best Quality (Recommended but takes more time)", command=self.handle_auto_download_button)

        self.buttons_frame.grid(row=5, column=0)
        self.download_button.grid(row=0, column=0)
        self.auto_download_button.grid(row=0, column=1)

        # Resize
        self.previous_width = 0
        self.previous_height = 0
        self.bind("<Configure>", self.resize)


    def resize(self, event = None):
        if event:
            if event.widget == self and (self.previous_height != event.height or self.previous_width != event.width):
                self.previous_width, self.previous_height = event.width, event.height
                available_width_for_text = event.width - self.THUMBNAIL_SIZE_X - 2 * (self.THUMBNAIL_PADX + self.TEXT_PADX)
                self.title_lb.configure(wraplength=available_width_for_text)
                self.desc_tb.configure(wraplength=available_width_for_text)


    def open_current_image(self, event=None):
        thumb_maxres = requests.get(f"https://img.youtube.com/vi/{self.yt.video_id}/maxresdefault.jpg", stream=True).raw
        with Image.open(thumb_maxres) as thumb:
            ImageShow.show(thumb, title="Video Thumbnail")


    def set_image(self, contents_or_url: str):
        with Image.open(contents_or_url) as thumb_img:
            thumb_img.thumbnail((128, 128))
            thumb_tkimg = ImageTk.PhotoImage(thumb_img)
            self.thumbnail_lb.configure(image=thumb_tkimg)
            self.thumbnail_lb.bind("<Button-1>", self.open_current_image)
            self.thumbnail_lb.image = thumb_tkimg


    def show_streams(self, event=None) -> None:
        # Clear previously loaded streams
        self.treeview.delete(*self.treeview.get_children())

        # Add current streams
        audio_only, video_only, progressive_only = self.TYPE_FILTER_DROPDOWN_VALUES[self.type_drop.get()]

        if not self.streams:
            # Streams have not been loaded yet
            return

        filtered_streams = self.streams.filter(only_audio=audio_only, only_video=video_only, progressive=progressive_only)

        for stream in filtered_streams:
            self.treeview.insert("", "end", iid=stream.itag, values=[func(stream) for func in self.COLUMN_VALUES.values()])

        # Add an option to download the maximum quality
        #self.treeview.insert("", "end", iid="-1", values=["N/A", "N/A", "True", "True", "N/A", "N/A", "N/A"])


    def handle_go_button(self, event=None) -> None:
        try:
            self.yt = pt.YouTube(self.url_entry.get())
        except pt.exceptions.RegexMatchError:
            self.go_button.configure(state="normal")
            messagebox.showerror("Invalid URL", "Please check that the URL is correct")
            return

        # Thumbnail
        try:
            # self.yt.thumbnail_url not used due to random cropping and low quality
            # https://stackoverflow.com/questions/2068344/how-do-i-get-a-youtube-video-thumbnail-from-the-youtube-api
            thumb_maxres = requests.get(f"https://img.youtube.com/vi/{self.yt.video_id}/maxresdefault.jpg", stream=True).raw
            self.current_img = thumb_maxres
            self.set_image(thumb_maxres)
        except requests.ConnectionError:
            # If image fails, use the default image instead
            self.set_image("placeholder.png")

        # Streams
        self.streams = self.yt.streams.asc() # This takes the longest time
        self.show_streams()

        # Used to make the description work
        # https://github.com/pytube/pytube/issues/1626
        self.streams.first()

        # Title & Description
        self.title_lb.configure(text=self.yt.title)
        self.desc_tb.configure(text=self.yt.description if self.yt.description else "No description")

        self.resize()


    def handle_auto_download_button(self, event=None) -> None:
        # Special value to download the highest resolution and bitrate, and merge them

        self.loading_window = tk.Toplevel()
        self.loading_window.wm_title("Progress")

        # Must have video
        video_streams = filter(self.COLUMN_VALUES["video"], self.streams)
        # Sort primarily by resolution, then by FPS
        video_stream: pt.Stream = max(*video_streams, key=lambda x: (int(x.__dict__.get('resolution', "0").replace("p", "")), int(self.COLUMN_VALUES["fps"](x))))

        # Must be audio only
        audio_streams = self.streams.filter(only_audio=True)
        # Sort by bitrate
        audio_stream: pt.Stream = max(*audio_streams, key=lambda x: int(x.__dict__['abr'].replace("kbps", "")))

        # Progress bars
        self.video_var = tk.DoubleVar(self.loading_window, name="video")
        self.audio_var = tk.DoubleVar(self.loading_window, name="audio")

        # video_bar = ttk.Progressbar(self.loading_window,
        #                             variable=self.video_var,
        #                             maximum=video_stream.filesize,
        #                             mode='determinate')
        # audio_bar = ttk.Progressbar(self.loading_window,
        #                             variable=self.audio_var,
        #                             maximum=video_stream.filesize,
        #                             mode='determinate')
        # muxing_bar = ttk.Progressbar(self.loading_window,
        #                              maximum=video_stream.filesize,
        #                              mode='indeterminate')

        video_lb = tk.Label(self.loading_window, text="Video Download")
        audio_lb = tk.Label(self.loading_window, text="Audio Download")

        video_progress_lb = tk.Label(self.loading_window)
        audio_progress_lb = tk.Label(self.loading_window)

        video_lb.grid(row=0, column=0)
        audio_lb.grid(row=1, column=0)

        video_progress_lb.grid(row=0, column=1)
        audio_progress_lb.grid(row=1, column=1)
        # muxing_bar.grid(row=2, column=0)

        # Starting downloads
        filename = video_stream.default_filename.split(".")[0]
        self.start_download(stream=video_stream, label=video_progress_lb, filename="max_video")
        self.start_download(stream=audio_stream, label=audio_progress_lb, filename="max_audio")
        # join threads
        self.needs_merging = 0
        self.after(100, lambda: self.merge_auto_files(filename))


    def merge_auto_files(self, filename: str):
        if self.needs_merging == 2:
            # Can merge now
            self.needs_merging = 0
            cmd = f"ffmpeg -y -i max_audio -r 30 -i max_video -filter:a aresample=async=1 -c:a flac -c:v copy '{filename}.mkv'"
            subprocess.call(cmd, shell=True)
            os.remove("max_video")
            os.remove("max_audio")

            self.loading_window.destroy()
            return
        self.after(100, lambda: self.merge_auto_files(filename))


    def handle_download_buttton(self, event=None) -> None:
        selection = self.treeview.selection()

        if not selection:
            # No items selected
            messagebox.showerror("No item selected", "Please select an item from the list to start download")
            return

        self.loading_window = tk.Toplevel()

        # if selection[0] == "-1":
        #     self.handle_auto_download_button()
        #     return

        # Regular downloads
        required_stream: pt.Stream = list(filter(lambda x: str(x.itag) == selection[0], self.streams))[0]
        required_stream.download()
        messagebox.showinfo("", "Download completed")
        self.loading_window.destroy()


    def start_download(self, stream: pt.Stream, label: tk.Label, filename: str = None):
        max_size = stream.filesize
        t = threading.Thread(target=stream.download, kwargs={"filename": filename})
        t.start()

        label.after(100, lambda: self.update_progress_bar(filename=filename, max_size=max_size, label=label))


    def update_progress_bar(self, filename: str, max_size: int, label: tk.Label):
        size = os.path.getsize(filename) if os.path.exists(filename) else 0
        label.configure(text=f"{size} / {max_size} [{round(size/max_size*100, 2)}%]")
        if size == max_size:
            self.needs_merging += 1
            return
        label.after(100, lambda: self.update_progress_bar(filename=filename, max_size=max_size, label=label))


print(__name__ == "__main__")
if __name__ == "__main__":
    app = App()
    app.mainloop()
