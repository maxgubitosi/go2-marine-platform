from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'fixed_camera'

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
    description='Fixed downward-facing camera for ArUco detection over marine platform',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_controller = fixed_camera.camera_controller:main',
            'aruco_detector = fixed_camera.aruco_detector:main',
        ],
    },
)
