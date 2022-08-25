#   makefile for MUD library.
#  $Log: makefile,v $
#  Revision 1.3  2017/06/28 00:52:53  asnd
#  Provide make shared.
#
#  Revision 1.2  2010/08/25 23:52:46  asnd
#  Fix up builds on different platforms, including mac, windows, 64bit Linux, new Linux
#  dstros without termcap (readline is not used by default in mud_util for easy make
#  without configure).
#
#  Revision 1.1  2001/09/13 04:59:42  asnd
#  DA - Fixup make files (now separate, with overall Makefile)
#

ifndef LIB_DIR
LIB_DIR    :=.
endif
ifndef INSTALL_DIR
INSTALL_DIR := ../lib
endif

#  Specify intended Fortran compiler compatibility by uncommenting a line, or assigning
#  FORT on the "make" command.
#  (see cfortran.h)

#  FORT = g77
#  FORT = f2cFortran
#  FORT = AbsoftUNIXFortran
#  FORT = AbsoftProFortran
#  etc.  Many compilers would need no definition.  Use "g77" for gfortran compatability.

CC    = gcc
CC_SWITCHES =  -O2
DEBUG =
MFLAG =
# set MFLAG for compiling to different word size; like "make MFLAG=-m32"

# mud.h version 1.3 :
SONAME = libmud.so.1
SOVERS = 3

CFLAGS = -I.
LIB  =  $(LIB_DIR)/libmud.a
OBJS =  mud.o mud_misc.o mud_all.o mud_new.o mud_gen.o \
        mud_tri_ti.o mud_encode.o \
        mud_friendly.o 


ifdef FORT
FDEF = -D$(FORT)
OBJS += fmud_friendly.o mud_fort.o 
else
FDEF =
endif

SOFILE = $(LIB_DIR)/$(SONAME).$(SOVERS)

shared : CC_SWITCHES +=  -fPIC

%.o: %.c mud.h
	$(CC) $(MFLAG) $(DEBUG) $(CFLAGS) -c $(CC_SWITCHES) $(FDEF) $<

all: $(LIB)

install: $(LIB)
	cp $(LIB) $(INSTALL_DIR)

$(LIB): $(OBJS)
	rm -f $@
	ar r $@ $(OBJS)
	ranlib $@

clean:
	rm -f $(LIB) $(OBJS) $(LIB_DIR)/$(SONAME)*

fmud_friendly.o : cfortran.h

shared: $(OBJS)
	$(CC) -shared -Wl,-soname,$(SONAME) -o $(SOFILE) $(OBJS) 
