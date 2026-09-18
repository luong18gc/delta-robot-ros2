from glob import glob

from setuptools import find_packages, setup

package_name = 'delta_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='luong18gc',
    maintainer_email='luong18gc@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'manual_control = delta_controller.interactive_control_node:main',
            'cartesian_control = delta_controller.cartesian_control_node:main',
            'gripper = delta_controller.gripper_node:main',
            'vision = delta_controller.vision_node:main',
            'calibrate_camera = delta_controller.calibrate_camera_node:main',
        ],
    },
)
