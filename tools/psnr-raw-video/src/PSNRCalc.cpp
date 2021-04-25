
#include "PSNRCalc.h"


PSNRCalc::PSNRCalc( const ConfigPars& cfg )
  : m_memory      ( cfg.memAlign(), cfg.memSizeRequired(ConfigPars::ORG) + cfg.memSizeRequired(ConfigPars::REC) )
  , m_org         ( cfg, ConfigPars::ORG, m_memory )
  , m_rec         ( cfg, ConfigPars::REC, m_memory )
  , m_dist        { {m_org.getComp(0),m_rec.getComp(0),cfg.SIMDmode()}, {m_org.getComp(1),m_rec.getComp(1),cfg.SIMDmode()}, {m_org.getComp(2),m_rec.getComp(2),cfg.SIMDmode()} }
  , m_simd        ( cfg.SIMDmode() )
  , m_prefix      ( cfg.prefixString() )
  , m_bitrate     ( cfg.bitrate() )
  , m_numFrames   ( cfg.numFrames() )
  , m_numComp     ( cfg.numComponents() )
  , m_psnrOffset  { 0.0, 0.0, 0.0 }
  , m_framePSNR   { 0.0, 0.0, 0.0 }
  , m_avgPSNR     { 0.0, 0.0, 0.0 }
  , m_minPSNR     ( 0.0 )
  , m_snrTime     ( 0 )
  , m_totTime     ( 0 )
{
  uint64_t maxV[3] = 
  { 
    uint64_t(255)<<(std::max<unsigned>(cfg.bitdepth(ConfigPars::ORG,0),cfg.bitdepth(ConfigPars::REC,0))-8),
    uint64_t(255)<<(std::max<unsigned>(cfg.bitdepth(ConfigPars::ORG,1),cfg.bitdepth(ConfigPars::REC,1))-8),
    uint64_t(255)<<(std::max<unsigned>(cfg.bitdepth(ConfigPars::ORG,2),cfg.bitdepth(ConfigPars::REC,2))-8)
  };
  const_cast<double&>(m_psnrOffset[0]) = 10.0 * log10( double(maxV[0]*maxV[0]*uint64_t(cfg.numSamples(0))) );
  const_cast<double&>(m_psnrOffset[1]) = 10.0 * log10( double(maxV[1]*maxV[1]*uint64_t(cfg.numSamples(1))) );
  const_cast<double&>(m_psnrOffset[2]) = 10.0 * log10( double(maxV[2]*maxV[2]*uint64_t(cfg.numSamples(2))) );
}

void PSNRCalc::calcPSNR( std::ostream* poutAll, std::ostream* poutSum )
{
  auto          totTimeStart  = std::chrono::high_resolution_clock::now();
  auto          snrTimeSum    = totTimeStart - totTimeStart;
  const double  avgScale      = 1.0 / double( m_numFrames );
  m_avgPSNR[0]  = 0.0;
  m_avgPSNR[1]  = 0.0;
  m_avgPSNR[2]  = 0.0;
  m_minPSNR     = std::numeric_limits<double>::infinity();
  m_org.open();
  m_rec.open();
  for( std::size_t n = 0; n < m_numFrames; n++ )
  {
    m_org.readNext();
    m_rec.readNext();
    auto snrTimeStart = std::chrono::high_resolution_clock::now();
    for( unsigned c = 0; c < m_numComp; c++ )
    {
      m_framePSNR[c]  = m_psnrOffset[c] - 10.0 * log10( double( m_dist[c].getSSD() ) );
      m_avgPSNR  [c] += m_framePSNR [c];
      m_minPSNR       = std::min<double>( m_minPSNR, m_framePSNR[c] );
    }
    snrTimeSum += ( std::chrono::high_resolution_clock::now() - snrTimeStart );
    outputAll( poutAll, n );
  }
  m_org.close();
  m_rec.close();
  m_avgPSNR[0] *= avgScale;
  m_avgPSNR[1] *= avgScale;
  m_avgPSNR[2] *= avgScale;
  
  auto totTime  = std::chrono::high_resolution_clock::now() - totTimeStart;
  m_snrTime     = std::chrono::duration_cast<std::chrono::nanoseconds>( snrTimeSum );
  m_totTime     = std::chrono::duration_cast<std::chrono::nanoseconds>( totTime    );

  if( poutAll )
  {
    *poutAll << std::endl;
  }
  outputSum( poutAll );
  outputSum( poutSum );
}

void PSNRCalc::outputAll( std::ostream* pout, std::size_t n )
{
  if( pout )
  {
    *pout << std::setw(6) << n << ":";
    for( unsigned c = 0; c < m_numComp; c++ )
    {
      *pout << std::setw(10) << std::fixed << std::setprecision(4) << m_framePSNR[c];
    }
    *pout << std::endl;
  }
}

void PSNRCalc::outputSum( std::ostream* pout )
{
  if( pout )
  {
    if( !m_prefix.empty() )
    {
      *pout << m_prefix << ":   ";
    }
    if( m_bitrate > 0.0 )
    {
      *pout << std::fixed << std::setprecision(4) << m_bitrate;
    }
    for( unsigned c = 0; c < m_numComp; c++ )
    {
      *pout << std::setw(10) << std::fixed << std::setprecision(4) << m_avgPSNR[c];
    }
    static const std::string    simdStr  [SIMD_NUM_VALUES] = { "scalar", "SSE4.1", "AVX2" };
    *pout << "   ";
    *pout << ( m_minPSNR == std::numeric_limits<double>::infinity() ? "[ same ]" : "[ diff ]" );
    *pout << "[ " << m_numFrames << " frames ]";
    *pout << "[ " << std::chrono::duration_cast<std::chrono::milliseconds>(m_snrTime).count() << " ms ]";
    *pout << "[ " << std::chrono::duration_cast<std::chrono::milliseconds>(m_totTime).count() << " ms ]";
    *pout << "[ " << simdStr[m_simd] << " ]";
    *pout << std::endl;
  }
}

