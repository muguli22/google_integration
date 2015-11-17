# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

version = '1.0.0'

with open("requirements.txt", "r") as f:
	install_requires = f.readlines()
	
setup(
    name='google_integration',
    version=version,
    description='Application will enable syncing of Calendar and Contacts from ERPNext to Google and vice versa.',
    author='Frappe Technologies Pvt. Ltd.',
    author_email='info@frappe.io',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
