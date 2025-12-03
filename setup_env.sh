#!/bin/bash


git submodule update --init --recursive

cd thirdparty/renode
git submodule update --init --recursive
cd -

cd thirdparty/renode-infrastructure
git submodule update --init --recursive
cd -
