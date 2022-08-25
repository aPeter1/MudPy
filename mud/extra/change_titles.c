
/*
 *  change_titles.c -- Change MUD file header fields.
 *
 *   Copyright (C) 2005-2021 TRIUMF (Vancouver, Canada)
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
 *   or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
 *   for more details.
 *
 * $Log: change_titles.c,v $
 * Revision 1.6  2021/09/15 18:58:47  asnd
 * eliminate less-portable strcasecmp
 *
 * Revision 1.5  2015/05/18 18:58:47  asnd
 * spelling/typo fix
 *
 * Revision 1.4  2012/12/18 17:19:46  asnd
 * Refactor program to better reflect yesterday's update (command mode)
 *
 * Revision 1.3  2012/12/17 23:05:39  asnd
 * Perform single change from the command line
 *
 * Revision 1.2  2010/08/26 00:12:34  asnd
 * Release under the GNU GPL.
 *
 * Revision 1.1  2005/06/14 01:38:31  asnd
 * Create extra utilities dir, containing initial version of change_titles
 *
 */

#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
/* No: #include <strings.h> */

#include "mud.h"

#define MAX_ERR 100


int change_titles( int argc, char** argv);
static int matchcmd(char* command, char* prototype, int len);
static int trimSpace( char* str );

static void field_error( int i_fh, char* Name);
static int displaynum( int i_fh, int (*MUD_get)(int,UINT32*), char* Name );
static int displaystr( int i_fh, int (*MUD_get)(int,char*,int), char* Name );
static int displayhistnum( int i_fh, int (*MUD_get)(int,int,UINT32*), char* Name, int NumH );
static int displayhiststr( int i_fh, int (*MUD_get)(int,int,char*,int), char* Name, int NumH );
static int replacestr(int i_fh, int (*MUD_set)(int,char*), char* Name, char* value);
static int replacenum(int i_fh, int (*MUD_set)(int,UINT32), char* Name, char* value);
static int replacehiststr(int i_fh, int (*MUD_set)(int,int,char*), char* Name, int NumH, char* value);
static int replacehistnum(int i_fh, int (*MUD_set)(int,int,UINT32), char* Name, int NumH, char* value);
static int replace_field(int i_fh,  char* entry, char* value);
static int display_headers(int i_fh);
static int close_for_exit (int i_fh, char* fname);

int errcnt;

UINT32 i_Type;
UINT32 HType, NumH;

static void usage()
{
    printf( "\n" );
    printf( "Usage: change_titles [file-name-or-run-number  [field-name  new-value] ]\n" );
    printf( "Supply zero, one, or three arguments.  If nothing is specified, you will\n" );
    printf( "be prompted for the file; supply the file path and name, or just the run\n" );
    printf( "number, if the file is in the current directory.\n" );
    printf( "If all 3 arguments are supplied, the single header field will be changed\n" );
    printf( "to the new value.\n" );
    printf( "Otherwise, you will be prompted (ct>) for changes to make in the headers.\n");
    printf( "When prompted, enter replacement fields as <field name> value(s)\n" );
    printf( "or one of the commands: exit, quit, show, help.\n" );
    printf( "\n" );
}

static void helpText()
{
  usage();

  printf("Type 'exit' to save changes and finish; 'quit' to abandon changes;\n");
  printf("'show' to display current values; 'help' for this help.\n");
  printf("\n");
  printf("When replacing header fields, the field name is case-insensitive,\n");
  printf("and may be abbreviated to 4 characters.\n");
  printf("\n");
  printf("Histogram parameters should be typed as a comma-separated list.\n");
  printf("Spaces around the commas are insignificant.  Blank items are\n");
  printf("left unchanged in the run file.  (You can't enter a blank histogram\n");
  printf("title, or one with a comma! Nor should you.)\n");
  printf("\n");
}


