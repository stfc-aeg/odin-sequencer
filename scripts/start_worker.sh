#!/bin/bash
CELERY_LOG='{ ABSOLUTE PATH TO LOG }/celery'
SUPERV_LOG='{ ABSOLUTE PATH TO LOG }/supervisord'
SUPERV_RUN='/tmp/run'
PYTHON_PATH='{ ABSOLUTE PATH TO PYTHON VIRTUAL ENV }/bin/activate'
PROJECT_PATH='{ ABSOLUTE PATH TO ODIN SEQUENCER }/odin-sequencer/src'
CONF_PATH='{ SUPERVISORD CONFIG }/supervisord.conf'
################################################################################
# Help                                                                         #
################################################################################
Help()
{
    # Display Help
    echo "Script for starting one or more worker nodes."
    echo
    echo "options:"
    echo "  -h            Print help page."
    echo "  -c            Print current config."
    echo "  -a            Start all workers in workers.txt."
    echo "  -i url        Start worker at url."
    echo
    echo "Example 1: sh start_worker.sh -a"
    echo "Example 2: sh start_worker.sh -i worker.co.uk"
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
    echo "Celery log path:          $CELERY_LOG"
    echo "Supervisord log path:     $SUPERV_LOG"
    echo "Supervisord run path:     $SUPERV_RUN"
    echo "Python bin path:          $PYTHON_PATH"
    echo "Project path:             $PROJECT_PATH"
    echo "Supervisord conf path:    $CONF_PATH"
    echo
    echo "Config at start of start_worker.sh"
    echo
}

################################################################################
# StartAll                                                                     #
################################################################################
StartAll()
{
    # read each line of workers.txt and run StartOne for each.
    # [[ -n "$worker" ]] prevents the last line from being ignored if it doesn't end with a \n
    while IFS='' read -r worker || [ -n "$worker" ]; do
        echo "$worker"
        StartOne "$worker"
    done < workers.txt
}

################################################################################
# StartOne                                                                     #
################################################################################
StartOne()
{
    # ssh into worker, make sure all required directories are made, start virtual enviroment and then start celery node.
    ssh -n $1 "
        mkdir -p $CELERY_LOG;
        mkdir -p $SUPERV_LOG;
        mkdir -p $SUPERV_RUN;
        source $PYTHON_PATH;
        cd $PROJECT_PATH;
        supervisord -c $CONF_PATH ||
        supervisorctl -c $CONF_PATH start celery;
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
            StartAll
            exit
            ;;
        i)
            StartOne "$OPTARG"
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
