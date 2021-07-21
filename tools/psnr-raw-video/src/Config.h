
#pragma once


#include "Common.h"




class ConfigPars
{
public:
  enum VT { ORG = 0, REC, NUMV };

public:
  ConfigPars( const int argc, const char** argv );

public:
  const std::string&  progname        ()                const   { return m_progName; }
  const std::string&  filename        ( VT t )          const   { return m_fileName[t]; }
  unsigned            numComponents   ()                const   { return m_numComp; }
  unsigned            numSamples      (       int k )   const   { return ( k < 3 ? m_numSamples[k] : 0 ); }
  unsigned            bytesPerSample  ( VT t, int k )   const   { return ( k < 3 ? m_bytesPerSample[t][k] : 0 ); }
  unsigned            bitdepth        ( VT t, int k )   const   { return ( k < 3 ? m_bitdepth[t][k] : 0 ); }
  std::size_t         skipBytes       ( VT t, int n )   const   { return ( n > 0 ? m_skipBytes[t][1] : m_skipBytes[t][0] ); }
  std::size_t         numFrames       ()                const   { return m_numFrames; }
  double              bitrate         ()                const   { return m_bitrate; }
  const std::string&  prefixString    ()                const   { return m_prefixString; }
  SIMDMode            SIMDmode        ()                const   { return m_SIMDMode; }
  std::size_t         memAlign        ()                const   { return m_memAlignment; }
  std::size_t         memSizeRequired ( VT t )          const   { return m_memSizeRequired[t]; }

private:
  Message             usage             ()                            const;
  void                parseError        ( const Message&  msg )       const;
  static SIMDMode     getSIMD           ( const SIMDMode  maxSIMD );

public:
  std::string   m_progName;
  std::string   m_fileName        [NUMV];
  unsigned      m_numComp;
  unsigned      m_numSamples            [3];
  unsigned      m_bytesPerSample  [NUMV][3];
  unsigned      m_bitdepth        [NUMV][3];
  std::size_t   m_skipBytes       [NUMV][2];
  std::size_t   m_numFrames;
  double        m_bitrate;
  std::string   m_prefixString;
  SIMDMode      m_SIMDMode;
  std::size_t   m_memAlignment;
  std::size_t   m_memSizeRequired [NUMV];
};
