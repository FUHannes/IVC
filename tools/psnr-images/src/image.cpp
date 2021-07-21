
#include <cmath>
#include <fstream>

#include "image.h"


ColorComp::ColorComp()
  : m_width     ( 0 )
  , m_height    ( 0 )
  , m_numSamples( 0 )
  , m_stride    ( 0 )
  , m_maxVal    ( 0 )
  , m_data      ( nullptr )
{}

ColorComp::ColorComp( int width, int height, int maxVal )
  : m_width     ( width )
  , m_height    ( height )
  , m_numSamples( m_width * m_height )
  , m_stride    ( m_width )
  , m_maxVal    ( maxVal )
  , m_data      ( new int [ m_numSamples ] )
{
}

ColorComp::ColorComp( ColorComp&& c ) noexcept
  : m_width     ( c.m_width )
  , m_height    ( c.m_height )
  , m_numSamples( c.m_numSamples )
  , m_stride    ( c.m_stride )
  , m_maxVal    ( c.m_maxVal )
  , m_data      ( c.m_data )
{
  c.m_data = nullptr;
}

ColorComp::~ColorComp()
{
  delete [] m_data;
}

ColorComp& ColorComp::operator=( ColorComp&& c ) noexcept
{
  delete [] m_data;
  m_width       = c.m_width;
  m_height      = c.m_height;
  m_numSamples  = c.m_numSamples;
  m_stride      = c.m_stride;
  m_maxVal      = c.m_maxVal;
  m_data        = c.m_data;
  c.m_data      = nullptr;
  return *this;
}

bool ColorComp::samePars( const ColorComp& c ) const
{
  return ( ( m_width      == c.m_width      ) &&
           ( m_height     == c.m_height     ) &&
           ( m_numSamples == c.m_numSamples )    );
}

double ColorComp::getPSNR( const ColorComp& c ) const
{
  double psnr = 0.0;
  if( samePars( c ) )
  {
    int64_t     ssd  = 0;
    const int*  datA =   m_data;
    const int*  datB = c.m_data;
    for( int64_t y = 0; y < m_height; y++, datA += m_stride, datB += c.m_stride )
      for( int64_t x = 0; x < m_width; x++ )
      {
        int diff = datA[ x ] - datB[ x ];
        ssd     += int64_t( diff ) * diff;
      }
    double mse = double( ssd ) / double( m_numSamples );
    psnr = 10.0 * log10( double( m_maxVal * m_maxVal ) / mse );
  }
  return psnr;
}





Image::Image() 
  : m_type( Image::Type::INVALID )
{}

Image::Image( int width, int height, int maxVal, Image::Type type ) 
  : m_type( type )
{
  if( m_type == Image::Type::GRAY )
  {
    m_comp.push_back( ColorComp( width, height, maxVal ) );
    return;
  }
  if( m_type == Image::Type::RGB )
  {
    m_comp.push_back( ColorComp( width, height, maxVal ) );
    m_comp.push_back( ColorComp( width, height, maxVal ) );
    m_comp.push_back( ColorComp( width, height, maxVal ) );
    return;
  }
  m_type = Image::Type::INVALID;
}

Image::Image( const std::string& name ) 
  : m_type( Image::Type::INVALID )
{
  read( name );
}

Image::Image( Image&& im ) noexcept
  : m_type  ( im.m_type )
  , m_comp  ( std::move( im.m_comp ) )
{}

Image::~Image()
{}

Image& Image::operator=( Image&& im ) noexcept
{
  m_type = im.m_type;
  m_comp = std::move( im.m_comp );
  return *this;
}

int Image::read( const std::string& name )
{
  //--- clear image data ---
  m_type = Image::Type::INVALID;
  m_comp.clear();

  //--- open file ---
  std::ifstream is( name, std::ifstream::in | std::ifstream::binary );
  if( !is.is_open() || !is.good() )
    return 1;   // cannot open file

  //--- try to read image ---
  if( _readNetPBM( is ) == 0 )
    return 0;
  return 2;     // invalid data
}

