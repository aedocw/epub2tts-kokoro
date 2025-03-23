from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="epub2tts-kokoro",
    description="Tool to read an epub to audiobook using kokoro TTS",
    author="Christopher Aedo aedo.dev",
    author_email="c@aedo.dev",
    url="https://github.com/aedocw/epub2tts-kokoro",
    license="GPL 3.0",
    version="1.2.3",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'epub2tts-kokoro = epub2tts_kokoro:main'
        ]
    },
)
