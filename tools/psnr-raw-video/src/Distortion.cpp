

#include "Distortion.h"


const Distortion::DFunc Distortion::sm_getSSD__8bit__8bit[SIMD_NUM_VALUES] = 
{
  &Distortion::getSSD__8bit__8bit_cstd,
  &Distortion::getSSD__8bit__8bit_sse41,
  &Distortion::getSSD__8bit__8bit_avx2
};
const Distortion::DFunc Distortion::sm_getSSD_16bit__8bit[SIMD_NUM_VALUES] = 
{
  &Distortion::getSSD_16bit__8bit_cstd,
  &Distortion::getSSD_16bit__8bit_sse41,
  &Distortion::getSSD_16bit__8bit_avx2
};
const Distortion::DFunc Distortion::sm_getSSD_16bit_16bit[SIMD_NUM_VALUES] = 
{
  &Distortion::getSSD_16bit_16bit_cstd,
  &Distortion::getSSD_16bit_16bit_sse41,
  &Distortion::getSSD_16bit_16bit_avx2
};





Distortion::Distortion( const ColorComponent& c1, const ColorComponent& c2, const SIMDMode simd )
  : m_numSamples( c1.numSamples() )
  , m_shift2    ( 0 )
  , m_data1     ( nullptr )
  , m_data2     ( nullptr )
  , m_getSSD    ( nullptr )
{
  ERROR( m_numSamples != c2.numSamples(), "Incompatible numer of samples" );

  const bool            secondFirst = ( c2.bitdepth() > c1.bitdepth() );
  const ColorComponent& comp1       = ( secondFirst ? c2 : c1 );
  const ColorComponent& comp2       = ( secondFirst ? c1 : c2 );
  const_cast<unsigned&>(m_shift2)   = comp1.bitdepth() - comp2.bitdepth();
  m_data1                           = comp1.data();
  m_data2                           = comp2.data();

  if     ( comp1.bytesPerSample() == 1 && comp2.bytesPerSample() == 1 )   const_cast<DFunc&>(m_getSSD) = sm_getSSD__8bit__8bit[simd];
  else if( comp1.bytesPerSample() == 2 && comp2.bytesPerSample() == 1 )   const_cast<DFunc&>(m_getSSD) = sm_getSSD_16bit__8bit[simd];
  else if( comp1.bytesPerSample() == 2 && comp2.bytesPerSample() == 2 )   const_cast<DFunc&>(m_getSSD) = sm_getSSD_16bit_16bit[simd];
  else
  {
    THROW( "Unsupport combination of bytes per sample (" << comp1.bytesPerSample() << "," << comp2.bytesPerSample() << ")" );
  }
}





uint64_t Distortion::getSSD__8bit__8bit_cstd() const
{
  const uint8_t*  data1 = reinterpret_cast<const uint8_t*>( m_data1 );
  const uint8_t*  data2 = reinterpret_cast<const uint8_t*>( m_data2 );
  uint64_t        dist  = 0;
  for( unsigned k = 0; k < m_numSamples; k++ )
  {
    int32_t diff = int32_t( data1[k] ) - int32_t( data2[k] );
    dist        += uint64_t( diff * diff );
  }
  return dist;
}

uint64_t Distortion::getSSD_16bit__8bit_cstd() const
{
  const uint16_t* data1 = reinterpret_cast<const uint16_t*>( m_data1 );
  const uint8_t*  data2 = reinterpret_cast<const uint8_t* >( m_data2 );
  uint64_t        dist  = 0;
  for( unsigned k = 0; k < m_numSamples; k++ )
  {
    int32_t diff = int32_t( data1[k] ) - ( int32_t( data2[k] ) << m_shift2 );
    dist        += uint64_t( diff * diff );
  }
  return dist;
}

uint64_t Distortion::getSSD_16bit_16bit_cstd() const
{
  const uint16_t* data1 = reinterpret_cast<const uint16_t*>( m_data1 );
  const uint16_t* data2 = reinterpret_cast<const uint16_t*>( m_data2 );
  uint64_t        dist  = 0;
  for( unsigned k = 0; k < m_numSamples; k++ )
  {
    int32_t diff = int32_t( data1[k] ) - ( int32_t( data2[k] ) << m_shift2 );
    dist        += uint64_t( diff * diff );
  }
  return dist;
}





