
#pragma once

#include <cassert>
#include <iostream>
#include <string>
#include <vector>


// simple integer array for storing image components
class ColorComp
{
public:
  ColorComp ();
  ColorComp ( int width, int height, int maxVal );
  ColorComp ( const ColorComp& c ) = delete;
  ColorComp ( ColorComp&&      c )   noexcept;
  ~ColorComp();

  ColorComp&  operator= ( const ColorComp& c ) = delete;
  ColorComp&  operator= ( ColorComp&&      c )   noexcept;

  bool        valid     ()                          const   { return  m_maxVal > 0; }
  int64_t     width     ()                          const   { return  m_width; }
  int64_t     height    ()                          const   { return  m_height; }
  int64_t     numSamples()                          const   { return  m_numSamples; }
  int64_t     stride    ()                          const   { return  m_stride; }
  int         maxValue  ()                          const   { return  m_maxVal; }
  const int*  data      ()                          const   { return  m_data; }
  int*        data      ()                                  { return  m_data; }
  const int*  data      ( int64_t _x, int64_t _y )  const   { return  m_data + _y*m_stride + _x; }
  int*        data      ( int64_t _x, int64_t _y )          { return  m_data + _y*m_stride + _x; }
  const int&  operator()( int64_t _x, int64_t _y )  const   { return  m_data [ _y*m_stride + _x ]; }
  int&        operator()( int64_t _x, int64_t _y )          { return  m_data [ _y*m_stride + _x ]; }

  bool        samePars  ( const ColorComp& _c )     const;
  double      getPSNR   ( const ColorComp& _c )     const;

private:
  int64_t   m_width;
  int64_t   m_height;
  int64_t   m_numSamples;
  int64_t   m_stride;
  int       m_maxVal;
  int*      m_data;
};



// simple wrapper for images
class Image
{
public:
  enum class Type { INVALID=0, GRAY, RGB };

public:
  Image ();
  Image ( int width, int heigth, int maxVal, Image::Type type );
  Image ( const std::string&  name );
  Image ( const Image&        im   ) = delete;
  Image ( Image&&             im   )   noexcept;
  ~Image();

  Image&              operator=   ( const Image&  im )  = delete;
  Image&              operator=   ( Image&&       im )    noexcept;

  bool                valid       ()              const { return m_type != Image::Type::INVALID; }
  Image::Type         type        ()              const { return m_type; }
  int64_t             width       ()              const { return m_comp[0].width(); }
  int64_t             height      ()              const { return m_comp[0].height(); }
  int                 maxValue    ()              const { return m_comp[0].maxValue(); }
  int64_t             numSamples  ()              const { return m_comp[0].numSamples(); }
  int64_t             numComp     ()              const { return m_comp.size(); }
  const ColorComp&    operator[]  ( int64_t c )   const { return m_comp[c]; }
  ColorComp&          operator[]  ( int64_t c )         { return m_comp[c]; }

  int                 read        ( const std::string&  name );
  int                 write       ( const std::string&  name )  const;
  std::vector<double> getPSNR     ( const Image&        im   )  const;
  bool                samePars    ( const Image&        im   )  const;

private:
  int                 _readNetPBM ( std::istream&       is   );
  int                 _readPGMDat ( std::istream&       is   );
  int                 _readPPMDat ( std::istream&       is   );
  int                 _writePGM   ( const std::string&  name )  const;
  int                 _writePPM   ( const std::string&  name )  const;

private:
  Image::Type             m_type;
  std::vector<ColorComp>  m_comp;
};


