from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'drone'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.xacro')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='linar',
    maintainer_email='mgubitosi@udesa.edu.ar',
    description='Drone simulation with downward-facing camera',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'drone_controller = drone.drone_controller:main',
            'aruco_detector = drone.aruco_detector:main',
            'drone_position_controller = drone.drone_position_controller:main',
        ],
    },
)
