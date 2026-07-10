#!/bin/bash

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJ_DIR}"
git fetch origin
git pull origin ShellArc_Portable