# First client sends message to auth server containing uname, pwd
# Stores in db and checks
# If credentials don't match, then reject the user
# If they match, forward to other servers (load balancing)