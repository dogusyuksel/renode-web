#!/bin/bash

cd /workspace

git submodule update --init --recursive

cd /workspace/thirdparty/renode
git submodule update --init --recursive

cd /workspace/thirdparty/renode-infrastructure
git submodule update --init --recursive

cd /workspace/scripts
