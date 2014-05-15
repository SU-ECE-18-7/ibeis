ibeis
=====

I.B.E.I.S. = Image Based Ecological Information System


#--------------------
# Environment Setup:
#--------------------

# Navigate to your code directory
cd ~/code

# Clone the IBEIS repos
git clone https://github.com:Erotemic/utool.git
git clone https://github.com:Erotemic/vtool.git
git clone https://github.com/Erotemic/hesaff.git
git clone https://github.com/Erotemic/plottool.git
git clone https://github.com/Erotemic/guitool.git
git clone https://github.com/Erotemic/ibeis.git
# Set the previous repos up for development by running this
# command in each directory

sudo python ~/code/utool/setup.py develop
sudo python ~/code/vtool/setup.py develop
sudo python ~/code/hesaff/setup.py develop
sudo python ~/code/plottool/setup.py develop
sudo python ~/code/guitool/setup.py develop
sudo python ~/code/ibeis/setup.py develop


# Clone these repos
git clone https://github.com/Erotemic/opencv.git
git clone https://github.com/Erotemic/flann.git
git clone https://github.com/bluemellophone/pyrf.git
# Use the build scripts in their for either unix or mingw
# you dont need to build detecttools
git clone https://github.com/bluemellophone/detecttools.git
<!--git clone https://github.com/bluemellophone/IBEIS2014.git-->


#--------------------
# Main Commands
#--------------------
python main.py <optional-arguments> [--help]
python dev.py <optional-arguments> [--help]
# main is the standard entry point to the program
# dev is a more advanced developer entry point

# Useful flags.
# Read code comments in dev.py for more info.
# Careful some commands don't work. Most do. 
# --cmd          # shows ipython prompt with useful variables populated
# -w, --wait     # waits (useful for showing plots)
# --gui          # starts the gui as well (dev.py does not show gui by default, main does)
# -t [test]


#--------------------
# PSA: Workdirs: 
#--------------------
# IBEIS uses the idea of a work directory for databases.
# Use --set-workdir <path> to set your own, or a gui will popup and ask you about it

# use --db to specify a database in your WorkDir
# --setdb makes that directory your default directory
python dev.py --db <dbname> --setdb

# Or just use the absolute path
python dev.py --dbdir <full-dbpath>


#--------------------
# Examples:
# Here are are some example commands
#--------------------
# Run the queries for each roi with groundtruth in the PZ_MOTHERS database
# using the best known configuration of parameters
python dev.py --db PZ_MOTHERS --allgt -t best
