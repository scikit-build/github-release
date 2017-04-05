#!/usr/bin/env bash

set -ex

if [[ "${TRAVIS}" == "true" ]] && [[ ${TRAVIS_PYTHON_VERSION} != "3.5.2" ]]; then
  echo "Skipping package on upload on Travis using python != 3.5.2 [TRAVIS_PYTHON_VERSION: ${TRAVIS_PYTHON_VERSION}]"
  exit 0
fi

pip install .

REPO_NAME=j0057/github-release
PRERELEASE_NAME=latest
PACKAGE_DIR=./dist
EXPECTED_PACKAGE_COUNT=2

release_date=$(date -u "+%Y-%m-%d at %0k:%M %Z")
release_name="Latest (updated at ${release_date})"

# Check if packages have been generated
packages=(${PACKAGE_DIR}/*)
if [[ ${#packages[@]} -ne ${EXPECTED_PACKAGE_COUNT} ]]; then
  echo "Error: ${EXPECTED_PACKAGE_COUNT} packages are expected in ${PACKAGE_DIR}"
  ls ${PACKAGE_DIR}
  exit 1
fi

# If needed, create release
githubrelease --github-token ${GITHUB_UPLOAD_RELEASE_TOKEN} \
  release ${REPO_NAME} create --prerelease ${PRERELEASE_NAME} --name "${release_name}"

# Remove existing packages
githubrelease --github-token ${GITHUB_UPLOAD_RELEASE_TOKEN} \
  asset ${REPO_NAME} delete ${PRERELEASE_NAME} "*"

# Upload latest packages
githubrelease --github-token ${GITHUB_UPLOAD_RELEASE_TOKEN} \
  asset ${REPO_NAME} upload ${PRERELEASE_NAME} ${PACKAGE_DIR}/*

# Update release reference and name
sha=$(git rev-parse HEAD)
githubrelease --github-token ${GITHUB_UPLOAD_RELEASE_TOKEN} \
  release ${REPO_NAME} edit ${PRERELEASE_NAME} --target-commitish ${sha} --name "${release_name}"

