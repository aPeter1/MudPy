/*
 *  deglitch.c -- remove a reproducible spurious glitch from data
 *
 *   Copyright (C) 2014 TRIUMF (Vancouver, Canada)
 *
 *   Authors: Donald Arseneau
 *
 *   Released under the GNU GPL - see http://www.gnu.org/licenses
 *
 *   This program is free software; you can distribute it and/or modify it under
 *   the terms of the GNU General Public License as published by the Free
 *   Software Foundation; either version 2 of the License, or any later version.
 *   Accordingly, this program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 *   or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 *   more details.
 *
 * $Log: deglitch.c,v $
 * Revision 1.1  2015/06/06 00:56:48  asnd
 * Add deglitch program
 *
 *
 */

#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#if defined(__MSDOS__) || defined(_WIN32)
#include "../util/getopt.c"
#else
#include <unistd.h>
#endif
#include <math.h>

#include "mud.h"

int histlinregr( int b1, int b2, int bb1, int bb2, UINT32 y[], double * slo, double * inter, double * aver);

#define FNAME_LEN 128

#define OOPS goto oops

static int usage()
{
  printf( "\n" );
  printf( "Usage: deglitch file_name_or_number hist_num bin1 bin2 reference_file\n" );
  printf( "\n" );
  printf( "Smooth a glitch in one run, based on the same glitch in a different run,\n" );
  printf( "where that other \"reference\" run has no varying \"signal\" near the glitch.\n" );
  printf( "Choose a bin range that just covers the distorted but fixable bins.\n\n" );
  printf( "WARNING: The deglitched result is output to the original input file,\n" );
  printf( "         and the original content will be OVERWRITTEN! So work on personal\n" );
  printf( "         copies of input files.\n\n" );
  return( 0 );
}


