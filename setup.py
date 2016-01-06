from setuptools import setup, find_packages
import android_autotools

with open('README.rst') as f:
    desc = f.read()

setup(
    name = "android-autotools",
    version = android_autotools.__version__,
    packages = find_packages(),
    author = "Brendan Molloy",
    author_email = "brendan+pypi@bbqsrc.net",
    description = "Handles autotools mayhem for Android development",
    license = "BSD-2-Clause",
    keywords = "autotools android cross-compilation",
    url = "https://github.com/bbqsrc/android-autotools",
    long_description=desc,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5"
    ],
    entry_points = {
        'console_scripts': [
            'abuild = android_autotools.__main__:main'
        ]
    }
)
