
#pragma once


#include "Common.h"
#include "Config.h"
#include "Frame.h"
#include "Distortion.h"


class PSNRCalc
{
public:
  PSNRCalc( const ConfigPars& cfg );

  void calcPSNR   ( std::ostream* pout, std::ostream* poutSum );

private:
  void outputAll  ( std::ostream* pout, std::size_t n );
  void outputSum  ( std::ostream* pout );

private:
  FrameMemory                 m_memory;
  Frame                       m_org;
  Frame                       m_rec;
  Distortion                  m_dist[3];
  const SIMDMode              m_simd;
  const std::string           m_prefix;
  const double                m_bitrate;
  const std::size_t           m_numFrames;
  const unsigned              m_numComp;
  const double                m_psnrOffset[3];
  double                      m_framePSNR [3];
  double                      m_avgPSNR   [3];
  double                      m_minPSNR;
  std::chrono::nanoseconds    m_snrTime;
  std::chrono::nanoseconds    m_totTime;
};

