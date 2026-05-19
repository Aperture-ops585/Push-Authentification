#!/bin/bash
# Log the PAM variables to verify it's working
echo "$(date): PAM called for user '$PAM_USER' from '$PAM_RHOST' (Service: $PAM_SERVICE)" >> /tmp/pam_test.log
exit 0