uint64_t Distortion::getSSD__8bit__8bit_sse41() const
{
#if ENABLE_SIMD < 1
  return getSSD__8bit__8bit_cstd();
#else
  const __m128i*  pOrg  = reinterpret_cast<const __m128i*>( m_data2 );
  const __m128i*  pRec  = reinterpret_cast<const __m128i*>( m_data1 );
  const unsigned  numV  = m_numSamples >> 4;
  uint64_t        dist  = 0;
  for( unsigned v = 0; v < numV; v++ )
  {
    __m128i v16x8_Org   = _mm_load_si128    ( pOrg++     );
    __m128i v16x8_Rec   = _mm_load_si128    ( pRec++     );
    __m128i v8x16_Org_0 = _mm_cvtepu8_epi16 ( v16x8_Org  ); 
    __m128i v8x16_Rec_0 = _mm_cvtepu8_epi16 ( v16x8_Rec  );
    __m128i v8x16_Dif_0 = _mm_sub_epi16     ( v8x16_Org_0, v8x16_Rec_0 );
    __m128i v16x8_Org_  = _mm_shuffle_epi32 ( v16x8_Org  , 0xee        );
    __m128i v16x8_Rec_  = _mm_shuffle_epi32 ( v16x8_Rec  , 0xee        );
    __m128i v8x16_Org_1 = _mm_cvtepu8_epi16 ( v16x8_Org_ ); 
    __m128i v8x16_Rec_1 = _mm_cvtepu8_epi16 ( v16x8_Rec_ );
    __m128i v8x16_Dif_1 = _mm_sub_epi16     ( v8x16_Org_1, v8x16_Rec_1 );
    __m128i v4x32_Dx8_0 = _mm_madd_epi16    ( v8x16_Dif_0, v8x16_Dif_0 );
    __m128i v4x32_Dx8_1 = _mm_madd_epi16    ( v8x16_Dif_1, v8x16_Dif_1 );
    __m128i v4x32_Dx4   = _mm_hadd_epi32    ( v4x32_Dx8_0, v4x32_Dx8_1 );
    __m128i v4x32_Dx2   = _mm_hadd_epi32    ( v4x32_Dx4,   v4x32_Dx4   );
    __m128i v4x32_Dx1   = _mm_hadd_epi32    ( v4x32_Dx2,   v4x32_Dx2   );
    dist               += _mm_extract_epi32 ( v4x32_Dx1,   0 );
  }
  const uint8_t*  data1 = reinterpret_cast<const uint8_t*>( m_data1 );
  const uint8_t*  data2 = reinterpret_cast<const uint8_t*>( m_data2 );
  for( unsigned k = (numV<<4); k < m_numSamples; k++ )
  {
    int32_t diff = int32_t( data1[k] ) - int32_t( data2[k] );
    dist        += uint64_t( diff * diff );
  }
  return dist;
#endif
}

