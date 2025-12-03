#!/bin/bash

rm -rf ../uploads
cp -rf uploads ../uploads
cd .. && python3 auto_resc_generator.py && cd - 
