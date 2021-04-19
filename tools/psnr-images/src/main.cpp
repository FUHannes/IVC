
#include <fstream>
#include <iostream>
#include <iomanip>
#include <string>
#include <cmath>

#include "image.h"



//______________________________________________________________________
//
//    C O M M A N D    L I N E    P A R A M E T E R S
//______________________________________________________________________

struct CmdPars
{
public:
  CmdPars( int argc, const char** argv );

  void                report  ( const std::string& err )  const;
  bool                valid   ()                          const  { return m_valid; }
  const std::string&  image1  ()                          const  { return m_filenames[0]; }
  const std::string&  image2  ()                          const  { return m_filenames[1]; }
  const std::string&  stream  ()                          const  { return m_filenames[2]; }

private:
  bool        m_valid;
  std::string m_progName;
  std::string m_filenames[3];
};

CmdPars::CmdPars( int argc, const char** argv ) 
  : m_valid     ( false )
  , m_progName  ( argv[0] )
{
  if( argc < 3 || argc > 4 )
  {
    report( argc == 1 ? "" : "Wrong number of parameters." );
    return;
  }
  for( int k = 1; k < argc; k++ )
  {
    m_filenames[k-1] = argv[k];
  }
  m_valid = true;
}

void CmdPars::report( const std::string& err ) const
{
  std::ostream& out = ( err.empty() ? std::cout : std::cerr );
  if( !err.empty() )
  {
    out << std::endl 
        << m_progName << ": ERROR: " << err << std::endl;
  }
  out << std::endl 
      << "Usage: " << m_progName << " (image1) (image2) [bitstream]" << std::endl
      << std::endl
      << "\timage1:     image file in PGM or PPM format" << std::endl
      << "\timage2:     image file (same format and size as image1)" << std::endl
      << "\tbitstream:  optional bitstream file (for bit rate output)" << std::endl
      << std::endl;
}



//______________________________________________________________________
//
//    M A I N
//______________________________________________________________________

int main( int argc, const char** argv )
{
  //---- read command line parameters ----
  const CmdPars pars( argc, argv );
  if( !pars.valid() )
    return 1;

  //---- open and check images ----
  Image image1( pars.image1() );
  Image image2( pars.image2() );
  if( !image1.valid() )
  {
    pars.report( "Cannot read image \"" + pars.image1() + "\"." );
    return 1;
  }
  if( !image2.valid() )
  {
    pars.report( "Cannot read image \"" + pars.image2() + "\"." );
    return 1;
  }
  if( !image1.samePars( image2) )
  {
    pars.report( "Images \"" + pars.image1() + "\" and \"" + pars.image2() 
               + "\" have different sizes and/or types." );
    return 1;
  }

  //---- get PSNR and bit rate ----
  std::vector<double> PSNRs   = image1.getPSNR( image2 );
  double              avgMSE  = 0.0;
  double              rateBpp = 0.0;
  for( double PSNR : PSNRs )
    avgMSE += ::pow( 10.0, -0.1*PSNR );
  avgMSE   /= double( PSNRs.size() );
  double avgPSNR = -10.0*::log10( avgMSE );
  if( !pars.stream().empty() )
  {
    std::ifstream bs( pars.stream() );
    if( !bs.is_open() || !bs.good() )
    {
      pars.report( "Cannot open bitstream file \"" + pars.stream() + "\"." );
      return 1;
    }
    bs.seekg( 0, std::ios::end );
    std::size_t   fsize = bs.tellg();
    rateBpp = double(fsize << 3) / double(image1.numSamples());
  }

  //---- output ----
  std::cout << std::fixed << std::setprecision(4);
  if( rateBpp > 0.0 )
  {
    std::cout << std::setw(8) << rateBpp << " bpp    ";
  }
  std::cout << std::setw(8) << avgPSNR << " dB";
  if( image1.type() == Image::Type::RGB )
  {
    std::cout << "   ( "
              << "R: " << std::setw(8) << PSNRs[0] << " dB   "
              << "G: " << std::setw(8) << PSNRs[1] << " dB   "
              << "B: " << std::setw(8) << PSNRs[2] << " dB )";
  }
  std::cout << std::endl;

  return 0;
}