uint64_t Distortion::getSSD_16bit__8bit_sse41() const
{
#if ENABLE_SIMD < 1
  return getSSD_16bit__8bit_cstd();
#else
  const __m128i*  pOrg  = reinterpret_cast<const __m128i*>( m_data2 );
  const __m128i*  pRec  = reinterpret_cast<const __m128i*>( m_data1 );
  const unsigned  numV  = m_numSamples >> 4;
  uint64_t        dist  = 0;
  if( m_shift2 )
  {
    __m128i   shift_cnt = _mm_set_epi32     ( 0, 0, 0, (int)m_shift2 );
    for( unsigned v = 0; v < numV; v++ )
    {
      __m128i v16x8_Tmp_0 = _mm_load_si128    ( pOrg++                   );
      __m128i v8x16_Tmp_0 = _mm_cvtepu8_epi16 ( v16x8_Tmp_0              ); 
      __m128i v8x16_Org_0 = _mm_sll_epi16     ( v8x16_Tmp_0, shift_cnt   );
      __m128i v8x16_Rec_0 = _mm_load_si128    ( pRec++                   );
      __m128i v8x16_Dif_0 = _mm_sub_epi16     ( v8x16_Org_0, v8x16_Rec_0 );
      __m128i v4x32_Dx4_0 = _mm_madd_epi16    ( v8x16_Dif_0, v8x16_Dif_0 );
      __m128i v4x32_Dx2_0 = _mm_hadd_epi32    ( v4x32_Dx4_0, v4x32_Dx4_0 );
      __m128i v4x32_Dx1_0 = _mm_hadd_epi32    ( v4x32_Dx2_0, v4x32_Dx2_0 );
      dist               += _mm_extract_epi32 ( v4x32_Dx1_0, 0 );

      __m128i v16x8_Tmp_1 = _mm_shuffle_epi32 ( v16x8_Tmp_0, 0xee        );
      __m128i v8x16_Tmp_1 = _mm_cvtepu8_epi16 ( v16x8_Tmp_1              ); 
      __m128i v8x16_Org_1 = _mm_sll_epi16     ( v8x16_Tmp_1, shift_cnt   );
      __m128i v8x16_Rec_1 = _mm_load_si128    ( pRec++                   );
      __m128i v8x16_Dif_1 = _mm_sub_epi16     ( v8x16_Org_1, v8x16_Rec_1 );
      __m128i v4x32_Dx4_1 = _mm_madd_epi16    ( v8x16_Dif_1, v8x16_Dif_1 );
      __m128i v4x32_Dx2_1 = _mm_hadd_epi32    ( v4x32_Dx4_1, v4x32_Dx4_1 );
      __m128i v4x32_Dx1_1 = _mm_hadd_epi32    ( v4x32_Dx2_1, v4x32_Dx2_1 );
      dist               += _mm_extract_epi32 ( v4x32_Dx1_1, 0 );
    }
  }
  else
  {
    for( unsigned v = 0; v < numV; v++ )
    {
      __m128i v16x8_Org_0 = _mm_load_si128    ( pOrg++                   );
      __m128i v8x16_Org_0 = _mm_cvtepu8_epi16 ( v16x8_Org_0              ); 
      __m128i v8x16_Rec_0 = _mm_load_si128    ( pRec++                   );
      __m128i v8x16_Dif_0 = _mm_sub_epi16     ( v8x16_Org_0, v8x16_Rec_0 );
      __m128i v4x32_Dx4_0 = _mm_madd_epi16    ( v8x16_Dif_0, v8x16_Dif_0 );
      __m128i v4x32_Dx2_0 = _mm_hadd_epi32    ( v4x32_Dx4_0, v4x32_Dx4_0 );
      __m128i v4x32_Dx1_0 = _mm_hadd_epi32    ( v4x32_Dx2_0, v4x32_Dx2_0 );
      dist               += _mm_extract_epi32 ( v4x32_Dx1_0, 0 );

      __m128i v16x8_Org_1 = _mm_shuffle_epi32 ( v16x8_Org_0, 0xee        );
      __m128i v8x16_Org_1 = _mm_cvtepu8_epi16 ( v16x8_Org_1              ); 
      __m128i v8x16_Rec_1 = _mm_load_si128    ( pRec++                   );
      __m128i v8x16_Dif_1 = _mm_sub_epi16     ( v8x16_Org_1, v8x16_Rec_1 );
      __m128i v4x32_Dx4_1 = _mm_madd_epi16    ( v8x16_Dif_1, v8x16_Dif_1 );
      __m128i v4x32_Dx2_1 = _mm_hadd_epi32    ( v4x32_Dx4_1, v4x32_Dx4_1 );
      __m128i v4x32_Dx1_1 = _mm_hadd_epi32    ( v4x32_Dx2_1, v4x32_Dx2_1 );
      dist               += _mm_extract_epi32 ( v4x32_Dx1_1, 0 );
    }
  }
  const uint8_t*  data1 = reinterpret_cast<const uint8_t*>( m_data1 );
  const uint8_t*  data2 = reinterpret_cast<const uint8_t*>( m_data2 );
  for( unsigned k = (numV<<4); k < m_numSamples; k++ )
  {
    int32_t diff = int32_t( data1[k] ) - int32_t( data2[k] );
    dist        += uint64_t( diff * diff );
  }
  return dist;
#endif
}

