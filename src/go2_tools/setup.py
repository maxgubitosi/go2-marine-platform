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
    maintainer_email='linar@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'body_pose_smoother = go2_tools.body_pose_smoother:main',
            'body_posture_effort_ctrl = go2_tools.body_posture_effort_ctrl:main',
            'marine_platform_simulator = go2_tools.marine_platform_simulator:main',
            'marine_manual_control = go2_tools.marine_manual_control:main',
        ],
    },
)
