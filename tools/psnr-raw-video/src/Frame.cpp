

#include "Frame.h"


unsigned getAlignShift( const std::size_t alignment )
{
  switch( alignment )
  {
  case    1:  return 0;
  case    2:  return 1;
  case    4:  return 2;
  case    8:  return 3;
  case   16:  return 4;
  case   32:  return 5;
  case   64:  return 6;
  case  128:  return 7;
  default:
    THROW( "Alignment of " << alignment << " bytes is not supported" );
  }
}

FrameMemory::FrameMemory( const std::size_t alignment, const std::size_t totalMemory )
  : m_alignShift  ( getAlignShift( alignment ) )
  , m_alignOffset ( ( 1 << m_alignShift ) - 1 )
  , m_alignMask   ( ~m_alignOffset )
  , m_memStart    ( nullptr )
  , m_memEnd      ( nullptr )
  , m_next        ( nullptr )
{
  std::size_t allocSize = totalMemory + alignment;  // extra for first alignment
  uint8_t*    memory    = nullptr;
  try
  {
    memory = new uint8_t [ allocSize ];
  }
  catch( ... )
  {
    memory = nullptr;
  }
  ERROR( memory == nullptr, "Memory allocation failed" );

  std::uintptr_t  memAddr = reinterpret_cast<std::uintptr_t>( memory );
  std::uintptr_t  mask    = std::uintptr_t( m_alignOffset );
  std::uintptr_t  aligned = ( memAddr + mask ) & ~mask;
  std::size_t     offset  = std::size_t( aligned - memAddr );

  const_cast<uint8_t*&>( m_memStart ) = memory;
  const_cast<uint8_t*&>( m_memEnd   ) = m_memStart + allocSize;
  m_next                              = m_memStart + offset;
}

FrameMemory::~FrameMemory()
{
  delete [] m_memStart;
}

void* FrameMemory::getMem( const std::size_t memSize )
{
  std::size_t alignedSize = ( memSize + m_alignOffset ) & m_alignMask;
  if( alignedSize > std::size_t( m_memEnd - m_next ) )
  {
    return nullptr;
  }
  uint8_t*  chunk = m_next;
  m_next         += alignedSize;
  return static_cast<void*>( chunk );
}





ColorComponent::ColorComponent( const ConfigPars& cfg, const ConfigPars::VT vtype, const int comp, FrameMemory& mem )
  : m_bitdepth      ( cfg.bitdepth      ( vtype, comp ) )
  , m_bytesPerSample( cfg.bytesPerSample( vtype, comp ) )
  , m_numSamples    ( cfg.numSamples    (        comp ) )
  , m_numBytes      ( m_numSamples * m_bytesPerSample )
  , m_data          ( mem.getMem( m_numBytes ) )
{
  ERROR( !m_data, "Insufficient memory for color component " << comp );
}

void ColorComponent::read( std::istream& istr, const std::string& filename )
{
  istr.read( static_cast<char*>( m_data ), std::streamsize(m_numBytes) );
  ERROR( !istr, "Failed reading " << m_numBytes << " bytes from data stream \"" << filename << "\"" );
}



Frame::Frame( const ConfigPars& cfg, const ConfigPars::VT vtype, FrameMemory& mem )
  : m_filename  ( cfg.filename( vtype ) )
  , m_numComp   ( cfg.numComponents() )
  , m_comp      { {cfg,vtype,0,mem}, {cfg,vtype,1,mem}, {cfg,vtype,2,mem} }
  , m_file      ()
  , m_skipBytes { cfg.skipBytes(vtype,0), cfg.skipBytes(vtype,1) }
  , m_skipNext  ( 0 )
{
}

Frame::~Frame()
{
  if( m_file.is_open() )
  {
    m_file.close();
  }
}

void Frame::open()
{
  close();
  m_file.open( m_filename, std::ios::in | std::ios::binary );
  ERROR( !m_file.is_open(), "Cannot open video file \"" << m_filename << "\"" );
  m_skipNext = m_skipBytes[0];
}

void Frame::readNext()
{
  if( m_skipNext )
  {
    m_file.ignore( m_skipNext );
    ERROR( !m_file, "Error while skipping " << m_skipNext << " bytes from file \"" << m_filename << "\"" );
  }
  for( unsigned c = 0; c < m_numComp; c++ )
  {
    m_comp[c].read( m_file, m_filename );
  }
  m_skipNext = m_skipBytes[1];
}

void Frame::close()
{
  if( m_file.is_open() )
  {
    m_file.close();
  }
}





