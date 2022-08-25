/*
 * Run Parameters block for TD_muSR data.
 *
 *   Copyright (C) 1994 TRIUMF (Vancouver, Canada)
 *
 *   Authors: T. Whidden
 *
 *   Released under the GNU LGPL - see http://www.gnu.org/licenses
 *
 *   This program is free software; you can distribute it and/or modify it under
 *   the terms of the Lesser GNU General Public License as published by the Free
 *   Software Foundation; either version 2 of the License, or any later version.
 *   Accordingly, this program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 *   or FITNESS FOR A PARTICULAR PURPOSE. See the Lesser GNU General Public License
 *   for more details.
 *
 */

typedef struct {
	  UINT16     mrun;
	  UINT16     mhists;
	  UINT16     msclr;
	  UINT16     msupd;
	  UINT32     jtsc[18];
	  UINT32     jdsc[18];
	  UINT16     mmin;
	  UINT16     msec;
	  UINT16     mtnew[6];
	  UINT16     mtend[6];
	  UINT16     mlston[4];
	  UINT16     mcmcsc;
	  UINT16     mlocsc[2][6];
	  UINT16     mrsta;
	  INT32	     acqtsk;
	  char	     logfil[10];
	  INT16	     muic;
	  UINT32     nevtot;
	  UINT16     mhsts;
	  UINT16     mbins;
	  UINT16     mshft;
	  INT16      mspare[7];
	  char	     title[40];
	  char	     sclbl[72];
	  char	     coment[144];
} TMF_F_HDR;

typedef struct {
	union {
	    struct {
		UINT16	     ihist;
		UINT16	     length;
		UINT32	     nevtot;
		UINT16	     ntpbin;
		UINT32	     mask;
		UINT16	     nt0;
		UINT16	     nt1;
		UINT16	     nt2;
		char	     htitl[10];
		char	     id[2];
		char	     fill[32];
		INT16	     head_bin;
	    } h;
	    UINT16	     data[256];
	} u;
} TMF_H_RECD;

