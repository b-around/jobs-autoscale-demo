#!/bin/bash
# This file logins to OCP based on pre-configured and pre-loaded environment variables

oc login --server $OCP_API -u $OCP_USER  -p $OCP_PASS
