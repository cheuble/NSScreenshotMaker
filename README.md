# NSScreenshotMaker
NSScreenshotMaker is a tool that will allow you to sign images for the Nintendo Switch. The Switch has an album function to view your screenshots, but it can't read images you put yourself on the SD card.  
This tool's purpose is to sign any image so the Switch can read it. I don't really see any use for it, but eh, some people want it ¯\\_(ツ)_/¯
## Requirements
* The Nintendo Switch capsrv screenshot HMAC secret key
* [Python3](https://www.python.org/downloads/)
* [PIL](http://pillow.readthedocs.io/en/5.1.x/installation.html)
* [piexif](http://piexif.readthedocs.io/en/latest/installation.html)  
You might otherwise use the [exe](https://github.com/cheuble/releases) file which doesn't need those requirements (except for the key). Your antivirus may block it though.  
## Usage
* Find the "Nintendo Switch capsrv screenshot HMAC secret" key (Can't share it here for legal reasons). Either save it in a key.bin file, or pass it as an argument when running the program.
* Create an `input` folder, and put your images in it. Images can be all sizes and formats that [PIL supports](http://pillow.readthedocs.io/en/4.1.x/handbook/image-file-formats.html).
* Download the program and run it. It should output an `SD` folder. Extract its content to the root of your Switch's SD card.
## Contributing
* [Fork it](https://github.com/cheuble/NSScreenshotMaker/fork)
* Create your feature branch: `git checkout -b feature`
* Commit your changes: `git commit -am 'Added feature'`
* Push to the branch: `git push origin feature`
* Submit a pull request
## History
* 1.0.0
    * Initial release
## License
This project is licensed under the MIT License. See the [LICENSE.md](LICENSE.md) file for details.
## Thanks
* [SciresM](https://github.com/SciresM) for documenting how the Screenshot verification works on [switchbrew](http://switchbrew.org/index.php?title=Capture_services#Notes), and for the key.
* [s0r00t](https://github.com/s0r00t) for testing
