from setuptools import find_packages, setup

package_name = 'go2_tools'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='linar',
    maintainer_email='mgubitosi@udesa.edu.ar',
    description='Tools for Unitree Go2 marine platform simulation',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'marine_platform_simulator = go2_tools.marine_platform_simulator:main',
            'marine_manual_control = go2_tools.marine_manual_control:main',
        ],
    },
)