int Image::_readNetPBM( std::istream& is )
{
  char magicNumber[2];
  is.read( magicNumber, 2 );
  if( !is.good() )
    return 1;         // read error
  if( magicNumber[0] != 'P' )
    return 1;         // unsupported format
  if( magicNumber[1] == '5' )
    return _readPGMDat( is );
  if( magicNumber[1] == '6' )
    return _readPPMDat( is );
  return 1;           // unsupported format
}

int Image::_readPGMDat( std::istream& is )
{
  assert( m_type == Image::Type::INVALID );
  assert( m_comp.size() == 0 );

  //----- read pgm header -----
  int width, height, maxVal;
  is >> width;
  is >> height;
  is >> maxVal;
  if( !is.good() )
    return 1;   // not enough data
  if( width <= 0 || height <= 0 || maxVal <= 0 || maxVal >= (1<<16) )
    return 1;   // invalid data in file
  if( is.get() != '\n' )
    return 1;   // invalid delimiter
  bool use2Bytes = ( maxVal > 255 );

  //----- create new image component -----
  ColorComp comp ( width, height, maxVal );

  //----- read image data -----
  int* dat = comp.data();
  if( use2Bytes )
    for( int y = 0; y < height; y++, dat += comp.stride() )
      for( int x = 0; x < width; x++ )
        dat[x] = ( is.get() << 8 ) + is.get();
  else
    for( int y = 0; y < height; y++, dat += comp.stride() )
      for( int x = 0; x < width; x++ )
        dat[x] = is.get();
  if( !is.good() )
    return 1;   // not enough data / read error

  //----- set image and return -----
  m_type = Image::Type::GRAY;
  m_comp.push_back( std::move( comp ) );
  return 0;
}

int Image::_readPPMDat( std::istream& is )
{
  assert( m_type == Image::Type::INVALID );
  assert( m_comp.size() == 0 );

  //----- read pgm header -----
  int width, height, maxVal;
  is >> width;
  is >> height;
  is >> maxVal;
  if( !is.good() )
    return 1;   // not enough data
  if( width <= 0 || height <= 0 || maxVal <= 0 || maxVal >= (1<<16) )
    return 1;   // invalid data in file
  if( is.get() != '\n' )
    return 1;   // invalid delimiter
  bool use2Bytes = ( maxVal > 255 );

  //----- create new image components -----
  ColorComp compR ( width, height, maxVal );
  ColorComp compG ( width, height, maxVal );
  ColorComp compB ( width, height, maxVal );

  //----- read image data -----
  int* datR = compR.data();
  int* datG = compG.data();
  int* datB = compB.data();
  if( use2Bytes )
    for( int y = 0; y < height; y++, datR += compR.stride(), datG += compG.stride(), datB += compB.stride() )
      for( int x = 0; x < width; x++ )
      {
        datR[x] = ( is.get() << 8 ) + is.get();
        datG[x] = ( is.get() << 8 ) + is.get();
        datB[x] = ( is.get() << 8 ) + is.get();
      }
  else
    for( int y = 0; y < height; y++, datR += compR.stride(), datG += compG.stride(), datB += compB.stride() )
      for( int x = 0; x < width; x++ )
      {
        datR[x] = is.get();
        datG[x] = is.get();
        datB[x] = is.get();
      }
  if( !is.good() )
    return 1;

  //----- set image and return -----
  m_type = Image::Type::RGB;
  m_comp.push_back( std::move( compR ) );
  m_comp.push_back( std::move( compG ) );
  m_comp.push_back( std::move( compB ) );
  return 0;
}

int Image::write( const std::string& name ) const
{
  if( m_type == Image::Type::GRAY )
  {
    if( _writePGM( name ) == 0 )
      return 0;
    return 1;
  }
  if( m_type == Image::Type::RGB )
  {
    if( _writePPM( name ) == 0 )
      return 0;
    return 1;
  }
  return 2; // invalid data
}