uint64_t Distortion::getSSD_16bit_16bit_sse41() const
{
#if ENABLE_SIMD < 1
  return getSSD_16bit_16bit_cstd();
#else
  const __m128i*  pOrg  = reinterpret_cast<const __m128i*>( m_data2 );
  const __m128i*  pRec  = reinterpret_cast<const __m128i*>( m_data1 );
  const unsigned  numV  = m_numSamples >> 3;
  uint64_t        dist  = 0;
  if( m_shift2 )
  {
    __m128i   shift_cnt = _mm_set_epi32     ( 0, 0, 0, (int)m_shift2 );
    for( unsigned v = 0; v < numV; v++ )
    {
      __m128i v8x16_Tmp = _mm_load_si128    ( pOrg++ );
      __m128i v8x16_Org = _mm_sll_epi16     ( v8x16_Tmp, shift_cnt );
      __m128i v8x16_Rec = _mm_load_si128    ( pRec++ );
      __m128i v8x16_Dif = _mm_sub_epi16     ( v8x16_Org, v8x16_Rec );
      __m128i v4x32_Dx4 = _mm_madd_epi16    ( v8x16_Dif, v8x16_Dif );
      __m128i v4x32_Dx2 = _mm_hadd_epi32    ( v4x32_Dx4, v4x32_Dx4 );
      __m128i v4x32_Dx1 = _mm_hadd_epi32    ( v4x32_Dx2, v4x32_Dx2 );
      dist             += _mm_extract_epi32 ( v4x32_Dx1, 0 );
    }
  }
  else
  {
    for( unsigned v = 0; v < numV; v++ )
    {
      __m128i v8x16_Org = _mm_load_si128    ( pOrg++ );
      __m128i v8x16_Rec = _mm_load_si128    ( pRec++ );
      __m128i v8x16_Dif = _mm_sub_epi16     ( v8x16_Org, v8x16_Rec );
      __m128i v4x32_Dx4 = _mm_madd_epi16    ( v8x16_Dif, v8x16_Dif );
      __m128i v4x32_Dx2 = _mm_hadd_epi32    ( v4x32_Dx4, v4x32_Dx4 );
      __m128i v4x32_Dx1 = _mm_hadd_epi32    ( v4x32_Dx2, v4x32_Dx2 );
      dist             += _mm_extract_epi32 ( v4x32_Dx1, 0 );
    }
  }
  const uint8_t*  data1 = reinterpret_cast<const uint8_t*>( m_data1 );
  const uint8_t*  data2 = reinterpret_cast<const uint8_t*>( m_data2 );
  for( unsigned k = (numV<<3); k < m_numSamples; k++ )
  {
    int32_t diff = int32_t( data1[k] ) - int32_t( data2[k] );
    dist        += uint64_t( diff * diff );
  }
  return dist;
#endif
}



uint64_t Distortion::getSSD__8bit__8bit_avx2() const
{
#if ENABLE_SIMD < 2
  return getSSD__8bit__8bit_cstd();
#else
  const __m128i*  pOrg  = reinterpret_cast<const __m128i*>( m_data2 );
  const __m128i*  pRec  = reinterpret_cast<const __m128i*>( m_data1 );
  const unsigned  numV  = m_numSamples >> 5;
  uint64_t        dist  = 0;
  for( unsigned v = 0; v < numV; v++ )
  {
    __m256i v16x16_Dif_1  = _mm256_sub_epi16          ( _mm256_cvtepu8_epi16( _mm_load_si128( pOrg++ ) ), _mm256_cvtepu8_epi16( _mm_load_si128( pRec++ ) ) );
    __m256i v16x16_Dif_2  = _mm256_sub_epi16          ( _mm256_cvtepu8_epi16( _mm_load_si128( pOrg++ ) ), _mm256_cvtepu8_epi16( _mm_load_si128( pRec++ ) ) );
    __m256i v8x32_Dx8_1   = _mm256_madd_epi16         ( v16x16_Dif_1,   v16x16_Dif_1  );
    __m256i v8x32_Dx8_2   = _mm256_madd_epi16         ( v16x16_Dif_2,   v16x16_Dif_2  );
    __m256i v8x32_Dx8_a   = _mm256_hadd_epi32         ( v8x32_Dx8_1,    v8x32_Dx8_2   );
    __m256i v8x32_Dx8_b   = _mm256_permute2x128_si256 ( v8x32_Dx8_a,    v8x32_Dx8_a,  1 );
    __m256i v8x32_Dx4     = _mm256_hadd_epi32         ( v8x32_Dx8_a,    v8x32_Dx8_b   );
    __m256i v8x32_Dx2     = _mm256_hadd_epi32         ( v8x32_Dx4,      v8x32_Dx4     );
    __m256i v8x32_Dx1     = _mm256_hadd_epi32         ( v8x32_Dx2,      v8x32_Dx2     );
    dist                 += _mm_extract_epi32         ( _mm256_extracti128_si256( v8x32_Dx1, 0 ), 0 );
  }
  const uint8_t*  data1 = reinterpret_cast<const uint8_t*>( m_data1 );
  const uint8_t*  data2 = reinterpret_cast<const uint8_t*>( m_data2 );
  for( unsigned k = (numV<<5); k < m_numSamples; k++ )
  {
    int32_t diff = int32_t( data1[k] ) - int32_t( data2[k] );
    dist        += uint64_t( diff * diff );
  }
  return dist;
#endif
}