int main( int argc, char** argv )
{
  char* p;

  if( argc > 4 || argc == 3 )
    {
      usage();
      exit( 1 );
    }
  else if( argc == 4 )
    {  /*   single-shot change from command line  */
      exit ( change_titles( argc-1, &argv[1] ) );
    }
  else if( argc == 2 )
    {  /*   interactive with prompting  */
      if( matchcmd( argv[1], "help", 3 ) || matchcmd( argv[1], "?", 1 ) ) 
        {
          usage();
          exit(0);
        }
      exit ( change_titles( argc-1, &argv[1] ) );
    }
  else if( argc < 2 )
    {  /*   prompt for file name; then interactive with prompting  */ 
      int stat;
      char fname[128];
      do {
        printf( "Enter Mud file name or run number: " );
        if( !fgets(fname,126,stdin) ) exit( 0 );
        fname[127]='\0';
        p = strchr( fname, '\n' );
        if( p ) *p = '\0';
        p = fname;
        if( matchcmd( p, "help", 3 ) || matchcmd( p, "?", 1 ) ) 
          {
            usage();
            stat = 1;
          }
        else
          {
            stat = change_titles( 1, &p );
          }
      } while ( stat == 2 || stat == 1 );
      exit ( stat );
    }
  exit(0);
}