int Image::_writePGM( const std::string& name ) const
{
  assert( m_type == Image::Type::GRAY );
  assert( m_comp.size() == 1 );

  std::ofstream os( name, std::ofstream::out | std::ofstream::binary );
  if( !os.is_open() || !os.good() )
    return 1;

  const ColorComp& comp = m_comp[0];

  //----- write pgm header -----
  os << "P5" << std::endl
      << comp.width() << " " << comp.height() << std::endl
      << comp.maxValue() << std::endl;
  //----- write image data -----
  const int* dat = comp.data();
  if( comp.maxValue() > 255 )
    for( int y = 0; y < comp.height(); y++, dat += comp.stride() )
      for( int x = 0; x < comp.width(); x++ )
      {
        os.put( (unsigned char)( ( dat[x] >> 8 ) & 255 ) );
        os.put( (unsigned char)(   dat[x]        & 255 ) );
      }
  else
    for( int y = 0; y < comp.height(); y++, dat += comp.stride() )
      for( int x = 0; x < comp.width(); x++ )
      {
        os.put( (unsigned char)( dat[x] & 255 ) );
      }
  if( !os.good() )
    return 1;
  return 0;
}

int Image::_writePPM( const std::string& name ) const
{
  assert( m_type == Image::Type::RGB );
  assert( m_comp.size() == 3 );
  assert( m_comp[1].samePars( m_comp[0] ) );
  assert( m_comp[2].samePars( m_comp[0] ) );

  std::ofstream os( name, std::ofstream::out | std::ofstream::binary );
  if( !os.is_open() || !os.good() )
    return 1;

  const ColorComp& compR = m_comp[0];
  const ColorComp& compG = m_comp[1];
  const ColorComp& compB = m_comp[2];

  //----- write pgm header -----
  os << "P6" << std::endl
     << compR.width() << " " << compR.height() << std::endl
     << compR.maxValue() << std::endl;
  //----- write image data -----
  const int* datR = compR.data();
  const int* datG = compG.data();
  const int* datB = compB.data();
  if( compR.maxValue() > 255 )
    for( int y = 0; y < compR.height(); y++, datR += compR.stride(), datG += compG.stride(), datB += compB.stride() )
      for( int x = 0; x < compR.width(); x++ )
      {
        os.put( (unsigned char)( ( datR[x] >> 8 ) & 255 ) );
        os.put( (unsigned char)(   datR[x]        & 255 ) );
        os.put( (unsigned char)( ( datG[x] >> 8 ) & 255 ) );
        os.put( (unsigned char)(   datG[x]        & 255 ) );
        os.put( (unsigned char)( ( datB[x] >> 8 ) & 255 ) );
        os.put( (unsigned char)(   datB[x]        & 255 ) );
      }
  else
    for( int y = 0; y < compR.height(); y++, datR += compR.stride(), datG += compG.stride(), datB += compB.stride() )
      for( int x = 0; x < compR.width(); x++ )
      {
        os.put( (unsigned char)( datR[x] & 255 ) );
        os.put( (unsigned char)( datG[x] & 255 ) );
        os.put( (unsigned char)( datB[x] & 255 ) );
      }
  if( !os.good() )
    return 1;
  return 0;
}

std::vector<double> Image::getPSNR( const Image& im ) const
{
  assert( m_type != Image::Type::INVALID );
  std::vector<double> psnr;
  for( size_t k = 0; k < m_comp.size(); k++ )
    psnr.push_back( m_comp[k].getPSNR( im.m_comp[k] ) );
  return psnr;
}

bool Image::samePars( const Image& im )  const
{
  if( m_type != im.m_type )
    return false;
  if( m_comp.size() != im.m_comp.size() )
    return false;
  for( std::size_t k = 0; k < m_comp.size(); k++ )
    if( !m_comp[k].samePars( im.m_comp[k] ) )
      return false;
  return true;
}