int main( int argc, char** argv )
{
  char c;
  char mudfile[FNAME_LEN] = { 0 } ;
  char reffile[FNAME_LEN] = { 0 } ;
  int rnum;
  int ih;

  int i_fh, r_fh;
  UINT32 i_Type, r_Type;
  UINT32 HType, NumH;
  UINT32 NumBins, NBi, T0_Bin, GoodBin1, GoodBin2; 
  REAL64 BinSec, BSi;
  UINT32 * rData = NULL;
  UINT32 * iData = NULL;
  int bin1 = 0;
  int bin2 = 0;
  int n25;

  int fb1, fb2, fbb1, fbb2;
  double slo, inter, aver;
  int j;

  /*
   * Process command-line parameters
   * file_name_or_number hist_num bin1 bin2 reference_file
   */

  if ( argc != 6 ) return( usage() );

  strncpy( mudfile, argv[1], FNAME_LEN ); mudfile[FNAME_LEN-1] = '\0';
  if ( mudfile[0] == '\0' ) return( usage() );
  if ( sscanf( argv[2], "%d", &ih ) != 1 ) return( usage() );
  if ( sscanf( argv[3], "%d", &bin1 ) != 1 ) return( usage() );
  if ( sscanf( argv[4], "%d", &bin2 ) != 1 ) return( usage() );
  strncpy( reffile, argv[5], FNAME_LEN ); reffile[FNAME_LEN-1] = '\0';
  if ( reffile[0] == '\0' ) return( usage() );

  /*
   * Check for run number vs file name
   */
  if ( sscanf( mudfile, "%d%c", &rnum, &c ) == 1 ) {
    sprintf( mudfile, "%06d.msr", rnum );
  }
  if ( sscanf( reffile, "%d%c", &rnum, &c ) == 1 ) {
    sprintf( reffile, "%06d.msr", rnum );
  }

  /*
   *  Attempt open
   */
  i_fh = MUD_openReadWrite( mudfile, &i_Type);
  if (i_fh < 0) {
    /* failure.  See if we need .msr appended */
    if ( (strlen(mudfile) < FNAME_LEN-4) && (!strstr( mudfile, ".msr" )) ) {
      strcat( mudfile, ".msr" );
      i_fh = MUD_openReadWrite( mudfile, &i_Type);
    }
  }
  if (i_fh < 0) {
    fprintf( stderr, "Could not open file %s.\n", mudfile );
    return( 1 );
  }

  r_fh = MUD_openRead( reffile, &r_Type);
  if (r_fh < 0) {
    /* failure.  See if we need .msr appended */
    if ( (strlen(reffile) < FNAME_LEN-4) && (!strstr( reffile, ".msr" )) ) {
      strcat( reffile, ".msr" );
      r_fh = MUD_openRead( reffile, &r_Type);
    }
  }
  if (r_fh < 0) {
    fprintf( stderr, "Could not open file %s.\n", reffile );
    return( 1 );
  }


  /*
   * Opened file; get run type identifier and histogram type ident
   */

  if ( i_Type != MUD_FMT_TRI_TD_ID || r_Type != MUD_FMT_TRI_TD_ID ) {
    MUD_closeRead( i_fh );
    MUD_closeRead( r_fh );
    fprintf( stderr, "Data file(s) not TD MuSR.\n" );
    return( 2 );
  }

  if ( MUD_getRunDesc( i_fh, &i_Type ) == 0 || MUD_getRunDesc( r_fh, &r_Type ) == 0 ) {
    MUD_closeRead( i_fh );
    MUD_closeRead( r_fh );
    fprintf( stderr, "Could not read the run header(s).\n");
    return( 2 );
  }

  if ( i_Type != MUD_SEC_GEN_RUN_DESC_ID || r_Type != MUD_SEC_GEN_RUN_DESC_ID ) {
    MUD_closeRead( i_fh );
    MUD_closeRead( r_fh );
    fprintf( stderr, "Data file(s) not TD MuSR.\n" );
    return( 2 );
  }

  if ( MUD_getHists( r_fh, &HType, &NumH ) == 0 ) OOPS;
  if ( HType == MUD_GRP_GEN_HIST_ID ) {
    MUD_closeRead( i_fh );
    MUD_closeRead( r_fh );
    printf( "Histograms aren't counts.\n");
    return( 0 );
  }

  if ( ih <= 0 || ih > NumH ) {
    MUD_closeRead( i_fh );
    MUD_closeRead( r_fh );
    printf( "Invalid histogram number (%d of %d).\n", ih, NumH);
    return( 0 );
  }

  if( MUD_getHistNumBins(r_fh, ih, &NumBins) == 0 ) OOPS;
  if( MUD_getHistT0_Bin(r_fh, ih, &T0_Bin) == 0 ) OOPS;
  if( MUD_getHistGoodBin1(r_fh, ih, &GoodBin1) == 0 ) OOPS;
  if( MUD_getHistGoodBin2(r_fh, ih, &GoodBin2) == 0 ) OOPS;
  if( MUD_getHistSecondsPerBin(r_fh, ih, &BinSec) == 0 ) OOPS;
  if ( bin2 > NumBins || bin1 > bin2-2 || (bin2-bin1)*BinSec > 50.0e-9 ) {
    MUD_closeRead( i_fh );
    MUD_closeRead( r_fh );
    printf( "Improper bin range.\n");
    return( 0 );
  }
  rData = (UINT32*)malloc( 4*NumBins );
  if( MUD_getHistData(r_fh, ih, (void*)rData) == 0 ) OOPS;


  if ( MUD_getHists( i_fh, &HType, &NumH ) == 0 ) OOPS;
  if ( HType == MUD_GRP_GEN_HIST_ID ) {
    MUD_closeRead( i_fh );
    MUD_closeRead( r_fh );
    printf( "Histograms aren't counts.\n");
    return( 0 );
  }

  if ( ih <= 0 || ih > NumH ) {
    MUD_closeRead( i_fh );
    MUD_closeRead( r_fh );
    printf( "Invalid histogram number (%d of %d).\n", ih, NumH);
    return( 0 );
  }

  if( MUD_getHistNumBins(i_fh, ih, &NBi) == 0 ) OOPS;
  if( MUD_getHistT0_Bin(i_fh, ih, &T0_Bin) == 0 ) OOPS;
  if( MUD_getHistGoodBin1(i_fh, ih, &GoodBin1) == 0 ) OOPS;
  if( MUD_getHistGoodBin2(i_fh, ih, &GoodBin2) == 0 ) OOPS;
  if( MUD_getHistSecondsPerBin(r_fh, ih, &BSi) == 0 ) OOPS;
  if ( NumBins != NBi || BinSec != BSi ) {
    MUD_closeRead( i_fh );
    MUD_closeRead( r_fh );
    printf( "Those two runs have incompatable histograms.\n");
    return( 0 );
  }
  iData = (UINT32*)malloc( 4*NumBins );
  if( MUD_getHistData(i_fh, ih, (void*)iData) == 0 ) OOPS;

  /*
   * Using surrounding (/following) bins of the reference histogram, interpolate 
   * (/extrapolate) a straight line through the glitch region.
   */

  n25 = 1 + 25.0e-09/BinSec;
  if ( bin2+n25 > GoodBin2 ) { /* Use preceding bins */
    fb1 = bin1 - 2*n25;
    fb2 = bin1 - 1;
    fbb1 = fbb2 = 0;
  } 
  else if ( bin1-n25 < GoodBin1 ) { /* Use following bins */
    fb1 = bin2 + 1;
    fb2 = bin2 + 2*n25;
    fbb1 = fbb2 = 0;
  }
  else { /* Use surrounding bins */
    fb1 = bin1 - n25;
    fb2 = bin1 - 1;
    fbb1 = bin2 + 1;
    fbb2 = bin2 + n25;
  }

  j = histlinregr( fb1, fb2, fbb1, fbb2, rData, &slo, &inter, &aver);

  /*printf( "Regression says slope %lf, intercept %lf, average %lf\n", slo, inter, aver);*/

  /*
   * At present, no hueristic for choosing average instead of slope&intercept.
   *
   * Linear regression requires a short bin range. Perhaps we should do linear
   * fit of log(data-bkgd) to linearize exponential decay.
   */


  /* 
   * Now smooth glitch region in i data
   */

  for ( j=bin1-1; j<=bin2-1; j++ ) {
    /*  printf ( "Change bin %d from %d to %d\n", j+1, iData[j],
        (int)( 0.499 + ((double)iData[j]) / (((double)rData[j]) / (slo*j+inter)) ) ); */
    iData[j] = 0.499 + ((double)iData[j]) / (((double)rData[j]) / (slo*j+inter)) ;
  }

  if ( MUD_setHistData( i_fh, ih, (void*)iData ) == 0 ) {
    fprintf( stderr, "error setting histogram data\n");
    MUD_closeRead( r_fh );
    MUD_closeRead( i_fh );
    return(4);
  }

  /*
   *  Now write out the modified data to the outfile. 
   */

  MUD_closeRead( r_fh );

  if ( MUD_closeWrite( i_fh ) == 0 ) {
    fprintf( stderr, "failed to overwrite file \"%s\"\n", mudfile );
    MUD_closeRead( i_fh );
    return(4);
  }

  return( 0 );

 oops:
  MUD_closeRead( r_fh );
  MUD_closeRead( i_fh );
  fprintf( stderr, "Could not read some histogram information.\n" );
  return( 2 );

}


