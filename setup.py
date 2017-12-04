######################################################################
# setup script for the Python wrapper of ODE
######################################################################

from distutils.core import setup, Extension
import distutils.sysconfig
import shutil, os, os.path, sys, glob, subprocess
from stat import *


def system(cmd):
   f = os.popen(cmd)
   return f.read()

# Include directories
INC_DIRS = []
# Library directories
LIB_DIRS = []
# Libraries to link with
LIBS = []
# Additional compiler arguments
CC_ARGS = []
CC_ARGS.extend(system("ode-config --cflags").split())
# Additional linker arguments
LINK_ARGS = []
LINK_ARGS.extend(system("ode-config --libs").split())

# If your version of ODE was compiled with OPCODE (trimesh support) enabled,
# this should be set to True.
TRIMESH_ENABLE = True

######################################################################
# Windows specific settings
######################################################################
if sys.platform=="win32":

   ODE_BASE = r"insert_your_path_here"
   INC_DIRS += [os.path.join(ODE_BASE, "include")]
   LIB_DIRS += [os.path.join(ODE_BASE, "lib", "releaselib")]

   LIBS     += ["ode", "user32"]  # user32 because of the MessageBox() call
   CC_ARGS  += ["/ML"]
   LINK_ARGS += ["/NODEFAULTLIB:LIBCMT"]

######################################################################
# Linux (and other) specific settings
######################################################################
else:

   for base in ["/usr", "/usr/local", "/opt/local"]:
      INC_DIRS += [os.path.join(base, "include")]
      LIB_DIRS += [os.path.join(base, "lib")]

   LIBS += ["ode", "stdc++"]

######################################################################
######################################################################
######################################################################

def info(msg):
   """Output an info message.
   """
   print("INFO:",msg)

def warning(msg):
   """Output a warning message.
   """
   print("WARNING:",msg)

def error(msg, errorcode=1):
   """Output an error message and abort.
   """
   print("ERROR:",msg)
   sys.exit(errorcode)

# Generate the C source file (if necessary)
def generate(name, trimesh_support):
   """Run Cython to generate the extension module source code.
   """

   # Generate the trimesh_switch file
   f = open("_trimesh_switch.pyx", "wt")
   print('# This file was generated by the setup script and is included in ode.pyx.\n', file=f)
   if (trimesh_support):
       print('include "trimeshdata.pyx"', file=f)
       print('include "trimesh.pyx"', file=f)
   else:
       print('include "trimesh_dummy.pyx"', file=f)
   f.close()

   cmd = "cython -o %s -I. -Isrc src/ode.pyx" % name
   cython_out = name

   # Check if the cython output is still up to date or if it has to be generated
   # (ode.c will be updated if any of the *.pyx files in the directory "src"
   # is newer than ode.c)
   if os.access(cython_out, os.F_OK):
       ctime = os.stat(cython_out)[ST_MTIME]
       for pyx in glob.glob("src/*.pyx"):
           pytime = os.stat(pyx)[ST_MTIME]
           if pytime>ctime:
               info("Updating %s"%cython_out)
               print(cmd)
               err = os.system(cmd)
               break
       else:
           info("%s is up to date"%cython_out)
           err = 0
   else:
       info("Creating %s"%cython_out)
       print(cmd)
       err = os.system(cmd)

   # Check if calling cython produced an error
   if err!=0:
       error("An error occured while generating the C source file.", err)

def install_ode():
    """Download and install ODE.
    """
    subprocess.check_call('./install_ode.sh')

######################################################################

# Check if ode.h can be found
# (if it is not found it might not be an error because it may be located
# in any of the include paths that are built into the compiler)
num = 0
for path in INC_DIRS:
   ode_h = os.path.join(path, "ode", "ode.h")
   if os.path.exists(ode_h):
       info("<ode/ode.h> found in %s"%path)
       num += 1

if num==0:
   warning("<ode/ode.h> not found. You can install ODE by running the install_ode.sh script."
           "If it's already installed you may have to adjust INC_DIRS")
   exit(1)
elif num>1:
   warning("ode.h was found more than once. Make sure the header and lib matches.")

# Generate all possible source code versions so that they can be
# packaged with the source archive and a user doesn't require Cython
generate('ode_trimesh.c', True)
generate('ode_notrimesh.c', False)

if (TRIMESH_ENABLE):
   info("Installing with trimesh support.")
   install = 'ode_trimesh.c'
else:
   info("INFO: Installing without trimesh support.")
   install = 'ode_notrimesh.c'

# Compile the module
setup(name = "Py3ODE",
     version = "1.2.0.dev5",
     description = "Port of PyODE for Python 3",
     author = "see file AUTHORS",
     author_email = "filipeabperes@gmail.com",
     license = "BSD or LGPL",
     url = "https://github.com/belbs/Py3ODE",
     packages = ["xode"],
     python_requires='>=3',
     install_requires=['cython'],
     ext_modules = [Extension("ode", [install]
                    ,libraries=LIBS
                    ,include_dirs=INC_DIRS
                    ,library_dirs=LIB_DIRS
                    ,extra_compile_args=CC_ARGS
                    ,extra_link_args=LINK_ARGS)
                   ])
