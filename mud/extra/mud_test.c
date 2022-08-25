/*
 *  mud_test.c
 */

#include "mud.h"

int
main( void )
{
    FILE* fin;
    FILE* fout;
    MUD_SEC_GRP* pMUD_data = NULL;
    MUD_SEC_GEN_RUN_DESC* pMUD_desc = NULL;
    MUD_SEC_GEN_HIST_HDR* pMUD_hist = NULL;
    UINT32 run_fmt_ID;
    char* filename = "006663.msr";

    /*
     *  Read an MUD format file into a linked list
     */
    fin = MUD_openInput( filename );
    if( fin == NULL ) {
	fprintf( stderr, "failed to open file \"%s\"\n", filename );
        exit( 0 );
    }

    pMUD_data = MUD_readFile( fin );
    fclose( fin );
    if (pMUD_data == NULL) {
      fprintf( stderr, "failed to read file \"%s\"\n", filename );
      exit( 0 );
    }
 
    run_fmt_ID = MUD_instanceID( pMUD_data );
    if (run_fmt_ID == MUD_FMT_TRI_TD_ID) 
      printf( "TRIUMF TD-muSR data\n" ); 
    else if (run_fmt_ID == MUD_FMT_TRI_TI_ID) 
      printf( "TRIUMF I-muSR data\n" ) ;

    /*
     *  Access the header for the third ("3") histogram, in the TD histogram 
     *  group, in the overall data group.
     */
    pMUD_hist = MUD_search( pMUD_data,
                            MUD_SEC_GRP_ID, run_fmt_ID,
                            MUD_SEC_GRP_ID, MUD_GRP_TRI_TD_HIST_ID,
                            MUD_SEC_GEN_HIST_HDR_ID, 3, 
                            0 );
    /*
     *  Alternative but equivalent search starts at the members of
     *  the overall data group.
     */
    pMUD_hist = MUD_search( pMUD_data->pMem,
                            MUD_SEC_GRP_ID, MUD_GRP_TRI_TD_HIST_ID,
                            MUD_SEC_GEN_HIST_HDR_ID, 3, 
                            0 );

    if (pMUD_hist == NULL) {
      fprintf( stderr, "could not find a histogram 3\n" );
      exit( 0 );
    }
    printf( "Number of bins in histogram 3: %d\n", pMUD_hist->nBins );

    /*
     *  Add a second ("2") but blank run description section to the list (silly nonsense)
     */
    pMUD_desc = (MUD_SEC_GEN_RUN_DESC*)MUD_new( MUD_SEC_GEN_RUN_DESC_ID, 2 );
    MUD_addToGroup( pMUD_data, pMUD_desc );

    /*
     :
     :  Do something not silly here
     :
     */

    /*
     *  Write MUD format file over the same filename (replace original)
     */
    fout = MUD_openOutput( filename );
    if( fout == NULL ) exit( 0 );

    MUD_writeFile( fout, pMUD_data );

    fclose( fout );

    /*
     *  Free the linked list
     */
    MUD_free( pMUD_data );
}

/*
 *  end mud_test.c
 */