/*
 *  Specialized linear regression for histogram data, where all input data (x and y) 
 *  are integer, and the error in y is sqrt(y). The weighting of a point is
 *              1/w = y
 *  One or two subsets of bins are selected based on the b1,b2,bb1,bb2 parameters.
 *  The return value is a status:
 *           0 = OK, got an answer 
 *           1 = failed 
 *  Slope and intercept and average are returned in the parameter list
 *  (calling program may use average when there is a small range in x).
 *
 */


int histlinregr( int b1, int b2, int bb1, int bb2, UINT32 y[], double * slo, double * inter, double * aver)
{
  double sw, sx, sy, sxx, sxy, xj, yj, w, dis;
  double eps = 1.0e-12;
  int j; /* count index; note that index is bin_num -1 */

  sw  = 0.0;
  sx  = 0.0;
  sy  = 0.0;
  sxx = 0.0;
  sxy = 0.0;
  while ( b2 > b1 ) {
    for ( j = b1-1; j <= b2-1; j++ )
    {
        xj  = j;
        yj  = y[j];
        w   = 1.0/(yj+1.0);
        sw  += w;
        sx  += w*xj;
        sy  += w*yj;
        sxx += w*xj*xj;
        sxy += w*xj*yj;
    }
    b1 = bb1;
    b2 = bb2;
  }
  dis = sw*sxx-sx*sx;
  *aver = sy/sw;
  if (dis < eps*sw*sxx) return(1);
  *slo = (sxy*sw-sx*sy)/dis;
  *inter = ((sxx*sy)-(sx*sxy))/dis;
  return(0);
}

