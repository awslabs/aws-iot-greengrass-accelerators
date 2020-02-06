#!/bin/sh

set -e

# Initial check before starting greengrassd
# Check if User Lambdas are starting in GreengrassContainer mode
if grep -q "GreengrassContainer" /greengrass/ggc/deployment/group/group.json; then
 echo "User Lambdas with GreengrassContainer mode aren't supported to run inside the GGC Docker Container. For troubleshooting, start a fresh deployment by following this guide: https://docs.aws.amazon.com/greengrass/latest/developerguide/run-gg-in-docker-container.html#docker-no-container. Finally, restart the GGC docker container after bind-mounting an empty deployment folder."
 exit 1;
fi

# For docker container support, set group to docker on the /var/run/docker.sock
usermod -a -G docker ggc_user
# Change the container's "docker" group ID to the hosts group id
ls -l /var/run/docker.sock | cut -d' ' -f4 | xargs -I 'GID' sed -i -E 's/docker:x:(.*):/docker:x:GID:/' /etc/group

# need to invoke the child process with "&"" in order for the parent shell script to catch SIGXXX
/greengrass/ggc/core/greengrassd start &

# from https://unix.stackexchange.com/questions/146756/forward-sigterm-to-child-in-bash
_term() {
    echo "Caught SIGTERM signal!"
    kill -TERM "$daemon_pid" 2>/dev/null
}
trap _term SIGTERM

# - since the greengrassd spawns its own child process, wait for the
#   /var/run/greengrassd.pid
while [ ! -e /var/run/greengrassd.pid ]
do
    sleep 1;
done

# wait "$daemon_pid" does not work. Has to keep this logic
daemon_pid=`cat /var/run/greengrassd.pid`
# block docker exit until daemon process dies.
while [ -d /proc/$daemon_pid ]
do
 # Sleep for 1s before checking that greengrass daemon is still alive
 daemon_cmdline=`cat /proc/$daemon_pid/cmdline`
 if [[ $daemon_cmdline != ^/greengrass/ggc/packages/1.10.0/bin/daemon.* ]]; then 
  sleep 1;
 else
  break;
 fi;
done 