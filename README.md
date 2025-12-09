> epub2tts-kokoro is a free and open source python app to easily create a full-featured audiobook from an epub or text file using realistic text-to-speech using [Kokoro](https://github.com/hexgrad/kokoro).

## 🚀 Features

- [x] Creates standard format M4B audiobook file
- [x] Automatic chapter break detection
- [x] Embeds cover art if specified
- [x] Resumes where it left off if interrupted
- [x] NOTE: epub file must be DRM-free
- [X] Optional mp3 export for services like BookFunnel.com


## 📖 Usage
<details>
<summary> Usage instructions</summary>

*NOTE:* If you want to specify where NLTK tokenizer will be stored (about 50mb), use an environment variable: `export NLTK_DATA="your/path/to/nltk_data"`

## 🐋 Docker

```
podmand build -f Dockerfile.intel -f localhost/epub2tts-kokoro-intel .
```

```
alias epub2tts-k='podman run --rm -it --device /dev/dri \
    -v "$PWD:$PWD":Z \
    -v "$HOME/.cache/kokoro_hf_cache:/root/.cache/huggingface:Z" \
    -w "$PWD" \
    localhost/epub2tts-kokoro-intel'
```

## OPTIONAL - activate the virutal environment if using
1. `source .venv/bin/activate`

## FIRST - extract epub contents to text and cover image to png:
1. `epub2tts-kokoro mybook.epub`
2. **edit mybook.txt**, replacing `# Part 1` etc with desired chapter names, and removing front matter like table of contents and anything else you do not want read. **Note:** First two lines can be Title: and Author: to use that in audiobook metadata.

## Read text to audiobook:

* `epub2tts-kokoro mybook.txt --cover mybook.png`
* Optional: specify a speaker with `--speaker <speaker>`. [Check here for available voices](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md), default speaker is `af_heart` if `--speaker` is not specified. You can also generate speaker samples by running the script `python gen_samples.py`


## All options
* `-h, --help` - show this help message and exit
* `--speaker SPEAKER` - Speaker to use (example: af_heart)
* `--cover image.[jpg|png]` - Image to use for cover
* `--paragraphpause <N>` - Number of milliseconds to pause between paragraphs
* `--speed <N>` - Reading speed (ex 1.3)
* `--notitles` - Do not read chapter titles when creating audiobook
* `--keep-chapters` - Retain identified sections as numbered MP3 files

## Deactivate virtual environment
`deactivate`
</details>

## 🐞 Reporting bugs
<details>
<summary>How to report bugs/issues</summary>

Thank you in advance for reporting any bugs/issues you encounter! If you are having issues, first please [search existing issues](https://github.com/aedocw/epub2tts-kokoro/issues) to see if anyone else has run into something similar previously.

If you've found something new, please open an issue and be sure to include:
1. The full command you executed
2. The platform (Linux, Windows, OSX, Docker)
3. Your Python version if not using Docker

</details>

## 🗒️ Release notes
<details>
<summary>Release notes </summary>

* 20251209: Added `--keep-chapters` feature. Notes on ROCM situation.
* 20250224: Changed to read individual setences rather than entire paragraph, for reading speed consistency
* 20250221: Added `--notitles` option
* 20250216: Initial release

</details>

## 📦 Install

Required Python version is 3.11.

*NOTE:* If you want to specify where NLTK tokenizer will be stored (about 50mb), use an environment variable: `export NLTK_DATA="your/path/to/nltk_data"`

<details>
<summary>MAC INSTALLATION</summary>

This installation requires Python < 3.12 and [Homebrew](https://brew.sh/) (I use homebrew to install espeak, [pyenv](https://stackoverflow.com/questions/36968425/how-can-i-install-multiple-versions-of-python-on-latest-os-x-and-use-them-in-par) and ffmpeg).

```
#install dependencies
brew install espeak pyenv ffmpeg
#install epub2tts-kokoro
git clone https://github.com/aedocw/epub2tts-kokoro
cd epub2tts-kokoro
pyenv install 3.11
pyenv local 3.11
#OPTIONAL - install this in a virtual environment
python -m venv .venv && source .venv/bin/activate
pip install .
```
</details>

<details>
<summary>LINUX INSTALLATION</summary>

These instructions are for Ubuntu 24.04.1 LTS and 22.04  (20.04 showed some depedency issues), but should work (with appropriate package installer mods) for just about any distro. Ensure you have `ffmpeg` installed before use.

```
#install dependencies
sudo apt install espeak-ng ffmpeg python3-venv
#clone the repo
git clone https://github.com/aedocw/epub2tts-kokoro
cd epub2tts-kokoro
#OPTIONAL - install this in a virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install .
```

</details>

<details>
<summary>WINDOWS INSTALLATION</summary>

Running epub2tts in WSL2 with Ubuntu 22 is the easiest approach, but these steps should work for running directly in windows.

### Windows 11 via PowerShell

No issues were encountered following the procedure for required components and utilizing choco when an option:

To install precompiled binaries of eSpeak NG on Windows:

1. open (https://github.com/espeak-ng/espeak-ng/releases) and click on Latest release and then appropriate *.msi file, e.g. espeak-ng-20191129-b702b03-x64.msi
2. Execute downloaded installer package.

</details>

<details>
<summary>GPU Support</summary>

## ROCM pyTorch Status

(TBD): Some issues cropped up on ROCM enabled systems where mismatch of ROCM backend (torch.cuda.is_available() returns true) but no ROCM device is present. To bypass that on effected systems, removed test for ROCM backend. 
* A path forward exists and will be added in a future patch. It will involve compiling wheel files via: https://github.com/scottt/rocm-TheRock/blob/gfx1151/docs/development/windows_support.md

Some creative pinning of torch, torchaudio and torchvision will be required. 

### Hardware Notes:

To have any chance of making a ROCm card work, you will need to identify the chipset. EG: 
RX6800 --> gfx103X --> RDNA2 (Not RDNA3!) Doesn't have WMMA, and thus may never work for GPU acceleration with this process.

*Issues* Some common but slightly older cards in the gfx10 arch may never work again, or never work outside very narrow bespoke combinations of cuda, pytorch, python and rocm. It's likely never going to happen.

</details>


## Updating

<details>
<summary>UPDATING YOUR INSTALLATION</summary>

1. cd to repo directory
2. `git pull`
3. Activate virtual environment you installed epub2tts in if you installed in a virtual environment using "source .venv/bin/activate"
4. `pip install . --upgrade`
</details>


## Author

👤 **Christopher Aedo**

- Website: [aedo.dev](https://aedo.dev)
- GitHub: [@aedocw](https://github.com/aedocw)
- LinkedIn: [@aedo](https://linkedin.com/in/aedo)

👥 **Contributors**

[![Contributors](https://contrib.rocks/image?repo=aedocw/epub2tts-kokoro)](https://github.com/aedocw/epub2tts-kokoro/graphs/contributors)

## 🤝 Contributing

Contributions, issues and feature requests are welcome!\
Feel free to check the [issues page](https://github.com/aedocw/epub2tts-kokoro/issues) or [discussions page](https://github.com/aedocw/epub2tts-kokoro/discussions).

## Show your support

Give a ⭐️ if this project helped you!
