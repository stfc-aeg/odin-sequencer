#!/bin/bash
PYTHON_PATH='{ ABSOLUTE PATH TO PYTHON VIRTUAL ENV }/bin/activate'
PROJECT_PATH='{ ABSOLUTE PATH TO ODIN SEQUENCER }/odin-sequencer/src'
CONF_PATH='{ SUPERVISORD CONFIG }/supervisord.conf'
################################################################################
# Help                                                                         #
################################################################################
Help()
{
    # Display Help
    echo "Script for stopping one or more worker nodes."
    echo
    echo "options:"
    echo "  -h            Print help page."
    echo "  -a            Stop all workers in workers.txt."
    echo "  -i url        Stop worker at url."
    echo
    echo "Example 1: sh stop_worker.sh -a"
    echo "Example 2: sh stop_worker.sh -i worker.co.uk"
    echo
}

################################################################################
# Config                                                                       #
################################################################################
Conf()
{
    # Display Config
    echo "Current config: "
    echo
    echo "Python bin path:          $PYTHON_PATH"
    echo "Project path:             $PROJECT_PATH"
    echo "Supervisord conf path:    $CONF_PATH"
    echo
    echo "Config at start of stop_worker.sh"
    echo
}

################################################################################
# StopAll                                                                      #
################################################################################
StopAll()
{
    # read each line of workers.txt and run StopOne for each.
    # [[ -n "$worker" ]] prevents the last line from being ignored if it doesn't end with a \n
    while IFS='' read -r worker || [ -n "$worker" ]; do
        echo "$worker"
        StopOne "$worker"
    done < workers.txt
}

################################################################################
# StopOne                                                                      #
################################################################################
StopOne()
{
    # ssh into worker, start virtual enviroment and then stop celery node.
    ssh -n $1 "
        source $PYTHON_PATH;
        cd $PROJECT_PATH;
        supervisorctl -c $CONF_PATH stop celery;
    "
}

################################################################################
################################################################################
# Main program                                                                 #
################################################################################
################################################################################

while getopts ":hai:" option; do
    case $option in
        h)
            Help
            exit
            ;;
        c)
            Conf
            exit
            ;;
        a)
            StopAll
            exit
            ;;
        i)
            StopOne "$OPTARG"
            exit
            ;;
        \?)
            echo 'Incorrect argument given'
            Help
            exit 1
            ;;
    esac
done

# if there isn't an agument given display the help page. 
if [ -z "$1" ]; then
    echo 'No argument given'
    Help
    exit
fi
