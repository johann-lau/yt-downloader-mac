# YT-Downloader
YT-Downloader is a GUI program for Mac to download YouTube videos.

![Screenshot of the app](/screenshots/app_screenshot.png)

## Version
Version: 0.0.3

Updated: 22 September 2023, 06:00 UTC

## Installation
1. Obtain the latest copy of the project: **If you are viewing this on GitHub**, Press the green Code button and select "Download ZIP", then unzip the downloaded file. **If you are viewing this from your local storage**, you likely already have the project downloaded; you can still get an updated version by following the steps above.

![Screenshot of how the ZIP file can be downloaded](/screenshots/download.png)

2. Set the permission: Due to the nature of permissions, you need to enable the execution permission for the program before running. Right click on the `yt-downloader-mac` folder and select **New Terminal at Folder**.

![Screenshot of how the terminal folder can be opened](/screenshots/permission.png)

![Screenshot of what the terminal looks like](/screenshots/chmod1.png)

3. Type `chmod +x downloader.command` and press enter. You can then close the terminal window.
![Screenshot of what happens after typing chmod and press enter](/screenshots/chmod2.png)

4. Congratulations! You have installed the project and can run it. Remember - every time you download the ZIP again, you need to re-enable permissions by following steps 2-3 above.

## Running
To run the program, just go into the `yt-downloader-mac` folder, and double click `downloader.command`. The program uses pytube and automatically checks for updates during startup. Internet connection is required and startup may take a few seconds.

1. Paste the URL of the video into the textbox, then press the Go button. The URL can be of any format, but must contain `v=xxxxxxxxxxx` (e.g. `v=dQw4w9WgXcQ`). Other parts of the URL does not affect the output.

2. A list of items should appear. (Resize the window to enlarge the list) There are video-only items (those with moving pictures but not audio), audio-only items, and progressive items (those with both video and audio). Due to the way YouTube stores files, the highest quality items are not progressive. Previously this required you to download them manually; but our program now has an option to merge them automatically (see step 4)!

3. Use the Media Type dropdown to filter items that match your needs. Note: If the dropdown is irresponsive, hover your mouse over the intended item and press Enter on your keyboard.

4. If you wish to have the highest possible quality video+audio, just press the "Auto Download Best Quality" button. We do the merging for you and output a `.mkv` file (Unfortunately, other file formats are not supported at this moment). If you wish to download an individual item listed in the list, select that item and press "Start Download".

5. A pop-up window with progress information will appear. Wait until the download is finished, then you can leave the program or download another video.

> [!NOTE]
> Due to how files are stored, you may see that audio files have the `.mp4` extension instead of the `.mp3` extension. This is normal behaviour and the file will still not contain the video part. Mainstream media players will correctly classify those as audio files, but you can still manually rename the extension to `.mp3` if needed.

> Besides, Please do not put files named `max_video` or `max_audio` inside the folder. These filenames are reserved for the program and will be deleted.


## Troubleshooting

#### chmod: No such file or directory
Please make sure that `downloader.command` is in the folder, and that you used "New Terminal at Folder" on the correct folder. Check for typpos within the file name as well.

#### Missing video description
Unfortunately, this may happen to some videos due to an issue with the library `pytube`. There is nothing we can do about this, but be assured as the video title should always be correct.

#### Common fixes
These are some generic items that you should check:

- MacOS (Unfortunately, only MacOS is supported right now, but we plan to add support for other operating systems soon.)
- Latest version of the project (check Step 1 of Installation to obtain the latest version)
- Correct URL entered in textbox
- Stable Internet connection

#### I found a bug that is not listed above! / I want to request a new issue!
Visit the [issue page](https://github.com/johann-lau/yt-downloader-mac/issues) and create a new issue. Please use the default templates provided if possible, and include the `log.log` file if needed. We will process your request as soon as possible.


## Developer
Would you like to contribute? Know someone proficient in Python or Shell scripting? Drop me a message or E-mail me at johannlau8888@gmail.com


## License
This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/4.0/ or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.