uint64_t Distortion::getSSD_16bit__8bit_avx2() const
{
#if ENABLE_SIMD < 2
  return getSSD_16bit__8bit_cstd();
#else
  const __m128i*  pOrg  = reinterpret_cast<const __m128i*>( m_data2 );
  const __m256i*  pRec  = reinterpret_cast<const __m256i*>( m_data1 );
  const unsigned  numV  = m_numSamples >> 5;
  uint64_t        dist  = 0;
  if( m_shift2 )
  {
    __m128i   shift_cnt     = _mm_set_epi32( 0, 0, 0, (int)m_shift2 );
    for( unsigned v = 0; v < numV; v++ )
    {
      __m256i v16x16_Dif_1  = _mm256_sub_epi16          ( _mm256_sll_epi16( _mm256_cvtepu8_epi16( _mm_load_si128( pOrg++ ) ), shift_cnt ), _mm256_load_si256( pRec++ ) );
      __m256i v16x16_Dif_2  = _mm256_sub_epi16          ( _mm256_sll_epi16( _mm256_cvtepu8_epi16( _mm_load_si128( pOrg++ ) ), shift_cnt ), _mm256_load_si256( pRec++ ) );
      __m256i v8x32_Dx8_1   = _mm256_madd_epi16         ( v16x16_Dif_1,   v16x16_Dif_1  );
      __m256i v8x32_Dx8_2   = _mm256_madd_epi16         ( v16x16_Dif_2,   v16x16_Dif_2  );
      __m256i v8x32_Dx8_a   = _mm256_hadd_epi32         ( v8x32_Dx8_1,    v8x32_Dx8_2   );
      __m256i v8x32_Dx8_b   = _mm256_permute2x128_si256 ( v8x32_Dx8_a,    v8x32_Dx8_a,  1 );
      __m256i v8x32_Dx4     = _mm256_hadd_epi32         ( v8x32_Dx8_a,    v8x32_Dx8_b   );
      __m256i v8x32_Dx2     = _mm256_hadd_epi32         ( v8x32_Dx4,      v8x32_Dx4     );
      __m256i v8x32_Dx1     = _mm256_hadd_epi32         ( v8x32_Dx2,      v8x32_Dx2     );
      dist                 += _mm_extract_epi32         ( _mm256_extracti128_si256( v8x32_Dx1, 0 ), 0 );
    }
  }
  else
  {
    for( unsigned v = 0; v < numV; v++ )
    {
      __m256i v16x16_Dif_1  = _mm256_sub_epi16          ( _mm256_cvtepu8_epi16( _mm_load_si128( pOrg++ ) ), _mm256_load_si256( pRec++ ) );
      __m256i v16x16_Dif_2  = _mm256_sub_epi16          ( _mm256_cvtepu8_epi16( _mm_load_si128( pOrg++ ) ), _mm256_load_si256( pRec++ ) );
      __m256i v8x32_Dx8_1   = _mm256_madd_epi16         ( v16x16_Dif_1,   v16x16_Dif_1  );
      __m256i v8x32_Dx8_2   = _mm256_madd_epi16         ( v16x16_Dif_2,   v16x16_Dif_2  );
      __m256i v8x32_Dx8_a   = _mm256_hadd_epi32         ( v8x32_Dx8_1,    v8x32_Dx8_2   );
      __m256i v8x32_Dx8_b   = _mm256_permute2x128_si256 ( v8x32_Dx8_a,    v8x32_Dx8_a,  1 );
      __m256i v8x32_Dx4     = _mm256_hadd_epi32         ( v8x32_Dx8_a,    v8x32_Dx8_b   );
      __m256i v8x32_Dx2     = _mm256_hadd_epi32         ( v8x32_Dx4,      v8x32_Dx4     );
      __m256i v8x32_Dx1     = _mm256_hadd_epi32         ( v8x32_Dx2,      v8x32_Dx2     );
      dist                 += _mm_extract_epi32         ( _mm256_extracti128_si256( v8x32_Dx1, 0 ), 0 );
    }
  }
  const uint8_t*  data1 = reinterpret_cast<const uint8_t*>( m_data1 );
  const uint8_t*  data2 = reinterpret_cast<const uint8_t*>( m_data2 );
  for( unsigned k = (numV<<5); k < m_numSamples; k++ )
  {
    int32_t diff = int32_t( data1[k] ) - int32_t( data2[k] );
    dist        += uint64_t( diff * diff );
  }
  return dist;
#endif
}