#define DisplayNUM(Object,Name) \
  if( !displaynum( i_fh, MUD_get##Object, Name ) ) \
  { field_error(i_fh,Name); return ( 2 ); }

#define DisplaySTR(Object,Name) \
  if( !displaystr( i_fh, MUD_get##Object, Name ) ) \
  { field_error(i_fh,Name); return ( 2 ); }

#define DisplayHistNUM(Object,Name) \
  if( !displayhistnum( i_fh, MUD_get##Object, Name, NumH ) ) \
  { field_error(i_fh,Name); return ( 2 ); }

#define DisplayHistSTR(Object,Name) \
  if( !displayhiststr( i_fh, MUD_get##Object, Name, NumH) ) \
  { field_error(i_fh,Name); return ( 2 ); }

#define ReplaceNUM(Object,Name,command,arg) \
  if( matchcmd(command,Name,4) ) {\
    replacenum(i_fh,MUD_set##Object,Name,arg);\
    return ( 0 );}

#define ReplaceSTR(Object,Name,command,arg) \
  if( matchcmd(command,Name,4) ) {\
    replacestr(i_fh,MUD_set##Object,Name,arg);\
    return ( 0 );}

#define ReplaceHistNUM(Object,Name,command,arg) \
  if( matchcmd(command,Name,4) ) {\
    replacehistnum(i_fh,MUD_set##Object,Name,NumH,arg);\
    return ( 0 );}

#define ReplaceHistSTR(Object,Name,command,arg)    \
  if( matchcmd(command,Name,4) ) {\
    replacehiststr(i_fh,MUD_set##Object,Name,NumH,arg);\
    return ( 0 );}

/* 
 *  change_titles:
 *  This is the main routine.  It does:
 *   - Open the mud data file
 *   - Read and display the existing headers
 *   - Loop, prompting for replacement commands (or quit/exit)
 *   - Close file (abandon changes on quit)
 *
 *  Parameter: string: file name or portion.
 *  Return value is the exit code:
 *  0 OK  
 *  1 no file
 *  2 failure to read file
 *  3 changes abandoned (EOF)
 *  4 abandon due to error(s)
 */

int change_titles( int argc, char** argv )
{
  int rnum;
  char c;
  char fname[127+1];

  char cmdline[256], command[256], arg1[512], rest[256];
  int na = -1;
  int stat;
  int i_fh;

  errcnt = 0;

  /*
   * Check for run number vs file name
   */
  if ( sscanf( argv[0], "%d%c", &rnum, &c ) == 1 ) {
    /* pure number, construct file name */
    sprintf( fname, "%06d.msr", rnum );
  }
  else {
    /* non-numeric */
    strncpy( fname, argv[0], 127 );
    fname[127]='\0';
  }

  /*
   *  Attempt open
   */
  i_fh = MUD_openReadWrite( fname, &i_Type);
  if (i_fh < 0) {
    /* failure.  See if we need .msr appended */
    if ( (strlen(fname) < 127-4) && (!strstr( fname, ".msr" )) ) {
      strcat( fname, ".msr" );
      i_fh = MUD_openReadWrite( fname, &i_Type);
    }
  }
  if (i_fh < 0) {
    /* Still failure; die. */
    fprintf( stderr, "Could not open file %s for modification.\n%s\n",
             fname, "Check that it exists and you have write access.");
    return( 1 );
  }

  /*
   *  Opened file; get run type identifier and number of histograms
   */

  if (MUD_getRunDesc( i_fh, &i_Type ) == 0 || MUD_getHists( i_fh, &HType, &NumH ) == 0) {
    MUD_closeRead( i_fh );
    fprintf( stderr, "Could not read the run header from %s.\n%s\n",
             fname, "Is it really a MUD file?");
    return( 2 );
  }

  /* 
   * Perform single-shot change given on command line, and return.
   */
  if (argc == 3 ) { /* command and arg were given. Ensure termination. */
    strncpy( command, argv[1], 255);
    command[255] = '\0';
    strncpy( arg1, argv[2], 511);
    arg1[511] = '\0';
  
    stat = replace_field( i_fh, command, arg1 );

    return ( close_for_exit( i_fh, fname ) );
  }

  /* 
   * So not single-shot ...  we will prompt for changes in a loop.
   * First display existing headers (like "show" command)
   */
  stat = display_headers( i_fh );
  if ( stat ) return( stat );
  printf( "\nNow enter replacement lines or one of: quit, exit, show, help\n\n" );

  /*
   * Now do changes, repeatedly.
   */
  while( 1 )
    {
      if( errcnt > MAX_ERR ) {
        printf( "Too many errors; quitting.\n" );
        MUD_closeRead( i_fh );
        return( 4 );
      }

      /* prompt for command and argument */
      printf( "ct> " );
      fflush( stdout );
      
      if( fgets( cmdline, 256, stdin ) == NULL ) {
        MUD_closeRead( i_fh );
        return( 3 );
      }
      cmdline[255]='\0';
      arg1[0] = '\0';
      
      na = sscanf( cmdline, "%s %s%[^\n]", command, arg1, rest );
      
      if( na < 1 ) {
        printf( "Type exit to apply changes and finish; or quit to abandon\n");
        errcnt++;
        continue;
      }
        
      /*
       * Process commands exit, quit, show, help
       */
      if( matchcmd( command, "exit", 4 ) ) { /* avoid clash with "experiment" */
        return ( close_for_exit( i_fh, fname ) );
      }
      
      if( matchcmd( command, "quit", 1 ) ) {
        MUD_closeRead( i_fh );
        return( 3 );
      }
      
      if( matchcmd( command, "show", 3 ) ) {
        display_headers( i_fh );
        continue;
      }
      
      if( matchcmd( command, "help", 4 ) || matchcmd( command, "?", 1 )) {
        helpText();
        continue;
      }
      /*
        if( na < 2 ) {
        printf( "Invalid replacement command; use format as shown above.\nType exit to finish, quit to abandon\n");
        errcnt++;
        continue;
        }
      */
      
      /* 
       * If replacement value was split due to space(s) concatenate the rest
       */
      if( na > 2 ) {
        strncat( arg1, rest, 255 );
      }  

      /*
       * Have the field and value; perform the change
       */
      stat = replace_field( i_fh, command, arg1 );

      if ( stat == 4 ) {
        printf( "Type exit to finish, quit to abandon\n");
        errcnt++;
      }
 
    } /* end while (repeats to get next user entry) */ 
}


static int close_for_exit ( int i_fh, char* fname )
{
  if( MUD_closeWrite(i_fh) == 0) {
    fprintf( stderr, "Could not write to file %s.\n%s\n",
             fname, "Has it just disappeared?" );
    MUD_closeRead( i_fh );
    
    return( 4 );
  }
  return( 0 );
}


static void field_error( int i_fh, char* Name)
{
  MUD_closeRead( i_fh );
  fprintf( stderr, "Error processing %s.\n", Name);
}


/*
 * Display Header fields:
 * input parameters: i_fh ; but uses global i_Type also
 * output parameters: none; but sets globals HType, NumH
 * returns: status code as above.
 * Note: "Display" actions are coded in macros.
 */
 
static int display_headers( int i_fh )
{
  /* globals: i_Type,  HType, NumH; */
  DisplayNUM(RunNumber,"RunNumber");
  DisplayNUM(ExptNumber,"Experiment");
  DisplaySTR(Experimenter,"Operator");
  DisplaySTR(Title,"Title");
  DisplaySTR(Sample,"Sample");
  DisplaySTR(Orient,"Orient");
  
  if (i_Type == MUD_SEC_TRI_TI_RUN_DESC_ID) {
    DisplaySTR(Subtitle,"Subtitle");
  }
  else {
    DisplaySTR(Temperature,"Temperature");
    DisplaySTR(Field,"Field");
  }
  DisplaySTR(Area,"Beamline");
  DisplaySTR(Apparatus,"Rig");
  DisplaySTR(Insert,"Mode");
  
  if ( i_Type == MUD_SEC_TRI_TI_RUN_DESC_ID ) {
    DisplaySTR(Comment1,"Cmt1");
    DisplaySTR(Comment2,"Cmt2");
    DisplaySTR(Comment3,"Cmt3");
  }
  
  DisplayNUM(TimeBegin,"Startsec");
  DisplayNUM(TimeEnd,"Endsec");
  DisplayNUM(ElapsedSec,"Elapsedsec");
  
  /* Then the lists of parameters from the histogram headers */
  
  if ( MUD_getHists( i_fh, &HType, &NumH ) == 0 ) return( 2 );
  
  DisplayHistSTR(HistTitle,"HTitles");
  
  if ( i_Type != MUD_SEC_TRI_TI_RUN_DESC_ID ) {
    DisplayHistNUM(HistT0_Bin,"t0Bins");
    DisplayHistNUM(HistT0_Ps,"t0Ps");
    DisplayHistNUM(HistGoodBin1,"t1Bins");
    DisplayHistNUM(HistGoodBin2,"t2Bins");
    DisplayHistNUM(HistBkgd1,"Bg1Bins");
    DisplayHistNUM(HistBkgd2,"Bg2Bins");
  }
  return( 0 );
}

/*
 * Replace one item in the run geader, or one item in all hist headers.
 * input parameters: i_fh, strings entry and value; also globals.
 * output parameters: none
 * returns: status code as above.
 * Note: "Replace" actions are coded in macros.
 */
static int replace_field( int i_fh, char* entry, char* value )
{
  /* globals:  i_Type,  HType, NumH; */

  ReplaceNUM(RunNumber,"RunNumber",entry,value);
  ReplaceNUM(ExptNumber,"Experiment",entry,value);
  ReplaceSTR(Experimenter,"Operator",entry,value);
  ReplaceSTR(Title,"Title",entry,value);
  ReplaceSTR(Sample,"Sample",entry,value);
  ReplaceSTR(Orient,"Orient",entry,value);
  
  if (i_Type == MUD_SEC_TRI_TI_RUN_DESC_ID) {
    ReplaceSTR(Subtitle,"Subtitle",entry,value);
  }
  else {
    ReplaceSTR(Temperature,"Temperature",entry,value);
    ReplaceSTR(Field,"Field",entry,value);
  }
  ReplaceSTR(Area,"Beamline",entry,value);
  ReplaceSTR(Apparatus,"Rig",entry,value);
  ReplaceSTR(Insert,"Mode",entry,value);
  
  if (i_Type == MUD_SEC_TRI_TI_RUN_DESC_ID) {
    ReplaceSTR(Comment1,"Cmt1",entry,value);
    ReplaceSTR(Comment2,"Cmt2",entry,value);
    ReplaceSTR(Comment3,"Cmt3",entry,value);
  }
  
  ReplaceNUM(TimeBegin,"Startsec",entry,value);
  ReplaceNUM(TimeEnd,"Endsec",entry,value);
  ReplaceNUM(ElapsedSec,"Elapsedsec",entry,value);
  
  if( NumH > 0 ) {
    ReplaceHistSTR(HistTitle,"HTitles",entry,value);

    if ( i_Type != MUD_SEC_TRI_TI_RUN_DESC_ID ) {
      ReplaceHistNUM(HistT0_Bin,"t0Bins",entry,value);
      ReplaceHistNUM(HistT0_Ps,"t0Ps",entry,value);
      ReplaceHistNUM(HistGoodBin1,"t1Bins",entry,value);
      ReplaceHistNUM(HistGoodBin2,"t2Bins",entry,value);
      ReplaceHistNUM(HistBkgd1,"Bg1Bins",entry,value);
      ReplaceHistNUM(HistBkgd2,"Bg2Bins",entry,value);
    }
  }
  
  /* If we get here, then none of the Replace macros was applied */
  fprintf( stderr, "Error: Unknown header entry: %s.\n", entry);
  return( 4 );
}

/*
 * displaynum and displaystr:
 * Show a field.  Return boolean for success (1=success)
 */
static int displaynum( int i_fh, int (*getProc)(int,UINT32*), char* name )
{
  UINT32 num;

  if( (*getProc)(i_fh,&num) == 0 ) return 0;

  printf( "%-12s %d\n", name, num );

  return 1;
}

static int displaystr( int i_fh, int (*getProc)(int,char*,int), char* name )
{
  char field[256];

  if( (*getProc)(i_fh,field,255) == 0 ) return 0;

  printf( "%-12s %s\n", name, field );

  return 1;
}


static int displayhistnum( int i_fh, int (*getProc)(int,int,UINT32*), char* name, int nh )
{
  UINT32 num;
  int j;

  for( j=1; j<=nh; j++) {
    if ( (*getProc)(i_fh,j,&num) == 0 ) return 0;
    if( j==1 ) 
      printf("%-12s %d", name, num);
    else 
      printf( ",%d",num);
  }
  printf("\n");
  return 1;
}

static int displayhiststr( int i_fh, int (*getProc)(int,int,char*,int), char* name, int nh )
{
  char str[64];
  int j;

  for( j=1; j<=nh; j++) {
    if ( (*getProc)(i_fh,j,str,64) == 0 ) return 0;
    if( j==1 )
      printf("%-12s %s",name,str);
    else
      printf( ",%s",str);
  }
  printf("\n");
  return 1;
}

static int replacestr(int i_fh, int (*setProc)(int,char*), char* name, char* value)
{
  if( *value == '\0' ) return 1;
  if( (*setProc)(i_fh, value) ) return 1;
  printf( "Error: Invalid %s string\n", name );
  errcnt++;
  return 0;
}

static int replacenum(int i_fh, int (*setProc)(int,UINT32), char* name, char* value)
{
  UINT32 num;
  char c;

  if( *value == '\0' ) return 1;
  if ( sscanf( value, "%d%c", &num, &c ) == 1 ) {
    if( (*setProc)(i_fh, num) ) return 1;
  }
  printf( "Error: Invalid %s value\n", name );
  errcnt++;
  return 0;
}

static int replacehiststr(int i_fh, int (*setProc)(int,int,char*), char* name, int nh, char* value)
{
  char str[64];
  int j;
  char *p;
  int errflag = 0;

  if( *value == '\0' ) return 1;
  p = value;
  for( j=1; j<=nh; j++) {
    str[0] = '\0';
    if( sscanf( p, "%[^,]", str ) ) {
      p += strlen(str);
    }
    if( *p == ',' ) p++;
    if( trimSpace( str ) > 0 ) {
      if( (*setProc)(i_fh, j, str) == 0) {
	printf( "Error: Invalid %s value for hist %d\n", name, j );
	errflag = 1;
      }
    }
  }
  if( errflag ) {
    errcnt++;
    return 0;
  }
  return 1;
}
      
static int replacehistnum(int i_fh, int (*setProc)(int,int,UINT32), char* name, int nh, char* value)
{
  char str[64];
  UINT32 num;
  int j;
  char *p;
  char c;
  int errflag = 0;

  if( *value == '\0' ) return 1;
  p = value;
  for( j=1; j<=nh; j++) {
    str[0] = '\0';
    if( sscanf( p, "%[^,]", str ) ) {
      p += strlen(str);
    }
    if( *p == ',' ) p++;
    if( trimSpace( str ) > 0 ) {
      strcat( str, ",." );
      if( sscanf( str, "%d,%c", &num, &c) == 2 ) {
        if( (*setProc)(i_fh, j, num) == 0) {
          printf( "Error: Invalid %s value for hist %d\n", name, j );
          errflag = 1;
        }
      }
      else {
        printf( "Error: Invalid %s value for hist %d\n", name, j );
        errflag = 1;
      } 
    }
  }
  if( errflag ) {
    errcnt++;
    return 0;
  }
  return 1;
}



/*
 * trimSpace:
 * Erase leading and trailing spaces.
 * Return final string length.
 */
static int trimSpace( char str[] ) 
{
  int j = 0;
  int k = 0;

  while( str[j] == ' ') j++ ;

  while( str[j] ) str[k++] = str[j++];

  str[k] = '\0';

  while( k ) {
    if( str[k-1] != ' ') break;
    str[--k] = '\0';
  }

  return k;
}

/*
 * matchcmd
 * Match two strings to see if command matches prototype.
 * Match is case-insensitive, and command may be abbreviated to
 * lesser of len parameter and length of prototype
 */

static int matchcmd(char* command, char* prototype, int len)
{
  int lp, lc, lm, i;

  lp = strlen(prototype);
  lc = strlen(command);
  if ( lc < lp && lc < len ) return( 0 );
  lm = (lp < lc ? lp : lc );
  /*
  Not:   return ( !strncasecmp(command, prototype, lm) );   due to portability issues.
  */
  for ( i=0; i<lm; i++ )
    {
      if ( tolower(command[i]) != tolower(prototype[i]) )
        {
          return ( 0 );
        }
    }
  return ( 1 );
}

