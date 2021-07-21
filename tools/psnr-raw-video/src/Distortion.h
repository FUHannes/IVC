
#pragma once


#include "Common.h"
#include "Frame.h"


class Distortion
{

public:
  Distortion( const ColorComponent& c1, const ColorComponent& c2, const SIMDMode simd );
  
  uint64_t  getSSD() const { return (this->*(this->m_getSSD))(); }

private:
  uint64_t  getSSD__8bit__8bit_cstd ()  const;
  uint64_t  getSSD_16bit__8bit_cstd ()  const;
  uint64_t  getSSD_16bit_16bit_cstd ()  const;

  uint64_t  getSSD__8bit__8bit_sse41()  const;
  uint64_t  getSSD_16bit__8bit_sse41()  const;
  uint64_t  getSSD_16bit_16bit_sse41()  const;

  uint64_t  getSSD__8bit__8bit_avx2 ()  const;
  uint64_t  getSSD_16bit__8bit_avx2 ()  const;
  uint64_t  getSSD_16bit_16bit_avx2 ()  const;

private:
  typedef             uint64_t (Distortion::*DFunc)() const;
  static const DFunc  sm_getSSD__8bit__8bit[SIMD_NUM_VALUES];
  static const DFunc  sm_getSSD_16bit__8bit[SIMD_NUM_VALUES];
  static const DFunc  sm_getSSD_16bit_16bit[SIMD_NUM_VALUES];

private:
  const unsigned  m_numSamples;
  const unsigned  m_shift2;
  const void*     m_data1;
  const void*     m_data2;
  const DFunc     m_getSSD;
};

