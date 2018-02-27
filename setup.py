from setuptools import setup, find_packages

setup(
    name='sirius',
    version='0.0.6',
    description='Stellar Python SDK for Humans.',
    url='https://github.com/hard-codr/sirius.git',
    license='Apache',
    author='hardcodr',
    author_email='hello@hardcodr.com',
    include_package_data=True,
    packages=find_packages(),
    test_suite = 'nose.collector',
    classifiers=[
        'Development Status :: 0 - Alpha/unstable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'ed25519', 'crc16', 'requests', 'sseclient',
    ],
    tests_require = [
        'mock', 'nose',
    ],
)
