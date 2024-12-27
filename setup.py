from setuptools import setup, find_packages

setup(
    name='story_weaver',
    version='0.1',
    packages=find_packages(),
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
        ],
    },
    author='Kaitlyn Hennacy',
    author_email='kaitlynhennacy@gmail.com.com',
    description='A package for story weaker',
    url='https://github.com/kaittah/story_weaver',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)