uint64_t Distortion::getSSD_16bit_16bit_avx2() const
{
#if ENABLE_SIMD < 2
  return getSSD_16bit_16bit_cstd();
#else
  const __m256i*  pOrg  = reinterpret_cast<const __m256i*>( m_data2 );
  const __m256i*  pRec  = reinterpret_cast<const __m256i*>( m_data1 );
  const unsigned  numV  = m_numSamples >> 5;
  uint64_t        dist  = 0;
  if( m_shift2 )
  {
    __m128i   shift_cnt     = _mm_set_epi32( 0, 0, 0, (int)m_shift2 );
    for( unsigned v = 0; v < numV; v++ )
    {
      __m256i v16x16_Dif_1  = _mm256_sub_epi16          ( _mm256_sll_epi16( _mm256_load_si256( pOrg++ ), shift_cnt ), _mm256_load_si256( pRec++ ) );
      __m256i v16x16_Dif_2  = _mm256_sub_epi16          ( _mm256_sll_epi16( _mm256_load_si256( pOrg++ ), shift_cnt ), _mm256_load_si256( pRec++ ) );
      __m256i v8x32_Dx8_1   = _mm256_madd_epi16         ( v16x16_Dif_1,   v16x16_Dif_1  );
      __m256i v8x32_Dx8_2   = _mm256_madd_epi16         ( v16x16_Dif_2,   v16x16_Dif_2  );
      __m256i v8x32_Dx8_a   = _mm256_hadd_epi32         ( v8x32_Dx8_1,    v8x32_Dx8_2   );
      __m256i v8x32_Dx8_b   = _mm256_permute2x128_si256 ( v8x32_Dx8_a,    v8x32_Dx8_a,  1 );
      __m256i v8x32_Dx4     = _mm256_hadd_epi32         ( v8x32_Dx8_a,    v8x32_Dx8_b   );
      __m256i v8x32_Dx2     = _mm256_hadd_epi32         ( v8x32_Dx4,      v8x32_Dx4     );
      __m256i v8x32_Dx1     = _mm256_hadd_epi32         ( v8x32_Dx2,      v8x32_Dx2     );
      dist                 += _mm_extract_epi32         ( _mm256_extracti128_si256( v8x32_Dx1, 0 ), 0 );
    }
  }
  else
  {
    for( unsigned v = 0; v < numV; v++ )
    {
      __m256i v16x16_Dif_1  = _mm256_sub_epi16          ( _mm256_load_si256( pOrg++ ), _mm256_load_si256( pRec++ ) );
      __m256i v16x16_Dif_2  = _mm256_sub_epi16          ( _mm256_load_si256( pOrg++ ), _mm256_load_si256( pRec++ ) );
      __m256i v8x32_Dx8_1   = _mm256_madd_epi16         ( v16x16_Dif_1,   v16x16_Dif_1  );
      __m256i v8x32_Dx8_2   = _mm256_madd_epi16         ( v16x16_Dif_2,   v16x16_Dif_2  );
      __m256i v8x32_Dx8_a   = _mm256_hadd_epi32         ( v8x32_Dx8_1,    v8x32_Dx8_2   );
      __m256i v8x32_Dx8_b   = _mm256_permute2x128_si256 ( v8x32_Dx8_a,    v8x32_Dx8_a,  1 );
      __m256i v8x32_Dx4     = _mm256_hadd_epi32         ( v8x32_Dx8_a,    v8x32_Dx8_b   );
      __m256i v8x32_Dx2     = _mm256_hadd_epi32         ( v8x32_Dx4,      v8x32_Dx4     );
      __m256i v8x32_Dx1     = _mm256_hadd_epi32         ( v8x32_Dx2,      v8x32_Dx2     );
      dist                 += _mm_extract_epi32         ( _mm256_extracti128_si256( v8x32_Dx1, 0 ), 0 );
    }
  }
  const uint8_t*  data1 = reinterpret_cast<const uint8_t*>( m_data1 );
  const uint8_t*  data2 = reinterpret_cast<const uint8_t*>( m_data2 );
  for( unsigned k = (numV<<5); k < m_numSamples; k++ )
  {
    int32_t diff = int32_t( data1[k] ) - int32_t( data2[k] );
    dist        += uint64_t( diff * diff );
  }
  return dist;
#endif
}

