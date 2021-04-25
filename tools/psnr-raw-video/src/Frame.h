
#pragma once



#include "Common.h"
#include "Config.h"



class FrameMemory
{
public:
  FrameMemory ( const std::size_t alignment,      // alignment in bytes
                const std::size_t totalMemory );  // maximum total memory required including alignments (in bytes)
  ~FrameMemory();

  void* getMem( const std::size_t memSize );

private:
  const unsigned        m_alignShift;
  const std::size_t     m_alignOffset;
  const std::size_t     m_alignMask;
        uint8_t* const  m_memStart;
        uint8_t* const  m_memEnd;
        uint8_t*        m_next;
};



class ColorComponent
{
public:
  ColorComponent( const ConfigPars& cfg, const ConfigPars::VT vtype, const int comp, FrameMemory& mem );

public:
  void        read          ( std::istream& istr, const std::string& filename );
  unsigned    bitdepth      ()    const   { return m_bitdepth; }
  unsigned    bytesPerSample()    const   { return m_bytesPerSample; }
  unsigned    numSamples    ()    const   { return m_numSamples; }
  const void* data          ()    const   { return m_data; }

private:
  const unsigned    m_bitdepth;
  const unsigned    m_bytesPerSample;
  const unsigned    m_numSamples;
  const std::size_t m_numBytes;
  void* const       m_data;
};



class Frame
{
public:
  Frame ( const ConfigPars& cfg, const ConfigPars::VT vtype, FrameMemory& mem );
  ~Frame();

  void  open      ();
  void  readNext  ();
  void  close     ();

  unsigned              numComp()         const { return m_numComp; }
  const ColorComponent& getComp( int k )  const { return m_comp[k]; }

private:
  const std::string   m_filename;
  const unsigned      m_numComp;
  ColorComponent      m_comp[3];
  std::ifstream       m_file;
  const std::size_t   m_skipBytes[2];
  std::size_t         m_skipNext;
};



