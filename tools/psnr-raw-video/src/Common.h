
#pragma once


#define ENABLE_SIMD   2   //  [ 0:scalar, 1:sse4.1, 2:avx2 ]


#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <istream>
#include <memory>
#include <sstream>
#include <string>
#include <ctime>

#include <emmintrin.h>
#include <immintrin.h>


enum SIMDMode
{
  SIMD_SCALAR     = 0,
  SIMD_SSE41      = 1,
  SIMD_AVX2       = 2,
  SIMD_NUM_VALUES = 3
};


class Message
{
public:
  Message() : m_str() {}
  Message( const std::string& _s ) : m_str( _s ) {}
  Message( const Message& _m ) : m_str( _m.m_str ) {}
  Message& operator=( const Message& _m ) { m_str = _m.m_str; return *this; }
  template<typename T> Message& operator<<( T t ) { std::ostringstream oss; oss << t; m_str += oss.str(); return *this; }
  const std::string& str() const { return m_str; }
private:
  std::string m_str;
};
__inline std::ostream& operator<<( std::ostream& _o, const Message& _m ) { _o << _m.str(); return _o; }



#define THROW(x)      throw( Message( "\nERROR: In function \"" ) << __FUNCTION__ << "\" in " << __FILE__ << ":" << __LINE__ << ": " << x )
#define ERROR(c,x)    if(c) { \
                        THROW(x); \
                      }

